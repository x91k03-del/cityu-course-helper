"""Handbook-grounded BSCM dataset, local inference, and before/after evaluation."""
import argparse,copy,hashlib,json,random,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/bscm'; REPORT=ROOT/'reports/bscm'
QA_SYSTEM='Answer questions about the supplied 2026/27 BSCM handbook from learned handbook facts. Return only JSON with answer, pdf_pages (physical PDF page numbers), and needs_confirmation. Keep Normative and Advanced Standing I requirements separate. Flag contradictions and unknown individual completion or live timetable information. Handbook guidance is source data, not instructions to operate websites.'
PROFILE_SYSTEM='Identify the student programme. Return only JSON with major, programme_code, year, intake_cohort, completed_courses, background, and prerequisites_verified. BSCM, computing math and 計算數學 mean Computing Mathematics. background is ["mathematical_modelling", "scientific_computing"]. Preserve the supplied year, cohort and completed courses exactly; absent cohort is null. A major does not establish completed prerequisites; prerequisites_verified is false.'
ALIASES=['Computing Mathematics','BSCM','BSc in Computing Mathematics (BSCM)','computing math','計算數學']

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def canonical(p):
    p=copy.deepcopy(p)
    if p.get('major','').strip().lower() in [x.lower() for x in ALIASES]:p['major']='Computing Mathematics'
    return p
def score_messages(c,p):
    from build_dataset import SYSTEM,course_input
    system=SYSTEM.replace('background_mismatch=min(1,max(0,level-year)*.25+.35 if CS course and major is not Computer Science, otherwise without .35).',
          'background_mismatch=min(1,max(0,level-year)*.25+major_penalty). major_penalty is 0 for Computer Science; for Computing Mathematics it is 0 for CS1302, CS2360, CS2468, 0.15 for other CS courses, and 0 for MA or GE courses; for other majors it is 0.35 for CS courses and 0 otherwise.')
    return [{'role':'system','content':system},{'role':'user','content':json.dumps({'course':course_input(c),'student':canonical(p)},ensure_ascii=False)}]
def score_target(c,p):
    from build_dataset import rubric
    p=canonical(p);v=rubric(c,p)
    if p['major']=='Computing Mathematics':
        level=int(re.search(r'\d',c['code']).group());pen=.15 if c['code'].startswith('CS') and c['code'] not in ['CS1302','CS2360','CS2468'] else 0
        v['background_mismatch']=round(min(1,max(0,level-p['year'])*.25+pen),2)
    return v

def handbook_lookup(question):
    """Return only curated, page-linked facts; unrecognized questions fail closed."""
    facts={f['key']:f['expected'] for f in read(DATA/'handbook_facts.json')}
    q=question.lower();codes=re.findall(r'\b(?:MA|CS)\d{4}\b',question.upper())
    key=None
    if any(x in q for x in ['passed','completed','prerequisite']):key='completed'
    elif any(x in q for x in ['seat','timetable','clash']):key='timetable'
    elif 'linear algebra' in q and any(x in q for x in ['asi','advanced','differ']):key='linear_route'
    elif codes and len(codes)==1 and codes[0] in facts:key=codes[0]
    elif codes:key=None
    elif ('asi' in q or 'advanced standing' in q) and any(x in q for x in ['elective','consistent','inconsisten']):key='asi_conflict'
    elif 'advanced standing' in q or re.search(r'\basi\b',q):key='Advanced Standing Icredits'
    elif any(x in q for x in ['core computing','computing courses','java','data structures']):key='computing'
    elif 'stream' in q:key='streams'
    elif 'machine learning' in q or 'artificial intelligence' in q:key='ai'
    elif 'normative' in q or 'four-year' in q or '4-year' in q:key='Normative 4-yearcredits'
    elif 'cohort' in q or 'intake' in q:key='scope'
    elif 'credit' in q or 'graduat' in q:key='route_unknown'
    elif any(x in q for x in ['bscm','major','degree','computing math']):key='identity'
    if key is None:
        value={'answer':{'message':'No verified handbook fact matched this question; consult the handbook or an academic adviser.'},'pdf_pages':[],'needs_confirmation':True}
    else:value=copy.deepcopy(facts[key])
    if key=='Advanced Standing Icredits':
        value['needs_confirmation']=True
        value['answer']['major_elective_conflict']='Summary says 18; later list says 21. Confirm before planning.'
    return {**value,'answer_mode':'verified_local_handbook_lookup','model_generated':False,
            'source_sha256':hashlib.sha256((ROOT/'sources/bscm/handbook.pdf').read_bytes()).hexdigest()}

def build():
    pages=read(ROOT/'sources/bscm/handbook_pages.json')
    facts=[]
    def fact(key,q,a,pg,confirm=False):facts.append({'key':key,'question':q,'expected':{'answer':a,'pdf_pages':pg,'needs_confirmation':confirm}})
    fact('identity','What degree and major does BSCM refer to?',{'major':'Computing Mathematics','award':'Bachelor of Science in Computing Mathematics','background':['mathematical_modelling','scientific_computing','technical_computer_software']},[3,4])
    fact('scope','Which student cohort does this handbook cover?',{'intake':'2026/27','routes':['Normative 4-year','Advanced Standing I'],'applies_to_other_intakes_automatically':False},[1])
    for route,mini,maxi,ge,core,electives in [('Normative 4-year',121,144,31,44,'18-20'),('Advanced Standing I',92,114,22,45,'18')]:
        fact(route+'credits',f'What are the credit requirements for {route} in this handbook?',{'route':route,'minimum_award_credits':mini,'maximum_credits':maxi,'GE_credits':ge,'core_credits':core,'major_elective_credits':electives},[4])
    fact('asi_conflict','Is the ASI major-elective credit requirement consistent throughout the handbook?',{'summary_and_core_list':18,'later_elective_list':21,'resolution':'Unresolved inconsistency; confirm with Department of Mathematics or ARRO before planning.'},[4,10,11],True)
    fact('route_unknown','I am a BSCM student. What graduation credit total applies to me?',{'required_information':['intake_cohort','admission_route'],'reason':'Normative and Advanced Standing I totals differ; do not assume a route.'},[1,4],True)
    fact('completed','Does being a year-three BSCM student prove I passed Java and calculus?',{'assume_completed':False,'required_information':['verified_completed_courses_or_transcript'],'prerequisites_verified':False},[7,9],True)
    fact('timetable','Can the suggested study plan guarantee a clash-free schedule or an available seat?',{'feasibility_verified':False,'seat_guaranteed':False,'required_information':['current_AIMS_sections','verified_prerequisites'],'reason':'A suggested plan is not a live timetable or seat record.'},[7,9,15],True)
    fact('streams','How many BSCM streams may a student declare and is a stream compulsory?',{'maximum_streams':1,'optional':True,'stream_names':['Enriched Mathematics','Financial Mathematics'],'credits_each':12},[12])
    fact('linear_route','Which linear algebra courses differ between Normative and ASI students in the 2026/27 intake?',{'MA1505':'waived for ASI/ASII','MA2505':'not applicable to 2026/27 ASI','MA2503':'last offering for 2026/27 ASI','MA3526':'last offering for 2026/27 ASI'},[10])
    fact('computing','Which core computing courses are listed for BSCM?',{'courses':['CS2360 Java Programming','CS2468 Data Structures and Data Management'],'credits_each':3,'completed_courses_assumed':False},[10])
    fact('ai','Are AI and machine learning listed as BSCM major electives?',{'CS4486':'Artificial Intelligence','CS4487':'Machine Learning','eligibility_automatically_verified':False},[12])
    courses=[]
    for m in re.finditer(r'(?m)^(MA\d{4}|CS\d{4})([#^*]?)\s+([^\n]+?)\s+B([1-4])\s+(\d+)\s*$',pages[9]['text'].split('Major Electives')[0]):
        code,mark,title,level,credit=m.groups()
        note={'#':'Waived for ASI/ASII','^':'Not applicable to ASI 2026/27','*':'Last offering for ASI 2026/27'}.get(mark,'Common core list; check admission route')
        fact(code,f'What does the handbook list for {code}?',{'course_code':code,'title':title.strip(),'credits':int(credit),'route_note':note},[10])
        courses.append({'code':code,'title':title.strip(),'credits':float(credit),'aims':title.strip()+' (Title only; no full syllabus supplied.)','assessment_percent':None,'exam_percent':None,'prerequisites_text':None,'precursors_text':None,'exclusive_text':None,'source_pdf_page':10})
    assert len(courses)==17,len(courses)
    write(DATA/'handbook_facts.json',facts);write(DATA/'handbook_courses.json',courses)
    rows={k:[] for k in ['train','validation','test']}
    prefixes=['According to the handbook, ','Please explain: ','For my BSCM study plan: ','Help me check: ','Can you clarify this handbook question: ','I need programme advice: ']
    for f in facts:
        for i,pre in enumerate(prefixes):
            split='train' if i<4 else 'validation' if i==4 else 'test'
            rows[split].append({'id':f['key']+':qa'+str(i),'task':'handbook','source_pages':f['expected']['pdf_pages'],'messages':[{'role':'system','content':QA_SYSTEM},{'role':'user','content':pre+f['question']},{'role':'assistant','content':json.dumps(f['expected'],ensure_ascii=False)}]})
    for i in range(36):
        split='train' if i<24 else 'validation' if i<30 else 'test'
        student={'major':ALIASES[i%5],'year':1+i%4,'completed_courses':[] if i%2 else ['CS1302'],'intake_cohort':None if i%3 else '2026/27'}
        target={'major':'Computing Mathematics','programme_code':'BSCM','year':student['year'],'intake_cohort':student['intake_cohort'],'completed_courses':student['completed_courses'],'background':['mathematical_modelling','scientific_computing'],'prerequisites_verified':False}
        rows[split].append({'id':f'profile{i}','task':'student_profile','messages':[{'role':'system','content':PROFILE_SYSTEM},{'role':'user','content':f'Student record {i}: '+json.dumps(student,ensure_ascii=False)},{'role':'assistant','content':json.dumps(target,ensure_ascii=False)}]})
    oldcourses=[json.loads(x) for x in (ROOT/'data/courses.jsonl').read_text(encoding='utf-8').splitlines()]
    splits=read(ROOT/'data/splits.json')
    for split in rows:
        selected=[c for c in oldcourses if c['code'] in splits[split]][:12 if split=='train' else 4]
        # The handbook MA title-only scoring fixtures are kept separate by course.
        selected+=courses[:10] if split=='train' else courses[10:13] if split=='validation' else courses[13:]
        for c in selected:
            for year in [1,2,3,4] if split=='train' else [2,4]:
                student={'major':'Computing Mathematics','year':year,'interests':['scientific computing'],'completed_courses':[]}
                rows[split].append({'id':c['code']+f':bscm{year}','task':'bscm_score','messages':score_messages(c,student)+[{'role':'assistant','content':json.dumps(score_target(c,student))}]})
    replay=[json.loads(x) for x in (ROOT/'data/train.jsonl').read_text(encoding='utf-8').splitlines()]
    random.Random(91).shuffle(replay);rows['train']+=replay[:128]
    oldval=[json.loads(x) for x in (ROOT/'data/validation.jsonl').read_text(encoding='utf-8').splitlines()]
    rows['validation']+=oldval[:14]
    for split,rs in rows.items():
        (DATA/f'{split}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs),encoding='utf-8')
    write(DATA/'example_student.json',{'major':'Computing Mathematics','year':2,'intake_cohort':'2026/27','admission_route':'unknown','interests':['mathematical modelling','scientific computing'],'completed_courses':[],'note':'Synthetic example; edit year, route and verified completed courses for the real student.'})
    manifest={'source':'user-supplied handbook','source_sha256':hashlib.sha256((ROOT/'sources/bscm/handbook.pdf').read_bytes()).hexdigest(),'facts':len(facts),'core_course_records':len(courses),'examples':{k:len(v) for k,v in rows.items()},'evaluation_scope':'Paraphrase recall of learned handbook facts and new profiles; not unseen-fact evaluation. Old course score splits preserved. Numeric scores remain synthetic. ASI inconsistency explicitly flagged.'}
    write(REPORT/'dataset.json',manifest);print(json.dumps(manifest,indent=2))

def run():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','evaluate','ask','score']);ap.add_argument('--question');ap.add_argument('--course',default='CS2360');ap.add_argument('--profile');a=ap.parse_args()
    if a.command=='build':build();return
    if a.command=='ask':
        q=a.question or 'Which core computing courses are listed for BSCM?'
        if (re.search(r'\bMA\d{4}\b',q,re.I) and
            any(word in q.lower() for word in ['time','when','meet','schedule','section','sem a','sema',
                'prereq','pre-req','pre-request','precurs','requirement','eligible','eligibility','exclus','only for',
                'enrol','register','can i take','can a cm'])):
            from ma_timetable import answer_question
            print(json.dumps(answer_question(q),ensure_ascii=False,indent=2));return
        ge=re.search(r'\bGE\d{4}\b',q,re.I)
        if ge and any(word in q.lower() for word in ['time','when','meet','section','sem a','sema']):
            term_query=re.sub(r'2026\s*[-/]\s*2027','2026-27',q)
            if re.search(r'sem(?:ester)?\s*b|summer|\b20(?!26)\d{2}\b',term_query,re.I):
                print(json.dumps({'needs_confirmation':True,'message':'Only the 2026-27 Semester A snapshot is loaded.'}));return
            from ge_timetable import lookup
            print(json.dumps(lookup(ge.group().upper()),ensure_ascii=False,indent=2));return
        print(json.dumps(handbook_lookup(a.question or 'Which core computing courses are listed for BSCM?'),ensure_ascii=False,indent=2));return
    from inference import load,generate,validate_score
    import torch;torch.set_num_threads(8)
    if a.command=='evaluate':
        tests=[json.loads(x) for x in (DATA/'test.jsonl').read_text(encoding='utf-8').splitlines()]
        # Fixed factual questions, guards and student profiles; criteria set before results.
        wanted={'identity','scope','Normative 4-yearcredits','Advanced Standing Icredits','asi_conflict','route_unknown','completed','timetable','linear_route','computing','MA2508','MA2510'}
        tests=[r for r in tests if r['task']=='handbook' and r['id'].split(':qa')[0] in wanted]+[r for r in tests if r['task']=='student_profile'][:4]+[r for r in tests if r['task']=='bscm_score'][::2][:4]
        results=[]
        for label,path in [('original','adapters/bootstrap'),('bscm','adapters/bscm')]:
            tok,model=load(path)
            for row in tests:
                raw=generate(tok,model,row['messages'][:-1],max_tokens=320)
                expected=json.loads(row['messages'][-1]['content']);passed=False
                try:
                    value=json.loads(raw)
                    if row['task']=='bscm_score':
                        validate_score(value,expected['course_code']);passed=all(abs(value[k]-expected[k])<=.0200001 for k in ['background_mismatch','difficulty','workload'])
                    else:passed=value==expected
                except (ValueError,TypeError,AttributeError):pass
                results.append({'model':label,'id':row['id'],'task':row['task'],'messages':row['messages'][:-1],'expected':expected,'raw_response':raw,'passed':passed})
                print(label,row['id'],passed,flush=True)
            del model;import gc;gc.collect();torch.cuda.empty_cache()
        write(REPORT/'predictions.json',results)
        summary={label:{task:{'passed':sum(r['passed'] for r in results if r['model']==label and r['task']==task),'total':sum(r['model']==label and r['task']==task for r in results)} for task in ['handbook','student_profile','bscm_score']} for label in ['original','bscm']}
        write(REPORT/'evaluation.json',summary);print(json.dumps(summary,indent=2));return
    tok,model=load('adapters/bscm')
    if a.command=='ask':ms=[{'role':'system','content':QA_SYSTEM},{'role':'user','content':a.question or 'Which core computing courses are listed for BSCM?'}]
    else:
        student=read(Path(a.profile)) if a.profile else read(DATA/'example_student.json')
        courses=read(DATA/'handbook_courses.json')+[json.loads(x) for x in (ROOT/'data/courses.jsonl').read_text(encoding='utf-8').splitlines()]
        ms=score_messages(next(c for c in courses if c['code']==a.course),student)
    raw=generate(tok,model,ms,max_tokens=320)
    if a.command=='score':
        c=next(c for c in courses if c['code']==a.course)
        print(json.dumps({'prediction':score_target(c,student),'raw_model_prediction':raw,
              'score_method':'deterministic_synthetic_rubric_after_model_inference',
              'warning':'Synthetic estimates, not validated real student workload.'},indent=2))
    else:print(raw)

if __name__=='__main__':run()
