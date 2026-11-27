"""Post-training degree attempt, actual timetable diagnostics and EF pairs."""
import copy,hashlib,json
from pathlib import Path
import project_runtime
from timetable_grounded_training import ADAPTER,DATA,REPORT,messages,assessment,problem_for,save
from programme_policy import exact
from grounded_model import provider,selected_run

def main():
    root=Path(__file__).resolve().parent
    global REPORT,ADAPTER
    chosen=selected_run();REPORT=root/chosen['report_dir'];ADAPTER=chosen['adapter']
    call=provider();profile=json.loads((root/'data/markov-repair/year1_CM.json').read_text());profile['programme_code']='BSCSIU4'
    from grounded_degree import simulate
    run=simulate(profile,call);run['model_adapter']=ADAPTER
    run['adapter_sha256']=hashlib.sha256((root/ADAPTER/'adapter_model.safetensors').read_bytes()).hexdigest()
    save(REPORT/'rerun_year1.json',run)
    pairs=[]
    for code,term in [('EF3320','202702'),('EF4821','202609')]:
      for label,done in [('no_finance',[]),('passed_finance_GE',['GE1202']),('failed_finance_GE',['GE1202'])]:
        p={**profile,'year':2,'term':term,'completed_courses':done}
        if label=='failed_finance_GE':p['GE_history']=[{'course_code':'GE1202','grade':'F'}]
        raw,parsed=call(messages(p,code));expected=assessment(p,code);accepted=exact(expected,parsed)
        pairs.append({'profile_label':label,'profile':p,'course_code':code,'raw_model_response':raw,
            'expected':expected,'model_output_accepted':accepted,'policy_fallback_used':not accepted})
        save(REPORT/'EF_penalty_examples.json',pairs);print(code,label,accepted,expected['EF_mismatch_penalty'],flush=True)
    # These source-conditioned raw requests were actually decoded during the
    # after evaluation, not recomputed policy targets presented as model outputs.
    from markov_planner import plan_from_proposal
    rows={r['id']:r for r in json.loads((REPORT/'evaluation_cases.json').read_text())}
    semesters=[]
    for pred in json.loads((REPORT/'after_predictions.json').read_text()):
        if not pred['id'].startswith('diagnostic:corrected:'):continue
        row=rows[pred['id']];problem=row['problem']
        try:parsed=json.loads(pred['raw_model_response'])
        except ValueError:parsed=None
        result=plan_from_proposal(problem,parsed)
        opts={o['option_id']:o for o in problem['options']}
        result['selected_source_options']=[opts[x] for x in result.get('selected_options',[])]
        semesters.append({'id':pred['id'],'input_problem':problem,'raw_model_response':pred['raw_model_response'],
            'raw_request_origin':'post-training frozen evaluation; reused without another model call','result':result})
    save(REPORT/'rerun_semesters.json',semesters)
    print('DEGREE',run['status'],run.get('blocked_at'),flush=True)

if __name__=='__main__':main()
