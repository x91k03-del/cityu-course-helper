"""Offline CityU timetable import: no browser automation, login, HTTP or cookies."""
import argparse,hashlib,html,json,re,sys
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from bs4 import BeautifulSoup,Comment
from collect_banweb_timetable import ROOT,ALIASES,key,table_grid,parse_html,dump,aggregate,course_file

DEFAULT_INPUT=ROOT/'MA_SAVED_PAGES'

def documents(path):
    data=path.read_bytes()
    if path.suffix.lower() in {'.mhtml','.mht'}:
        message=BytesParser(policy=policy.default).parsebytes(data)
        for i,part in enumerate(message.walk()):
            if part.get_content_type()!='text/html':continue
            raw=part.get_payload(decode=True)
            if raw is not None:yield i,raw,str(part.get('Content-Location',''))
    else:yield 0,data,''

def source_identity(soup,location):
    # Read only source course/term identifiers. Never export the full source URL.
    sources=[location]
    for comment in soup.find_all(string=lambda s:isinstance(s,Comment)):
        if 'saved from url' in str(comment).lower():
            match=re.search(r'https?://\S+',str(comment))
            if match:sources.append(match.group().rstrip(' >'))
    for source in sources:
        u=urlparse(source)
        if u.hostname!='banweb.cityu.edu.hk':continue
        qs={k.lower():v[-1] for k,v in parse_qs(u.query).items()}
        subj=qs.get('subj','').upper();crse=qs.get('crse','').upper();term=qs.get('term')
        identity=(subj,crse) if re.fullmatch(r'[A-Z]{2,6}',subj) and re.fullmatch(r'\d{4,5}[A-Z]?',crse) else None
        if identity or term:return identity,term
    return None,None

def mapping(row):
    return {name:i for i,cell in enumerate(row) for name,aliases in ALIASES.items() if key(cell) in aliases}

def table_html(grid):
    return '<table>'+''.join('<tr>'+''.join('<td>'+html.escape(cell).replace('\n','<br>')+'</td>' for cell in row)+'</tr>' for row in grid)+'</table>'

def import_file(path,term,subject):
    parsed=[];problems=[]
    fname=re.fullmatch(r'([A-Z]{2,6})(\d{4,5}[A-Z]?)',path.stem.upper())
    filename_identity=(fname[1],fname[2]) if fname else None
    for part_index,raw,location in documents(path):
        soup=BeautifulSoup(raw,'html.parser')
        identity,source_term=source_identity(soup,location)
        if source_term and source_term!=term:
            problems.append({'part':part_index,'reason':'Source term differs from requested term','source_term':source_term});continue
        fallback=identity or filename_identity
        if identity and filename_identity and identity!=filename_identity:
            problems.append({'part':part_index,'reason':'Filename and embedded source course disagree'});continue
        for table_index,table in enumerate(soup.find_all('table')):
            grid=table_grid(table);header=None;header_index=0
            for i,row in enumerate(grid[:15]):
                m=mapping(row)
                if 'day' in m and ('time' in m or {'start_time','end_time'}<=set(m)):
                    header=m;header_index=i;break
            if header is None:continue
            term_col=next((i for i,c in enumerate(grid[header_index]) if key(c) in {'term','termcode','semester'}),None)
            body=[]
            for row in grid[header_index+1:]:
                value=row[term_col].strip() if term_col is not None and term_col<len(row) else ''
                if re.fullmatch(r'20\d{4}',value):
                    if value!=term:continue
                body.append(row)
            # Blank/unrecognised term cells must not inherit evidence from another row.
            table_term_confirmed=bool(body) and term_col is not None and all(
                term_col<len(row) and row[term_col].strip()==term for row in body)
            grid=grid[:header_index+1]+body
            ids=set()
            def get(row,k):return row[header[k]].strip() if k in header and header[k]<len(row) else ''
            for row in grid[header_index+1:]:
                s=get(row,'subject').upper();c=re.match(r'\d{4,5}[A-Z]?',get(row,'course_number').upper())
                full=re.match(r'([A-Z]{2,6})\s*(\d{4,5}[A-Z]?)',get(row,'course_code').upper())
                if full:ids.add((full[1],full[2]))
                elif re.fullmatch(r'[A-Z]{2,6}',s) and c:ids.add((s,c.group()))
            if not ids and fallback:ids.add(fallback)
            if not ids:
                # Only accept an actual nearest course heading; do not infer from unrelated body text.
                heading=table.find_previous(['h1','h2','h3','h4'])
                full=re.search(r'\b([A-Z]{2,6})\s*(\d{4,5}[A-Z]?)\b',heading.get_text(' ',strip=True) if heading else '')
                if full:ids.add((full[1],full[2]))
            if not ids:
                problems.append({'part':part_index,'table':table_index,'reason':'Meeting table has no course-code column or identifiable course heading; save the individual page as MA1502.html, or supply a source-preserving MHTML.'});continue
            clean=table_html(grid[header_index:])
            for subj,crse in sorted(ids):
                if subject!='ALL' and subj!=subject:continue
                result=parse_html(clean,subj,crse,term)
                if result['status']=='unrecognized_layout':
                    problems.append({'part':part_index,'table':table_index,'course_code':subj+crse,'reason':'No matching course rows recognized'});continue
                for row in result['meeting_rows']:
                    row.update(source_file=str(path.resolve()),source_part=part_index,source_table=table_index,
                               term_verification='embedded_source_term' if source_term or table_term_confirmed else 'user_selected_term_not_independently_verified')
                result['import_source_file']=str(path.resolve());parsed.append(result)
    if not parsed and not problems:problems.append({'reason':'No supported meeting table found; the file may be a login, error, or portal-wrapper page.'})
    return parsed,problems

def run_import(folder,output,term='202609',subject='MA',expected_file=None):
    files=sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {'.html','.htm','.mhtml','.mht'})
    if not files:raise ValueError('No saved HTML/MHTML files found. Sign in normally through CityU Portal, save the MA course-result pages in '+str(folder))
    courses={};issues=[];file_report=[]
    for path in files:
        records,warnings=import_file(path,term,subject)
        issues.extend({'file':path.name,**w} for w in warnings)
        file_report.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'parsed_course_tables':len(records)})
        for r in records:
            code=r['course_code']
            if code not in courses:courses[code]={**r,'meeting_rows':[],'unparsed_course_rows':[]}
            courses[code]['meeting_rows']+=r['meeting_rows'];courses[code]['unparsed_course_rows']+=r['unparsed_course_rows']
    if not courses:
        dump(output/'offline_import.json',{'files':file_report,'issues':issues,'imported_courses':0,'complete':False})
        raise ValueError('No matching timetable records could be imported. See '+str(output/'offline_import.json'))
    for code,r in courses.items():
        # Remove exact duplicate meeting records across repeated saved pages; retain distinct rooms/times.
        seen=set();unique=[]
        for row in r['meeting_rows']:
            signature=tuple(json.dumps(row[k],sort_keys=True) for k in ['course_code','crn','section','section_type','days','start_time','end_time','start_date','end_date','building','room','location'])
            if signature not in seen:seen.add(signature);unique.append(row)
        r['meeting_rows']=unique
        r['status']='parsed_with_warnings' if any(x['warnings'] for x in unique) else 'parsed'
        dump(output/'courses'/(code+'.json'),r)
    requested=sorted((re.match(r'([A-Z]{2,6})(\d{4,5}[A-Z]?)$',code)[1],re.match(r'([A-Z]{2,6})(\d{4,5}[A-Z]?)$',code)[2]) for code in courses)
    expected=course_file(expected_file,subject) if expected_file else requested
    dump(output/'requested_courses.json',[s+c for s,c in expected])
    aggregate(output,requested,{'source':'local_user_saved_HTML_or_MHTML','selected_term':term,'scope_note':'Only the saved pages are covered. This does not prove that all MA courses were exported.'})
    # Independent missing coverage: existing output files must not count as newly imported inputs.
    missing=sorted(s+c for s,c in expected if s+c not in courses)
    run=json.loads((output/'run.json').read_text(encoding='utf-8'))
    run.update(requested_courses=len(expected),pending_courses=missing,all_requested_processed=not missing,
               scope_complete_verified=False)
    dump(output/'run.json',run)
    report={'files':file_report,'issues':issues,'imported_courses':len(courses),
            'meeting_rows':sum(len(r['meeting_rows']) for r in courses.values()),'missing_expected_courses':missing,
            'all_expected_present_in_this_import':not missing if expected_file else None,
            'complete_export_verified':False,'network_requests':0,'browser_automation':False,
            'source_term_verified_rows':sum(row['term_verification']=='embedded_source_term' for r in courses.values() for row in r['meeting_rows'])}
    dump(output/'offline_import.json',report)
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',type=Path,default=DEFAULT_INPUT);ap.add_argument('--term',default='202609')
    ap.add_argument('--subject',default='MA');ap.add_argument('--all-subjects',action='store_true')
    ap.add_argument('--output',type=Path,default=ROOT/'data/banweb-offline');ap.add_argument('--expected-courses',type=Path)
    a=ap.parse_args();subject='ALL' if a.all_subjects else a.subject.upper()
    if not re.fullmatch(r'20\d{4}',a.term) or subject!='ALL' and not re.fullmatch(r'[A-Z]{2,6}',subject):ap.error('Invalid term or subject')
    a.input.mkdir(parents=True,exist_ok=True)
    out=a.output.resolve()/a.term/subject
    report=run_import(a.input.resolve(),out,a.term,subject,a.expected_courses)
    print(json.dumps(report,ensure_ascii=False,indent=2));print('\nSaved timetable:',out)
    if report['issues'] or report['missing_expected_courses']:print('Some pages or expected courses need review; inspect offline_import.json.')

if __name__=='__main__':
    try:main()
    except Exception as exc:print('Import stopped:',str(exc),file=sys.stderr);sys.exit(1)
