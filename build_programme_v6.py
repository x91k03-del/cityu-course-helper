"""Import user PDFs, preserving source versions, terms, restrictions and parse failures."""
import hashlib,json,re,random
from pathlib import Path
import project_runtime
from pypdf import PdfReader
from ma_timetable import parse_pdf
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data/programme-v6';REPORT=ROOT/'reports/programme-v6'
CODE=r'\b[A-Z]{2,6}\d{4}[A-Z]?\b'
def save(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def extract(path):return [p.extract_text(extraction_mode='layout') or '' for p in PdfReader(path).pages]
def main():
    DATA.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    sources={'CM':ROOT/'GE_SEMA/MA/CMcourses.pdf','CS':ROOT/'GE_SEMA/CS/programme discription/Majors.pdf'}
    manifest=[];lists={};texts={}
    for major,path in sources.items():
        pages=extract(path);texts[major]='\n'.join(pages)
        lists[major]=sorted(set(re.findall(CODE,texts[major])))
        manifest.append({'programme':major,'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'catalogue_urls':sorted(set(re.findall(r'https://www.cityu.edu.hk/catalogue/\S+',texts[major]))),'codes':len(lists[major])})
        save(DATA/(major+'_pages.json'),pages)
    ge=set(json.loads((ROOT/'data/four-year/GE_areas.json').read_text()))|{'GE1401','GE1501','GE1601','GE2401'}
    # GE requires evidence in the captured GE list; prefixes alone do not authorize invented courses.
    streams={'CM':{
      'Enriched Mathematics':{'required':['MA3523','MA4542','MA4545'],'options':['MA4528','MA4546','MA4551'],'choose':1,'slots':4},
      'Financial Mathematics':{'required':['MA3521','MA4529'],'options':['MA4537','EF3320','EF4821'],'choose':2,'slots':4}},
      'CS':{
      'Artificial Intelligence':{'core_choice':['CS4486','CS4487'],'options':['CS3383','CS4186','CS4386','CS4486','CS4487','CS4489','CS4490','CS4493'],'choose':2,'slots':3},
      'Data Science':{'required':['CS3481','CS4480','CS4487'],'slots':3},
      'Cybersecurity':{'required':['CS4286','CS4293','CS4394'],'slots':3},
      'Multimedia Computing':{'required':['CS3483','CS4182'],'options':['CS3189','CS4185','CS4186','CS4187','CS4188'],'choose':1,'slots':3},
      'Software Engineering and Project Management':{'options':['CS3346','CS3356','CS4348','CS4389'],'choose':3,'slots':3}}}
    for major,rules in streams.items():
        for rule in rules.values():assert set(rule.get('required',[])+rule.get('options',[])+rule.get('core_choice',[]))<=set(lists[major])
    save(DATA/'policy.json',{'allowlists':lists,'GE_codes':sorted(ge),'streams':streams,'sources':manifest,
       'scope':'Document membership is necessary, not sufficient, for registration. CM source is historical 2022/23; CS major page 2026/27 differs from supplied 2025 suggested plan. No cohort reconciliation is assumed.',
       'special_route':'CS ACT (JS1070) has compulsory DSC3026/CS3505 route-specific requirements; not auto-assigned to other admission routes.',
       'stream_policy':'One stream is rewarded as a user preference. Academic declaration is optional; no claim of formal declaration is made.'})
    records=[];failures=[];seen=set()
    jobs=[(ROOT/'GE_SEMA/MA/SEMA','202609','CM',True),(ROOT/'GE_SEMA/MA/SEMB','202702','CM',True),
       (ROOT/'GE_SEMA/CS/cs sema time','202609','CS',True),(ROOT/'GE_SEMA/CS/cs semb time','202702','CS',True)]
    for folder,term,major,recurse in jobs:
        paths=folder.rglob('*.pdf') if recurse else folder.glob('*.pdf')
        for path in sorted(paths):
            if not re.fullmatch(r'(?:MA|CS|EF)\d{4}[A-Z]?(?:_SEMB)?',path.stem.upper()):continue
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if (digest,term,major) in seen:continue
            seen.add((digest,term,major));pages=extract(path)
            source={'file':str(path),'sha256':digest,'term':term,'programme':major}
            try:
                record=parse_pdf(path,term,major);record['snapshot_date']='2026-11-21' if '2026/11/21' in '\n'.join(pages) else record['snapshot_date']
                record['programme']=major;record['document_allowed']=record['course_code'] in lists[major] or record['course_code'] in ge
                if not record['document_allowed']:record['sections']=[]
                records.append(record);manifest.append({**source,'status':'parsed','sections':len(record['sections'])})
            except Exception as e:
                failures.append({**source,'error':str(e),'source_pages':pages})
                manifest.append({**source,'status':'quarantined','error':str(e)})
    save(DATA/'courses.json',records);save(DATA/'quarantine.json',failures);save(REPORT/'sources.json',manifest)
    plan=next((ROOT/'GE_SEMA/CS/programme discription').glob('Nom*.pdf'));save(DATA/'CS_suggested_plan_pages.json',extract(plan))
    save(REPORT/'import.json',{'courses':len(records),'sections':sum(len(r['sections']) for r in records),'quarantined':len(failures),
      'CM_codes':len(lists['CM']),'CS_codes':len(lists['CS']),'GE_codes':len(ge),'deduplicated_timetable_files':len(seen)})
    print((REPORT/'import.json').read_text())
if __name__=='__main__':main()
