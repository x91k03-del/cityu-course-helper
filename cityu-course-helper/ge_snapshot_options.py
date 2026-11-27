"""Explicitly hypothetical GE bundles from the captured Semester A source.

The capture gives weekly meetings, not teaching weeks, prerequisites, component
linkage or registration eligibility. These assumptions remain visible per option.
No Semester B availability is inferred from a Semester A capture.
"""
import hashlib,json
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parent

@lru_cache(maxsize=4)
def _capture(stamp):
    path=ROOT/'sources/ge-timetable/semester_a_browser_capture.txt'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest=json.loads((ROOT/'reports/ge-timetable/import.json').read_text())
    if digest!=manifest['capture_sha256']:raise ValueError('GE capture changed; re-import and review first')
    areas=json.loads((ROOT/'data/four-year/GE_areas.json').read_text())
    courses={};current=None
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        fields=line.split('|')
        if fields[0].startswith('GE'):
            current=fields[0];courses[current]={'title':fields[2],'credits':int(fields[1]),'sections':{}}
        else:
            if len(fields)!=8:raise ValueError('Malformed GE capture')
            crn,section,kind,cap,day,clock,building,room=fields
            if kind!='Lecture' or not day or not clock.strip() or clock.strip()=='-':continue
            a,b=clock.split(' - ')
            minute=lambda t:int(t[:2])*60+int(t[3:5])
            meeting={'day':['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].index(day)+1,
                'start_minute':minute(a),'end_minute':minute(b),'weeks':list(range(1,15))}
            group=courses[current]['sections'].setdefault(crn,[])
            if meeting not in group:group.append(meeting)
    return path,digest,areas,courses

def options(profile):
    if profile['term']!='202609':return []
    path=ROOT/'sources/ge-timetable/semester_a_browser_capture.txt'
    source,digest,areas,courses=_capture(path.stat().st_mtime_ns)
    candidates=profile.get('ge_candidate_courses');done=set(profile['completed_courses']);out=[]
    for code,c in courses.items():
        if code in done or code not in areas or candidates is not None and code not in candidates:continue
        area_source=ROOT/Path(areas[code]['source_file'])
        if not area_source.exists():continue
        for crn,meetings in c['sections'].items():
            if not meetings:continue
            out.append({'option_id':code+':'+crn,'course_code':code,'credits':c['credits'],'term':profile['term'],
                'ge_area':areas[code]['area'],'rules_reviewed':True,'prerequisites_all':[],
                'prerequisites_any_groups':[],'corequisites':[],'exclusive_courses':[],
                'timetable_verified':True,'meetings':meetings,
                'scores':{'background_mismatch':.3,'difficulty':.35,'workload':.4},
                'source':str(source),'source_sha256':digest,'area_source':str(area_source),
                'area_source_sha256':hashlib.sha256(area_source.read_bytes()).hexdigest(),
                'source_url':'https://www.cityu.edu.hk/ge_info/Course/'+code,
                'teaching_weeks_assumed':True,'component_linkage_assumed':True,'GE_eligibility_assumed':True,
                'registration_verified':False,'score_basis':'editable illustrative GE rubric'})
    return out
