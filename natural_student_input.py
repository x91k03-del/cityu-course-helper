"""Read an ordinary student message; Qwen receives exactly one user turn."""
import argparse,contextlib,json,sys,time
from pathlib import Path
import project_runtime
from natural_language_training import validate_profile
from programme_policy import exact

ROOT=Path(__file__).resolve().parent

def source_titles(codes):
    result={}
    for row in json.loads((ROOT/'data/programme-v6/courses.json').read_text(encoding='utf-8')):
        if row['course_code'] in codes:result[row['course_code']]=row['title']
    for line in (ROOT/'data/courses.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line)
        if row['code'] in codes:result[row['code']]=row['title']
    return result

def render(value,titles):
    def shown(item):return 'not provided' if item is None else str(item)
    lines=['Student input interpreted by Qwen',
      'Programme: '+shown(value['programme']), 'Study year: '+shown(value['year']),
      'Semester: '+shown(value['semester']), 'Entry cohort: '+shown(value['cohort']),
      'Completed courses: '+(', '.join(value['completed_courses']) or 'none recorded'),
      'Desired stream: '+shown(value['desired_stream'])]
    for row in value['transcript']:
        code=row['course_code']
        lines.append(code+': '+row['grade']+(' -- '+titles[code] if code in titles else ''))
    if value['target']:
        lines += ['Preparation target: '+value['target']+(' -- '+titles[value['target']] if value['target'] in titles else ''),
          'Configured preparation reward: '+str(value['preparation_bonus']),
          'Strongest passed sources: '+(', '.join(value['strongest_sources']) or 'none')]
    lines += ['Penalty weights: '+json.dumps(value['weights'])]
    if value['missing_fields']:
        labels={'programme':'degree programme','year':'study year','semester':'semester','cohort':'entry cohort'}
        lines += ['Please provide: '+', '.join(labels.get(k,k.replace('grade:','grade for ')) for k in value['missing_fields'])]
    elif value['request']=='plan':lines += ['Saved your profile for the course planner.']
    lines += ['Course titles above are read from saved source data. Preparation rewards are advisory; they do not establish registration eligibility.']
    return '\n'.join(lines)+'\n'

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap=argparse.ArgumentParser(description='Give a student transcript in ordinary English, without a system prompt.')
    group=ap.add_mutually_exclusive_group(required=True);group.add_argument('--text');group.add_argument('--input-file');group.add_argument('--interactive',action='store_true')
    ap.add_argument('--output-dir',default='reports/natural-language-students-corrected/latest-input')
    args=ap.parse_args()
    if (ROOT/'data/active_objective_parameter_adapter.json').exists():
        # The current production route exports objective parameters only.
        # Keep the previous command usable without loading its profile-output model.
        from transcript_objective_input import main as objective_main
        source=args.text if args.text is not None else args.input_file
        sys.argv=[sys.argv[0]]+(['--interactive'] if args.interactive else ['--source',source])+['--output-dir',args.output_dir]
        return objective_main()
    text=input('Enter your student message or transcript: ') if args.interactive else args.text if args.text is not None else Path(args.input_file).read_text(encoding='utf-8-sig')
    if not text.strip():raise ValueError('Student message is empty')
    manifest_path=ROOT/'data/active_natural_language_adapter.json'
    if not manifest_path.exists():raise RuntimeError('No validated natural-language adapter is active')
    manifest=json.loads(manifest_path.read_text())
    if not manifest['accepted_for_activation']:raise RuntimeError('Natural-language adapter is not accepted')
    out=ROOT/args.output_dir;out.mkdir(parents=True,exist_ok=True)
    (out/'input.txt').write_text(text,encoding='utf-8')
    print('Reading your student message...',flush=True)
    messages=[{'role':'user','content':text}]
    with (out/'runtime.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        import torch
        from inference import load,generate
        torch.set_num_threads(8);tok,model=load(manifest['adapter'])
        raw=generate(tok,model,messages,max_tokens=600)
    (out/'raw_output.txt').write_text(raw,encoding='utf-8')
    try:
        model_value=json.loads(raw)
        value=validate_profile(model_value,text)
    except (ValueError,TypeError,KeyError) as e:
        (out/'validation.json').write_text(json.dumps({'accepted':False,'error':str(e),'fallback_used':False},indent=2))
        raise RuntimeError('Model output needs review; raw response saved: '+str(e)) from e
    codes={r['course_code'] for r in value['transcript']}|({value['target']} if value['target'] else set())
    titles=source_titles(codes);response=render(value,titles)
    (out/'profile_and_rewards.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    (out/'response.txt').write_text(response,encoding='utf-8')
    (out/'validation.json').write_text(json.dumps({'accepted':True,'accepted_component':'student profile',
      'fallback_used':False,'adapter':manifest['adapter'],'raw_complete_answer_matches_policy':exact(model_value,value),
      'model_reward_proposal':{k:model_value[k] for k in ['preparation_bonus','strongest_sources','missing_fields']},
      'used_model_reward_proposal':False,'contextual_reward_source':'external reviewed course-relation calculator'},indent=2))
    # Pass an ordinary, validated profile to the existing tools, preserving unknown context.
    planner={k:value[k] for k in ['programme','year','cohort','completed_courses','desired_stream','weights']}
    planner['transcript']=value['transcript'];planner['semester']=value['semester']
    planner['natural_language_source']=str(out/'input.txt')
    (out/'planner_profile.json').write_text(json.dumps(planner,indent=2),encoding='utf-8')
    print(response,flush=True)

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(1)
