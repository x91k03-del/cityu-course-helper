"""Default interface: deterministic source facts, Qwen parameters, external DP."""
import argparse,contextlib,copy,hashlib,json,re,sys
from pathlib import Path
import project_runtime
import transcript_parameter_pipeline as p
from natural_language_training import explicit_grades
from preparation import PASS
from programme_policy import policy

def natural_facts(text):
    """Small external reader for explicit English course/grade statements."""
    grades=explicit_grades(text)
    for code in re.findall(r'\b[A-Z]{2,6}\d{4}[A-Z]?\b',text.upper()):
        if code not in grades and re.search(r'\bPASSED\s+'+code+r'\b',text,re.I):grades[code]='P'
    if not grades:raise ValueError('Include course codes with grades, or use a text-based transcript PDF.')
    major='CM' if re.search(r'\bCM\b|Computing Math',text,re.I) else 'CS' if re.search(r'\bCS\b|Computer Science',text,re.I) else None
    return {'programme':major,'rows':[{'course_code':c,'grade':g} for c,g in sorted(grades.items())],
            'completed_courses':sorted(c for c,g in grades.items() if g in PASS),
            'in_progress_courses':sorted(c for c,g in grades.items() if g=='IP'),
            'confirmed_earned_degree_credits':None,'unresolved_degree_credit_rows':[]}

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap=argparse.ArgumentParser();ap.add_argument('--source');ap.add_argument('--fixture',choices=['F','N','M'])
    ap.add_argument('--context',help='Optional JSON with desired_stream, weights and stream_reward_multiplier')
    ap.add_argument('--output-dir',default='reports/transcript-parameter-pipeline/latest-run')
    ap.add_argument('--interactive',action='store_true');args=ap.parse_args()
    source=args.fixture or args.source
    if args.interactive or source is None:source=input('Enter F, N or M for a fictional transcript; a PDF/TXT path; or your student message: ').strip().strip('"')
    cases=json.loads((p.OUT/'cases.json').read_text(encoding='utf-8'));case=next((copy.deepcopy(c) for c in cases if c['id']==source.upper()),None)
    context=json.loads(Path(args.context).read_text(encoding='utf-8')) if args.context else {}
    if case:
        text=p.extract_pdf(Path(case['pdf']));facts=p.parse_transcript(text);preferences=case['preferences']
    else:
        path=Path(source)
        is_file=False
        try:is_file=len(source)<240 and path.is_file()
        except OSError:pass
        if is_file:text=p.extract_pdf(path) if path.suffix.lower()=='.pdf' else path.read_text(encoding='utf-8-sig')
        else:text=source
        document_mode='INSTITUTION CREDIT' in text
        facts=p.parse_transcript(text) if document_mode else natural_facts(text)
        stream=context.get('desired_stream')
        if not stream and facts['programme']:
            stream=next((s for s in policy()['streams'][facts['programme']] if s.lower() in text.lower()),None)
        if not stream and not document_mode and re.search(r'(?:want|prefer|interested in).{0,25}\bfinance\b',text,re.I) and facts['programme']=='CM':stream='Financial Mathematics'
        weights={'background_mismatch':1.,'difficulty':1.,'workload':1.};multiplier=3.
        if not document_mode:
            for key,label,letter in [('background_mismatch','background mismatch','b'),('difficulty','difficulty','d'),('workload','workload','w')]:
                match=re.search(r'(?:'+label+r'\s+(?:penalty\s+)?weight|lambda_'+letter+r')\s*[=:]?\s*(\d+(?:\.\d+)?)',text,re.I)
                if match:weights[key]=float(match.group(1))
            match=re.search(r'stream (?:reward )?multiplier\s*[=:]?\s*(\d+(?:\.\d+)?)',text,re.I)
            if match:multiplier=float(match.group(1))
        preferences={'desired_stream':stream,'weights':context.get('weights',weights),
                     'stream_reward_multiplier':context.get('stream_reward_multiplier',multiplier),
                     'include_fixture_planning_context':False}
        # Automatic full-path matching is restricted to the published fictional controls.
        for c in cases:
            expected=c['facts']
            exact_fixture=is_file and path.suffix.lower()=='.pdf' and hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256((p.ROOT/Path(c['pdf'])).read_bytes()).digest()
            if exact_fixture and facts==expected and (stream is None or stream==c['preferences']['desired_stream']):
                case=copy.deepcopy(c)
                preferences['desired_stream']=stream or c['preferences']['desired_stream']
                preferences['include_fixture_planning_context']=True
                break
    preferences.update({k:context[k] for k in ['desired_stream','weights','stream_reward_multiplier'] if k in context})
    expected=p.parameter_target(preferences['weights'],preferences['stream_reward_multiplier']);p.validate_parameters(expected,expected)
    manifest_path=p.ROOT/'data/active_objective_parameter_adapter.json'
    if not manifest_path.exists():raise RuntimeError('The parameter-only checkpoint has not passed its release checks yet.')
    manifest=json.loads(manifest_path.read_text())
    if not manifest.get('accepted_for_activation') or manifest.get('role')!='objective_parameters_only':raise RuntimeError('No validated parameter-only checkpoint is enabled.')
    out=p.ROOT/args.output_dir;out.mkdir(parents=True,exist_ok=True)
    (out/'input.txt').write_text(text,encoding='utf-8');p.save(out/'parsed_transcript.json',facts)
    messages=p.model_messages(text,preferences)
    p.save(out/'model_messages.json',messages)
    (out/'model_input.txt').write_text(messages[-1]['content'],encoding='utf-8')
    print('Reading the transcript and generating objective parameters...',flush=True)
    with (out/'runtime.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        import torch
        from inference import load,generate
        torch.set_num_threads(8);tok,model=load(manifest['adapter'])
        raw=generate(tok,model,messages,max_tokens=1900)
    (out/'raw_model_output.txt').write_text(raw,encoding='utf-8')
    try:parameters=p.validate_parameters(json.loads(raw),expected)
    except (ValueError,TypeError) as exc:
        p.save(out/'validation.json',{'accepted':False,'error':str(exc),'optimizer_called':False,'fallback_used':False})
        raise RuntimeError('Qwen did not return a valid parameter-only response. The optimiser was not called.') from exc
    p.save(out/'model_parameters.json',parameters)
    print('Qwen output accepted: objective parameters only.',flush=True)
    if case:
        case.update(text=text,preferences=preferences,expected_parameters=expected)
        with (out/'optimizer.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log):result=p.optimise_case(case,parameters)
        p.save(out/'optimizer_plan.json',result)
        if not result.get('curriculum_credit_plan_complete'):raise RuntimeError('The optimiser did not certify a complete path in this fixed context. Diagnostic output was saved.')
        p.save(out/'validation.json',{'accepted':True,'LLM_output_role':'objective_parameters_only','LLM_generated_schedule':False,
          'optimizer_called':True,'method':result['method'],'all_encoded_requirements_met':result['audit']['all_encoded_requirements_met'],
          'certificate':result['completion_optimality_certificate'],'fallback_used':False})
        lines=['External optimiser result',f"Total projected credits: {result['audit']['earned_credits']:g}",
          f"Discounted reward: {result['discounted_academic_reward']:.6f}"]
        for s in result['semesters']:lines.append(f"Year {s['year']} Semester {s['semester']}: "+', '.join(s['selected_courses'])+f" ({s['credits']:g} credits)")
        lines += ['Exact maximum within the supplied fixed completion context; independently checked.',
          'Pending class details remain pending. This is a curriculum simulation, not confirmed registration.']
    else:
        p.save(out/'validation.json',{'accepted':True,'LLM_output_role':'objective_parameters_only','LLM_generated_schedule':False,
          'optimizer_called':False,'reason':'No supported fixed full-degree context was supplied; no schedule is invented.','fallback_used':False})
        lines=['Objective parameters and extracted student facts saved.',
          'A supported full-degree planning context is needed before a maximum-reward path can be certified.',
          'Use F, N or M to run the complete fictional transcript-to-optimiser demonstrations.']
    (out/'response.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines),flush=True)

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)
