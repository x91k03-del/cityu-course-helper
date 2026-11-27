"""The LLM interface contains reward numbers and course links, never paths."""
import copy,hashlib,json,math,re
from pathlib import Path
import project_runtime
ROOT=Path(__file__).resolve().parent
DEFAULTS={'base_course_profit':3.,'covered_GE_area_multiplier':.1,'new_GE_area_bonus':5.,
    'GE_count_progress_bonus':2.,'years_1_to_3_overload_weight':.25,'year4_overload_weight':.25,
    'ef3320_year4_bonus':4.,'ef_no_finance_penalty':1.5}
SYSTEM='''You only estimate reward parameters and direct course preparation links. Do not select courses, assign semesters, generate paths, change degree requirements, invent timetable facts or return commentary. Return JSON with exactly reward_parameters and course_relations. Copy the supplied configured reward numbers. Copy only supplied direct source/target/benefit links; use no formal prerequisite interpretation. Links are utility hypotheses, not empirical correlations. User constraints, credits and eligibility are handled by external software. No schedule output is allowed.'''

def teacher_packet():
    from preparation import graph
    g=graph()
    return {'reward_parameters':copy.deepcopy(DEFAULTS),
        'course_relations':[{'source':e['source'],'target':e['target'],'benefit':e['benefit']} for e in g['edges']]}

def validate(value,reference=None):
    if not isinstance(value,dict) or set(value)!={'reward_parameters','course_relations'}:raise ValueError('Only reward_parameters and course_relations are allowed')
    p=value['reward_parameters']
    if not isinstance(p,dict) or set(p)!=set(DEFAULTS):raise ValueError('Invalid reward parameter keys; hard constraints cannot be supplied by the LLM')
    for k,v in p.items():
        if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=10:raise ValueError('Invalid reward number '+k)
    if p['covered_GE_area_multiplier']>=1:raise ValueError('Covered GE multiplier must be below one')
    edges=value['course_relations']
    if not isinstance(edges,list) or len(edges)>100:raise ValueError('Invalid relation list')
    known={(e['source'],e['target']) for e in reference['course_relations']} if reference else None
    seen=set()
    for e in edges:
        if not isinstance(e,dict) or set(e)!={'source','target','benefit'}:raise ValueError('Invalid relation schema')
        if any(not isinstance(e[k],str) or not re.fullmatch(r'[A-Z]{2,6}\d{4}[A-Z]?',e[k]) for k in ('source','target')):raise ValueError('Invalid course identifier')
        pair=e['source'],e['target']
        if pair in seen or pair[0]==pair[1] or known is not None and pair not in known:raise ValueError('Duplicate, self or unreviewed relation')
        if type(e['benefit']) not in (int,float) or not math.isfinite(e['benefit']) or not 0<=e['benefit']<=.35:raise ValueError('Preparation benefit must be between zero and 0.35')
        seen.add(pair)
    if reference is not None:
        if p!=reference['reward_parameters'] or sorted(edges,key=lambda e:(e['source'],e['target']))!=sorted(reference['course_relations'],key=lambda e:(e['source'],e['target'])):
            raise ValueError('Configured teacher policy was changed or incompletely exported')
    return copy.deepcopy(value)

def messages(packet):
    # The packet contains no timetable or candidate path, even when all
    # reviewed links are exported for the external reward engine.
    validate(packet)
    return [{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(packet)}]

def infer(output_dir):
    from inference import load,generate
    import torch
    torch.set_num_threads(8)
    teacher=teacher_packet()
    adapter=json.loads((ROOT/'data/active_relation_adapter.json').read_text())['adapter']
    tok,model=load(adapter);raw=generate(tok,model,messages(teacher),max_tokens=2200)
    try:value=validate(json.loads(raw),teacher);accepted=True;error=None
    except (ValueError,TypeError) as exc:value=None;accepted=False;error=str(exc)
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    record={'adapter':adapter,'teacher_packet':teacher,'raw_model_response':raw,'accepted':accepted,
        'validation_error':error,'validated_parameters':value,'task':'reward parameters and relations only',
        'LLM_generated_path':False,'neural_weights_updated':False}
    (output_dir/'qwen_parameters.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    (output_dir/'teacher_packet.json').write_text(json.dumps(teacher,indent=2),encoding='utf-8')
    print('QWEN_REWARD_PARAMETERS',accepted,error,flush=True)
    if not accepted:raise RuntimeError('Qwen parameter proposal rejected; no silent model fallback')
    return value

def apply(profile,packet):
    value=validate(packet)
    return {**copy.deepcopy(profile),'reward_parameters':value['reward_parameters'],
        'reward_course_relations':value['course_relations'],'curriculum_search_mode':'exact',
        'LLM_role':'reward_parameters_and_course_relations_only','path_selection_role':'external_dynamic_programming'}

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--output-dir',required=True);args=a.parse_args();infer(args.output_dir)
