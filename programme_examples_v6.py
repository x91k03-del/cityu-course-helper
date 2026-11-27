"""Source-derived semester examples, explicit hypothetical bundle assumptions."""
import json
from pathlib import Path
from programme_v6 import plan,lookup
from programme_policy import *
def main():
    out=ROOT/'reports/programme-v6';cases=[]
    for major,code,stream,done in [
      ('CS','BSCCCU4','Data Science',['CS1302A','CS2115','CS2310','CS2312','CS2402','MA1503','MA1508','MA2185']),
      ('CM','BSCSIU4','Enriched Mathematics',['MA1300','MA1301','MA2503','MA2508','MA2509','CS1302','CS2360'])]:
        for term in ['202609','202702']:
            profile={'programme':major,'programme_code':code,'cohort':2025,'term':term,'year':2,'completed_courses':done,'selected_stream':stream}
            result=plan(profile,True)
            cases.append({'profile':profile,'result':result})
    (out/'semester_examples.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
    for c in cases:print(c['profile']['programme'],c['profile']['term'],c['result']['status'],c['result'].get('course_codes'),flush=True)
    # Document and exact snapshot checks are mandatory even when a model suggests otherwise.
    from four_year_markov import simulate
    full=simulate('CM_V6_DOCUMENT_FILTER_AND_STREAM')
    assert full['status']=='complete',full.get('failure')
    assert all(allowed('CM',r['id']) for r in full['transcript'])
    assert stream_result('CM',full['audit']['passed_ids'],full['steps'][0]['state_before']['selected_stream'])['stream_complete']
    (out/'CM_four_year_mock.json').write_text(json.dumps(full,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CM full mock',full['audit']['earned_credits'],'stream complete',flush=True)
if __name__=='__main__':main()
