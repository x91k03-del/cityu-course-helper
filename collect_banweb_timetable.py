"""User-login-assisted, read-only CityU Banner timetable collector.

No password automation, cookie exports, persistent browser profiles or registration
actions. Live page layouts may vary; unknown tables are preserved as unparsed
course-table cells and are never silently reported as verified meetings.
"""
import argparse,hashlib,json,re,sys,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import parse_qs,urlencode,urljoin,urlparse
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
HOST='banweb.cityu.edu.hk'
ENDPOINT='https://'+HOST+'/pls/PROD/hwscrssh_cityu.P_DispOneSection'
SUBJECT=re.compile(r'^[A-Z]{2,6}$');COURSE=re.compile(r'^\d{4,5}[A-Z]?$')

def timestamp():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(path)

def course_url(term,subj,crse):
    subj=subj.upper();crse=crse.upper()
    if not re.fullmatch(r'20\d{4}',term) or not SUBJECT.fullmatch(subj) or not COURSE.fullmatch(crse):
        raise ValueError('Invalid term, subject or course number')
    return ENDPOINT+'?'+urlencode({'term':term,'subj':subj,'crse':crse,'camp':'%','web_avail':''})

def course_from_link(href,base,term,subject):
    if not href:return None
    href=href.replace('&amp;','&')
    if href.lower().startswith('javascript:'):
        match=re.search(r"((?:(?:https://banweb\.cityu\.edu\.hk)?/pls/PROD/)?hwscrssh_cityu\.P_DispOneSection\?[^'\"\s)]+)",href,re.I)
        if not match:return None
        href=match.group(1)
    u=urlparse(urljoin(base,href))
    if u.scheme!='https' or u.hostname!=HOST or u.path.lower()!='/pls/prod/hwscrssh_cityu.p_disponesection':return None
    q={k.lower():v[-1] for k,v in parse_qs(u.query,keep_blank_values=True).items()}
    subj=q.get('subj','').upper();crse=q.get('crse','').upper()
    if q.get('term')!=term or not SUBJECT.fullmatch(subj) or not COURSE.fullmatch(crse):return None
    if subject!='ALL' and subj!=subject:return None
    return subj,crse

def course_file(path,subject):
    text=path.read_text(encoding='utf-8-sig');found=set()
    if path.suffix.lower()=='.json':
        obj=json.loads(text)
        if isinstance(obj,dict):obj=obj.get('course_codes',obj.get('courses',[]))
        if not isinstance(obj,list):raise ValueError('JSON course file must contain a list')
        for row in obj:
            if isinstance(row,str):text+='\n'+row
            elif isinstance(row,dict):text+='\n'+str(row.get('course_code',row.get('code','')))
    found.update((m[0],m[1]) for m in re.findall(r'\b([A-Z]{2,6})[\s_-]*(\d{4,5}[A-Z]?)\b',text.upper()))
    if subject!='ALL':found={x for x in found if x[0]==subject}
    if not found:raise ValueError('No matching course codes found in '+str(path))
    return sorted(found)

def key(text):return re.sub(r'[^a-z0-9]','',text.lower())
ALIASES={
 'subject':{'subject','subj','subjectcode'},'course_number':{'course','crse','coursenumber','courseno'},
 'course_code':{'coursecode','subjectcourse'},
 'crn':{'crn','classreferencenumber','classno','classnumber'},
 'section':{'section','sec','sectioncode'},'type':{'type','classtype','activity','scheduletype'},
 'day':{'day','days','weekday','weekdays','meetingdays','classday'},
 'time':{'time','classtime','meetingtime','times'},
 'start_time':{'starttime','begintime','timefrom','fromtime'},'end_time':{'endtime','finishtime','timeto','totime'},
 'building':{'building','bldg','bldgcode'},'room':{'room','roomno','roomnumber'},
 'location':{'location','venue'},
 'start_date':{'startdate','begindate','datefrom','fromdate'},'end_date':{'enddate','finishdate','dateto','todate'},
 'dates':{'date','dates','daterange','meetingdates','classdates'},
 'capacity':{'capacity','cap','classcapacity'},
}

def table_grid(table):
    """Expand row/column spans, retaining line breaks in public course cells."""
    spans={};grid=[]
    for tr in table.find_all('tr'):
        if tr.find_parent('table') is not table:continue
        cells=[c for c in tr.find_all(['td','th'],recursive=False)]
        if not cells:continue
        row={};col=0
        for colnum,(left,val) in list(spans.items()):
            row[colnum]=val
            if left==1:del spans[colnum]
            else:spans[colnum]=(left-1,val)
        for c in cells:
            while col in row:col+=1
            value=c.get_text('\n',strip=True)
            for x in range(int(c.get('colspan',1))):
                row[col+x]=value
                if int(c.get('rowspan',1))>1:spans[col+x]=(int(c['rowspan'])-1,value)
            col+=int(c.get('colspan',1))
        grid.append([row.get(i,'') for i in range(max(row)+1)])
    return grid

def parse_clock(text):
    text=re.sub(r'\s+',' ',text.strip()).upper().replace('.', '')
    if re.fullmatch(r'\d{4}',text):text=text[:2]+':'+text[2:]
    for fmt in ['%H:%M:%S','%H:%M','%I:%M %p','%I:%M%p','%I %p','%I%p']:
        try:return datetime.strptime(text,fmt).strftime('%H:%M')
        except ValueError:pass
    return None

def parse_times(text):
    parts=re.split(r'\s*(?:-|–|—|\bto\b)\s*',text.strip(),maxsplit=1,flags=re.I)
    if len(parts)!=2:return None,None
    a,b=parts
    # Never infer AM/PM for an ambiguous partial 12-hour interval.
    if re.search(r'[AP]M',b,re.I) and not re.search(r'[AP]M',a,re.I):return None,None
    start,end=parse_clock(a),parse_clock(b)
    return (start,end) if start and end and start<end else (None,None)

def parse_days(text):
    if not text.strip() or re.search(r'tba|arrang|to be|not available',text,re.I):return None
    names=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    words=re.findall(r'Mon(?:day)?|Tue(?:sday|s)?|Wed(?:nesday)?|Thu(?:rsday|rs)?|Fri(?:day)?|Sat(?:urday)?|Sun(?:day)?',text,re.I)
    if words:return list(dict.fromkeys(x[:3].title() for x in words))
    compact=re.sub(r'[\s,/&]+','',text).upper()
    if compact=='TH':return ['Thu']
    mapping=dict(zip('MTWRFSU',names))
    return list(dict.fromkeys(mapping[x] for x in compact)) if compact and all(x in mapping for x in compact) else None

def parse_date(text):
    text=text.strip()
    for fmt in ['%Y-%m-%d','%d-%b-%Y','%d-%b-%y','%d %b %Y']:
        try:return datetime.strptime(text,fmt).date().isoformat()
        except ValueError:pass
    # Slash-only dates can be ambiguous; retain raw value rather than choose a locale.
    return None

def parse_html(html,subj,crse,term):
    soup=BeautifulSoup(html,'html.parser');rows=[];unparsed=[];matched_tables=0
    for tindex,table in enumerate(soup.find_all('table')):
        grid=table_grid(table);mapping=None;start=0
        for i,row in enumerate(grid[:15]):
            candidate={field:j for j,x in enumerate(row) for field,aliases in ALIASES.items() if key(x) in aliases}
            if 'day' in candidate and ('time' in candidate or {'start_time','end_time'}<=set(candidate)):
                mapping=candidate;start=i+1;matched_tables+=1;break
        if mapping is None:continue
        previous={}
        for cells in grid[start:]:
            if not any(x.strip() for x in cells):continue
            def get(k):return cells[mapping[k]].strip() if k in mapping and mapping[k]<len(cells) else ''
            if key(get('day')) in ALIASES['day']:continue
            listed_subj=get('subject').upper()
            listed_crse=re.match(r'\d{4,5}[A-Z]?',get('course_number').upper())
            listed_code=re.match(r'([A-Z]{2,6})\s*(\d{4,5}[A-Z]?)',get('course_code').upper())
            if listed_subj and listed_subj!=subj:continue
            if listed_crse and listed_crse.group()!=crse:continue
            if listed_code and (listed_code[1],listed_code[2])!=(subj,crse):continue
            crn=get('crn') or previous.get('crn');section=get('section') or previous.get('section')
            if get('crn') and get('crn')!=previous.get('crn') and not get('section'):section=None
            if crn:previous['crn']=crn
            if section:previous['section']=section
            day_text=get('day');time_text=get('time')
            if not day_text and not time_text and not get('start_time') and not get('end_time'):
                # A TBA row with a CRN is still an unknown meeting, not an empty/free class.
                if not get('crn') and not get('section'):continue
            if 'time' in mapping:a,b=parse_times(time_text)
            else:a,b=parse_clock(get('start_time')),parse_clock(get('end_time'))
            warnings=[]
            if not crn:warnings.append('CRN not identified')
            if not section:warnings.append('Section code not identified')
            day_list=parse_days(day_text)
            if day_list is None:warnings.append('Meeting days unknown')
            if not a or not b:warnings.append('Meeting times unknown or ambiguous')
            if a and b and a>=b:a=b=None;warnings.append('Invalid time interval')
            date_start=get('start_date');date_end=get('end_date');date_range=get('dates')
            if date_range and not date_start and not date_end:
                tokens=re.findall(r'\d{1,2}-[A-Za-z]{3}-\d{2,4}|\d{4}-\d{2}-\d{2}',date_range)
                if len(tokens)==2:date_start,date_end=tokens
            begin,end=parse_date(date_start),parse_date(date_end)
            if begin and end and begin>end:begin=end=None;warnings.append('Invalid date range')
            if not begin or not end:warnings.append('Calendar date range incomplete or ambiguous')
            row={'course_code':subj+crse,'subject':subj,'course_number':crse,'term_code':term,'crn':crn,'section':section,
                 'section_type':get('type') or None,'days':day_list,'start_time':a,'end_time':b,
                 'start_date':begin,'end_date':end,'building':get('building') or None,'room':get('room') or None,
                 'location':get('location') or None,'capacity':int(get('capacity')) if get('capacity').isdigit() else None,
                 'raw_day':day_text,'raw_time':time_text or (get('start_time')+' - '+get('end_time')),
                 'raw_dates':date_range or (date_start+' - '+date_end).strip(' -'),
                 'teaching_weeks':None,'eligibility_verified':False,'component_linking_verified':False,
                 'source_url':course_url(term,subj,crse),'captured_at':timestamp(),'warnings':warnings,'source_table':tindex}
            rows.append(row)
            if any('unknown' in w.lower() or 'ambiguous' in w.lower() for w in warnings):
                unparsed.append({'table':tindex,'cells':cells,'reason':warnings})
    text=soup.get_text(' ',strip=True)
    absent=bool(re.search(r'no (?:classes|sections|records|courses)(?:\s+(?:were|are))? (?:found|available|offered)|no data found',text,re.I))
    if rows:status='parsed_with_warnings' if any(r['warnings'] for r in rows) else 'parsed'
    elif absent:status='not_offered'
    else:status='unrecognized_layout'
    return {'course_code':subj+crse,'term_code':term,'status':status,'meeting_rows':rows,'unparsed_course_rows':unparsed,
            'matched_tables':matched_tables,'source_url':course_url(term,subj,crse),'captured_at':timestamp(),
            'table_content_sha256':hashlib.sha256('\n'.join(str(table_grid(t)) for t in soup.find_all('table')).encode()).hexdigest()}

def frame_links(frame,term,subject):
    links=frame.locator('a[href]').evaluate_all('(xs)=>xs.map(a=>a.getAttribute("href"))')
    return {x for href in links if (x:=course_from_link(href,frame.url,term,subject))}

def choose_results(context,term,subject):
    candidates=[]
    for page in context.pages:
        for frame in page.frames:
            try:
                if urlparse(frame.url).hostname!=HOST:continue
                links=frame_links(frame,term,subject)
                if links:candidates.append((len(links),page,frame))
            except Exception:continue
    return max(candidates,key=lambda x:x[0])[1:] if candidates else None

def discover(context,term,subject,max_pages):
    while True:
        print('\nIn the opened browser: log in, then open Master Class Schedule, select the term and all MA courses (or all subjects if requested), and display the full course search results.')
        input('When those results are visible, return here and press Enter: ')
        result=choose_results(context,term,subject)
        if result:break
        print('No matching course-detail links found. Keep the search results open, including any new tab, and try again. Ctrl+C cancels.')
    page,frame=result;found=set();seen=set();pages=0;pagination_complete=True
    while True:
        links=frame_links(frame,term,subject);fingerprint=tuple(sorted(links))
        if fingerprint in seen:raise RuntimeError('Repeated results page; refusing to claim complete discovery')
        seen.add(fingerprint);found.update(links);pages+=1
        next_links=frame.get_by_role('link',name=re.compile(r'^\s*(?:Next(?:\s+Page)?|>|»|›)\s*$',re.I)).all()
        next_link=next((x for x in next_links if x.is_visible() and x.is_enabled() and x.get_attribute('aria-disabled')!='true'),None)
        if next_link is None:break
        if pages>=max_pages:raise RuntimeError('Pagination limit reached. Increase --max-pages; discovery is incomplete')
        href=next_link.get_attribute('href') or ''
        if href and not href.startswith(('#','javascript:')):
            dest=urlparse(urljoin(frame.url,href))
            if dest.scheme!='https' or dest.hostname!=HOST or re.search(r'register|logout|adddrop|withdraw|payment',dest.path,re.I):
                raise RuntimeError('Next-page control does not point to a permitted timetable page')
        next_link.click();page.wait_for_timeout(1000)
    if len(found)<2:
        raise RuntimeError('Only one course discovered. Use all-course search results, or an explicit --courses-file for a single-course run.')
    print(f'Discovered {len(found)} course links across {pages} result page(s).')
    return sorted(found),{'source':'user_selected_course_search_results','pages':pages,
                         'pagination_traversed':pagination_complete,'scope_note':'Coverage is the selected results, not proof that every institutional subject or course was included.'}

def course_document(page,subj,crse,term):
    best=None
    for frame in page.frames:
        if urlparse(frame.url).hostname!=HOST:continue
        # Inspect timetable tables only. Do not save portal/account chrome, forms, hidden tokens or login pages.
        tables=frame.locator('table').evaluate_all('(xs)=>xs.map(t=>t.outerHTML).join("\\n")')
        parsed=parse_html(tables,subj,crse,term)
        if best is None or len(parsed['meeting_rows'])>len(best['meeting_rows']):best=parsed
        if not parsed['meeting_rows']:
            text=frame.locator('body').inner_text()
            if re.search(r'no (?:classes|sections|records) (?:found|available|offered)|no data found',text,re.I):parsed['status']='not_offered'
    return best

def aggregate(out,requested,discovery):
    records=[];rows=[];pending=[]
    for subj,crse in requested:
        p=out/'courses'/(subj+crse+'.json')
        if p.exists():
            r=json.loads(p.read_text(encoding='utf-8'));records.append({'course_code':subj+crse,'status':r['status'],'meeting_rows':len(r['meeting_rows'])});rows+=r['meeting_rows']
        else:pending.append(subj+crse)
    groups={}
    for r in rows:
        ident=(r['course_code'],r['crn'],r['section'])
        # Unknown identities remain separate, rather than merging unrelated classes.
        if not r['crn'] and not r['section']:ident=(*ident,len(groups))
        groups.setdefault(ident,{'course_code':r['course_code'],'term_code':r['term_code'],'crn':r['crn'],'section':r['section'],
            'meetings':[],'eligibility_verified':False,'component_linking_verified':False})['meetings'].append(r)
    dump(out/'meeting_rows.json',rows);dump(out/'sections.json',list(groups.values()))
    dump(out/'run.json',{'captured_at':timestamp(),'discovery':discovery,'requested_courses':len(requested),
         'processed_courses':len(records),'pending_courses':pending,'courses':records,
         'meeting_rows':len(rows),'all_requested_processed':not pending,
         'timing_rows_with_unknown_values':sum(r['days'] is None or r['start_time'] is None or r['end_time'] is None for r in rows),
         'rows_with_missing_date_range':sum(r['start_date'] is None or r['end_date'] is None for r in rows),
         'all_layouts_recognized':not pending and all(r['status']!='unrecognized_layout' for r in records),
         'date_note':'Date ranges are not proof that every date in the range has a class; holidays/teaching weeks may differ.',
         'security':'Credentials entered only by user in browser. No cookie, storage-state, password, screenshot or full authenticated-page export.'})

def browser_smoke():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context();page=context.new_page()
        page.set_content('<table><tr><th>CRN</th><th>Section</th><th>Day</th><th>Time</th></tr><tr><td>12345</td><td>C01</td><td>Mon</td><td>09:00-11:50</td></tr></table>')
        result=parse_html(page.locator('table').evaluate('(t)=>t.outerHTML'),'MA','1502','202609')
        assert result['meeting_rows'][0]['start_time']=='09:00'
        context.close();browser.close()
    print('Edge browser smoke test passed on synthetic HTML; no CityU account was accessed.')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--term',default='202609');ap.add_argument('--subject',default='MA');ap.add_argument('--all-subjects',action='store_true')
    ap.add_argument('--courses-file',type=Path);ap.add_argument('--output',type=Path,default=ROOT/'data/banweb')
    ap.add_argument('--channel',choices=['msedge','chrome','chromium'],default='msedge')
    ap.add_argument('--delay',type=float,default=2.0);ap.add_argument('--max-pages',type=int,default=100)
    ap.add_argument('--resume',action='store_true');ap.add_argument('--limit',type=int)
    ap.add_argument('--offline-html',type=Path,help='Parse saved MA1502.html-style files without opening a browser.')
    ap.add_argument('--browser-smoke-test',action='store_true')
    a=ap.parse_args()
    if a.browser_smoke_test:browser_smoke();return
    subject='ALL' if a.all_subjects else a.subject.upper()
    course_url(a.term,'MA' if subject=='ALL' else subject,'1502')
    if a.delay<1 or a.max_pages<1 or a.limit is not None and a.limit<1:ap.error('delay must be >=1; limits must be positive')
    out=a.output.resolve()/a.term/subject;out.mkdir(parents=True,exist_ok=True)
    if a.offline_html:
        requested=[]
        for f in sorted(a.offline_html.glob('*.html')):
            m=re.fullmatch(r'([A-Z]{2,6})(\d{4,5}[A-Z]?)',f.stem.upper())
            if not m or subject!='ALL' and m[1]!=subject:continue
            requested.append((m[1],m[2]));dump(out/'courses'/(f.stem.upper()+'.json'),parse_html(f.read_text(encoding='utf-8-sig'),m[1],m[2],a.term))
        if not requested:raise RuntimeError('No SUBJECT1234.html files in offline folder')
        aggregate(out,requested,{'source':'explicit_saved_HTML_files'});print('Saved parsed timetable to',out);return
    raise RuntimeError('Automated authenticated collection is disabled after AIMS rejected direct access. Use import_ma_timetable.cmd with pages saved normally through CityU Portal.')

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:print('\nCancelled. Existing course JSON files remain available for --resume.');sys.exit(130)
    except Exception as exc:print('Collection stopped:',type(exc).__name__,str(exc),file=sys.stderr);sys.exit(1)
