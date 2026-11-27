"""Freeze additional handwritten user-only messages before evaluating the update."""
import json
import project_runtime
from natural_language_training import REPORT,row,save

specs=[
 ('finance_pass',"I'm in Year 2 of Computing Mathematics at CityUHK. My grades are CS1302: B, MA1300: B+, GE2260: A-. Would my study help me with EF3320?",'CM',2,[('CS1302','B'),('MA1300','B+'),('GE2260','A-')],'EF3320','preparation',None,None),
 ('finance_fail',"I'm in Year 2 of Computing Mathematics at CityUHK. My grades are CS1302: B, MA1300: B+, GE2260: F. Would my study help me with EF3320?",'CM',2,[('CS1302','B'),('MA1300','B+'),('GE2260','F')],'EF3320','preparation',None,None),
 ('p_is_pass',"I study Computing Mathematics in Year 3. My results are MA2503 (B+), MA2510 (P), MA3515 (A-) and GE2340 (B). Can you assess my preparation for CS4487?",'CM',3,[('MA2503','B+'),('MA2510','P'),('MA3515','A-'),('GE2340','B')],'CS4487','preparation',None,None),
 ('cs_plan_context_missing',"I am a Year 2 Computer Science student at CityUHK. CS1302A: A, CS2310: B+, GE2340: B. I want the Artificial Intelligence stream. What should I study next semester?",'CS',2,[('CS1302A','A'),('CS2310','B+'),('GE2340','B')],None,'plan','Artificial Intelligence',None),
 ('explicit_weights',"My programme is CM, year 2, entry cohort 2025, semester A. I passed CS1302 with B and GE2260 with A-. I want the Financial Mathematics stream. Use background mismatch weight 2, difficulty weight 0.5, and workload weight 1. What should I consider next semester?",'CM',2,[('CS1302','B'),('GE2260','A-')],None,'plan','Financial Mathematics',{'semester':'A','cohort':2025,'weights':{'background_mismatch':2.,'difficulty':.5,'workload':1.}}),
 ('unknown_grade',"I am a Year 2 CM student. MA2508: grade unknown. How does my background prepare me for MA3515?",'CM',2,[('MA2508','UNKNOWN')],'MA3515','preparation',None,None),
]
rows=[]
for ident,text,programme,year,history,target,request,stream,extra in specs:
    p={'programme':programme,'year':year,'semester':None,'cohort':None,
       'transcript':[{'course_code':c,'grade':g} for c,g in history],
       'target':target,'request':request,'desired_stream':stream}
    p.update(extra or {})
    rows.append(row('manual:'+ident,p,text))
save(REPORT/'fresh_manual_cases.json',rows)
(REPORT/'fresh_manual_inputs.txt').write_text('\n\n'.join(r['id']+'\n'+r['messages'][0]['content'] for r in rows),encoding='utf-8')
print('Frozen six handwritten tests; excluded from training and validation.')
