"""Post-training evidence for EF3320 and the eight-semester terminal-credit rule."""
import json,hashlib
from pathlib import Path
import project_runtime
from degree_chain import simulate
from degree_chain_training import REPORT,SYSTEM,degree_messages,target
from grounded_model import provider,selected_run
from timetable_grounded_training import messages,assessment,record_for,compatible_sections
from programme_policy import exact
ROOT=Path(__file__).resolve().parent
def save(name,v):(REPORT/name).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    call=provider();profile=json.loads((ROOT/'data/markov-repair/year1_CM.json').read_text());profile['programme_code']='BSCSIU4'
    run=simulate(profile,call);run['model_adapter']=selected_run()['adapter'];save('model_rollout.json',run)
    probes=[]
    for credit in [121,122]:
        state={'semester':8,'earned_credits':credit,'other_graduation_requirements_met':True}
        raw,value=call(degree_messages(state));probes.append({'state':state,'raw':raw,'expected':target(state),'accepted':exact(target(state),value)})
    save('credit_boundary_probes.json',probes)
    p={**profile,'term':'202702','year':2,'completed_courses':[]};ms=messages(p,'EF3320');ms[0]={'role':'system','content':SYSTEM}
    raw,value=call(ms);expected=assessment(p,'EF3320');ss=compatible_sections(p,record_for(p,'EF3320'))
    save('EF3320_source_check.json',{'source_pdf':record_for(p,'EF3320')['source_pdf'],'source_sha256':record_for(p,'EF3320')['source_sha256'],
      'compatible_sections':ss,'raw_model_response':raw,'expected':expected,'model_output_accepted':exact(expected,value),
      'original_benchmark_rejection':'The invented EF3320:10000 option was in a Semester-A response; the real record is EF3320:11425 in Semester B.',
      'importer_bug_fixed':'General non-CB sections were incorrectly discarded because no explicit ONLY FOR CM line existed.'})
    print(run['status'],run['audit']['earned_credits'],run['coverage_certificate'],flush=True)
    print([(s['year'],s['semester'],s['course_count'],s['credits']) for s in run['diagnostic_semesters']],flush=True)
if __name__=='__main__':main()
