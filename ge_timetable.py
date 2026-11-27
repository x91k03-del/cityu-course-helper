"""Import public GE section data, train timetable tasks, and query the saved snapshot.

Network fetches fail closed on access challenges. The dated browser capture is
the source for this run; saved HTML can be re-imported without browser cookies.
"""
import argparse,copy,hashlib,json,random,re,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/ge-timetable';REPORT=ROOT/'reports/ge-timetable';SOURCE=ROOT/'sources/ge-timetable'
TERM='2026-27 Sem A'
DAYS={d:i+1 for i,d in enumerate(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])}
SYSTEM=('Return captured CityU GE timetable information as JSON with course_code, term, section, meetings, '
        'calendar_dates, teaching_weeks, and needs_confirmation. meetings contains day, start_time, end_time, building, room. '
        'Use the 2026-27 Semester A snapshot only. Missing days/times are null, not free periods. '
        'Calendar dates and teaching weeks were not published in this source, so both are null and needs_confirmation true. '
        'Capacity is not remaining seats. Preserve multiple room records without inventing date assignments.')

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def codes_from_pdfs():
    from pypdf import PdfReader
    codes=set()
    for p in (ROOT/'GE_SEMA/courseAavaible').glob('*.pdf'):
        text='\n'.join(x.extract_text() or '' for x in PdfReader(p).pages)
        codes.update(re.findall(r'\bGE\d{4}\b',text))
    if not codes:raise ValueError('No course codes in saved availability PDFs')
    return codes

def html_rows(path):
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(path.read_bytes(),'html.parser')
    table=soup.select_one('#id0mobileTableRegion')
    if not table:raise ValueError('No section table; possible access challenge or unavailable page: '+str(path))
    rows=[]
    for tr in table.select('tr'):
        cells=[c.get_text(' ',strip=True) for c in tr.select('td')]
        if len(cells)>=11 and cells[3]==TERM:
            rows.append([cells[1],cells[2],cells[4],cells[5],cells[6],cells[7],cells[8],cells[9]])
    text=soup.get_text(' ',strip=True);m=re.search(r'No\. of Credit Units\s+(\d+)',text)
    return {'title':soup.select_one('h1').get_text(' ',strip=True),'credits':int(m.group(1)) if m else None,'rows':rows}

def normalize():
    allowed=codes_from_pdfs();raw={};current=None
    capture=SOURCE/'semester_a_browser_capture.txt'
    for line in capture.read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        fields=line.split('|')
        if re.fullmatch(r'GE\d{4}',fields[0]):
            current=fields[0];raw[current]={'title':fields[2],'credits':int(fields[1]),'rows':[]}
        else:
            if current is None or len(fields)!=8:raise ValueError('Malformed capture row: '+line)
            raw[current]['rows'].append(fields)
    # Explicit local HTML refreshes override the browser capture for that course only.
    for path in (SOURCE/'html').glob('GE*.html'):
        code=path.stem
        if code in allowed:raw[code]=html_rows(path)
    if set(raw)!=allowed:raise ValueError('Course list mismatch: '+str(set(raw)^allowed))
    empty=[code for code,c in raw.items() if not c['rows']]
    if empty:raise ValueError('Availability list and detail pages disagree: no Semester A sections for '+str(empty))
    sections={};flat=[]
    for code,c in sorted(raw.items()):
        for crn,section,kind,cap,day,clock,building,room in c['rows']:
            assert crn.isdigit() and section.startswith(crn),(code,section)
            m=re.fullmatch(r'(\d{2}:\d{2}):00\s*-\s*(\d{2}:\d{2}):00',clock)
            if day not in DAYS or not m:
                if day or clock not in ['', '-']:raise ValueError('Unrecognised day/time: '+str([code,day,clock]))
                start=end=None;weekday=None
            else:
                start,end=m.groups();weekday=DAYS[day]
                assert minutes(start)<minutes(end)
            meeting={'day':day or None,'start_time':start,'end_time':end,'building':building or None,'room':room or None}
            row={'course_code':code,'title':c['title'],'credits':c['credits'],'crn':crn,'section':section,'term':TERM,
                 'section_type':kind,'capacity':int(cap),'day_number':weekday,**meeting,'calendar_dates':None,'teaching_weeks':None,
                 'source_url':'https://www.cityu.edu.hk/ge_info/Course/'+code,'snapshot_date':'2026-11-15'}
            flat.append(row);key=code+':'+section
            if key not in sections:
                sections[key]={k:row[k] for k in ['course_code','title','credits','crn','section','term','section_type','capacity','source_url','snapshot_date']}
                sections[key].update(meetings=[],calendar_dates=None,teaching_weeks=None,needs_confirmation=True,
                                     component_linking_verified=False,eligibility_verified=False)
            assert sections[key]['section_type']==kind and sections[key]['capacity']==int(cap)
            if meeting not in sections[key]['meetings']:sections[key]['meetings'].append(meeting)
    flat_path=DATA/'meeting_rows.json';write(flat_path,flat);write(DATA/'sections.json',list(sections.values()))
    sample=ROOT/'GE_SEMA/sampleGE/GE1101.html'
    assert not html_rows(sample)['rows'],'Summer-only GE1101 example must not enter Semester A'
    report={'term':TERM,'courses':len(raw),'meeting_rows':len(flat),'sections':len(sections),
            'missing_day_time_rows':sum(r['day'] is None for r in flat),
            'calendar_dates_published':False,'teaching_weeks_published':False,
            'capture_sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),
            'capture_method':'Rendered public course-detail DOM, restricted to exact Semester A term; manually serialized from browser output.',
            'retrieval_date':'2026-11-15','all_availability_codes_covered':True,
            'GE1101_summer_negative_control':'passed','authority_note':'ARRO Master Class Schedule prevails over this GE site.'}
    write(REPORT/'import.json',report);print(json.dumps(report,indent=2));return list(sections.values())

def minutes(clock):
    h,m=map(int,clock.split(':'));return h*60+m
def target(s):return {k:s[k] for k in ['course_code','term','section','meetings','calendar_dates','teaching_weeks','needs_confirmation']}
def question(s,style):
    prefix=['Give the captured timetable for','When does this Semester A section meet:','Check the saved meeting details of'][style]
    return f"{prefix} {s['course_code']} section {s['section']} in {TERM}?"

def build():
    sections=normalize();rng=random.Random(115);rows={n:[] for n in ['train','validation','test']}
    for i,s in enumerate(sections):
        expected=target(s)
        for style in [0,1,2]:
            split='train' if style==0 else 'validation' if style==1 else 'test'
            if split!='train' and i%9:continue
            rows[split].append({'id':s['course_code']+':'+s['section']+':recall'+str(style),'task':'snapshot_recall',
               'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':question(s,style)},
                           {'role':'assistant','content':json.dumps(expected,ensure_ascii=False)}]})
        source={'course_code':s['course_code'],'section':s['section'],'term':s['term'],'meetings':s['meetings']}
        # All snapshot facts are intentionally taught; held-out prompts test new wording, not unseen facts.
        rows['train'].append({'id':s['section']+':extract','task':'grounded_extraction','messages':[
            {'role':'system','content':SYSTEM},{'role':'user','content':'Extract the timetable from this saved record: '+json.dumps(source,ensure_ascii=False)},
            {'role':'assistant','content':json.dumps(expected,ensure_ascii=False)}]})
    replay=[json.loads(x) for x in (ROOT/'data/bscm/train.jsonl').read_text(encoding='utf-8').splitlines()]
    rng.shuffle(replay);rows['train']+=replay[:80]
    for name,rs in rows.items():
        (DATA/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs),encoding='utf-8')
    write(REPORT/'dataset.json',{'examples':{k:len(v) for k,v in rows.items()},'split_design':'All section facts taught. Validation/test use different question wording. No claim of unseen-fact generalization. Includes BSCM replay.'})
    print('DATASET', {k:len(v) for k,v in rows.items()})

def fetch_html():
    import requests
    from urllib.robotparser import RobotFileParser
    session=requests.Session();session.headers['User-Agent']='CityUCourseHelperResearch/0.2'
    r=session.get('https://www.cityu.edu.hk/robots.txt',timeout=30);r.raise_for_status();rp=RobotFileParser();rp.parse(r.text.splitlines())
    dest=SOURCE/'html';dest.mkdir(exist_ok=True)
    for code in sorted(codes_from_pdfs()):
        url='https://www.cityu.edu.hk/ge_info/Course/'+code
        if not rp.can_fetch(session.headers['User-Agent'],url):raise RuntimeError('Robots policy does not allow '+url)
        time.sleep(2);r=session.get(url,timeout=40);r.raise_for_status()
        temporary=dest/(code+'.download');temporary.write_bytes(r.content)
        html_rows(temporary) # A challenge page is never accepted as course data.
        temporary.replace(dest/(code+'.html'));print('SAVED',code,flush=True)

def lookup(code,section=None):
    data=[s for s in read(DATA/'sections.json') if s['course_code']==code and (not section or s['section']==section)]
    return {'course_code':code,'term':TERM,'snapshot_date':'2026-11-15','sections':data,
            'data_mode':'verified_snapshot_lookup','not_found':not bool(data),
            'warning':'Calendar dates, teaching weeks and section combinations need confirmation. Capacity is not available seats; ARRO prevails.'}

def weekly_overlap(a,b):
    known=False;missing=False
    for x in a['meetings']:
        for y in b['meetings']:
            if any(z.get('day') is None or z.get('start_time') is None or z.get('end_time') is None for z in [x,y]):missing=True;continue
            known |= x['day']==y['day'] and minutes(x['start_time'])<minutes(y['end_time']) and minutes(y['start_time'])<minutes(x['end_time'])
    return {'weekly_overlap':True if known else None if missing else False,
            'calendar_conflict_confirmed':None,'needs_confirmation':True}

def evaluate():
    import torch
    from inference import load,generate
    torch.set_num_threads(8)
    sections=read(DATA/'sections.json');selected=[]
    for code in ['GE1105','GE1113','GE1128','GE1202','GE1305','GE1354','GE1356','GE1362','GE1401','GE1501','GE1601','GE2262']:
        selected.append(next(s for s in sections if s['course_code']==code))
    tests=[]
    for s in selected:
        tests.append({'id':s['section']+':recall','task':'recall','messages':[{'role':'system','content':SYSTEM},{'role':'user','content':question(s,2)}],'expected':target(s)})
        evidence={k:s[k] for k in ['course_code','term','section','meetings']}
        tests.append({'id':s['section']+':grounded','task':'grounded','messages':[{'role':'system','content':SYSTEM},{'role':'user','content':'Read this supplied section and return its timetable fields: '+json.dumps(evidence,ensure_ascii=False)}],'expected':target(s)})
    # Independent test phrasing; validation is used only for checkpoint selection.
    results=[]
    for label,path in [('bscm','adapters/bscm'),('timetable','adapters/bscm-timetable')]:
        tok,model=load(path)
        for t in tests:
            raw=generate(tok,model,t['messages'],max_tokens=320);passed=False;time_match=False
            try:
                value=json.loads(raw);passed=value==t['expected']
                actual_meetings=value.get('meetings',[])
                time_match=(all(value.get(k)==t['expected'][k] for k in ['course_code','term','section']) and
                    bool(actual_meetings) and all(all(k in m for k in ['day','start_time','end_time']) for m in actual_meetings) and
                    {(m['day'],m['start_time'],m['end_time']) for m in actual_meetings}==
                    {(m['day'],m['start_time'],m['end_time']) for m in t['expected']['meetings']})
            except (ValueError,TypeError,KeyError,AttributeError):pass
            results.append({**t,'model':label,'raw_response':raw,'passed':passed,'time_fields_match':time_match})
            write(REPORT/'predictions.json',results);print(label,t['id'],passed,flush=True)
        del model;import gc;gc.collect();torch.cuda.empty_cache()
    summary={label:{task:{'passed':sum(r['passed'] for r in results if r['model']==label and r['task']==task),
              'time_fields_match':sum(r['time_fields_match'] for r in results if r['model']==label and r['task']==task),
              'total':sum(r['model']==label and r['task']==task for r in results)} for task in ['recall','grounded']} for label in ['bscm','timetable']}
    write(REPORT/'evaluation.json',summary);print(json.dumps(summary,indent=2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','fetch','import','lookup','overlap','evaluate','predict'])
    ap.add_argument('--course',default='GE1356');ap.add_argument('--section');ap.add_argument('--other-course',default='GE2213')
    ap.add_argument('--memory-only',action='store_true',help='Diagnostic only: omit source context despite unreliable recall.')
    a=ap.parse_args()
    if a.command=='build':build()
    elif a.command=='fetch':fetch_html()
    elif a.command=='import':normalize()
    elif a.command=='lookup':print(json.dumps(lookup(a.course,a.section),ensure_ascii=False,indent=2))
    elif a.command=='overlap':
        x=lookup(a.course,a.section)['sections'];y=lookup(a.other_course)['sections']
        if not x or not y:raise ValueError('Course or section not found')
        print(json.dumps([{'section_a':i['section'],'section_b':j['section'],**weekly_overlap(i,j)} for i in x for j in y],indent=2))
    elif a.command=='evaluate':evaluate()
    else:
        from inference import load,generate
        sections=lookup(a.course,a.section)['sections']
        if not sections:raise ValueError('Unknown section')
        from inference import current_timetable_adapter
        s=sections[0];tok,model=load(current_timetable_adapter())
        prompt=question(s,2) if a.memory_only else 'Read this saved meeting record and return its timetable fields: '+json.dumps({k:s[k] for k in ['course_code','term','section','meetings']})
        raw=generate(tok,model,[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],max_tokens=320)
        print(json.dumps({'model_mode':'memory_only_diagnostic' if a.memory_only else 'source_grounded',
                         'raw_model_response':raw,'verified_snapshot':target(s),'note':'Use verified_snapshot for exact times, not unchecked model memory.'},indent=2))

if __name__=='__main__':main()
