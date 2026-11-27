"""Insert only measured experiment data into the authored inline timetable fragment."""
import json,re,sys
from pathlib import Path
from test_cm_profiles import FIXTURES,OUT,read

def explanation(text):
    if text=='incorrect_completed_course_extraction':return 'Incorrect transcript pass/fail extraction'
    if text.startswith('invalid_or_incomplete_component_option:'):return text.split(':')[1]+': invalid or missing lecture/tutorial component'
    if text.startswith('missing_or_invented_meetings:'):return text.split(':')[1]+': missing or invented meeting times'
    if text.startswith('ineligible:'):
        _,code,why,*rest=text.split(':')
        messages={'combined_requirement_not_satisfied':'preparation requirement not met','already_completed':'already passed',
                  'exclusive_course_completed':'conflicts with a completed exclusive course','restriction':'wrong '+(' / '.join(rest) or 'restriction')}
        return code+': '+messages.get(why,why)
    return text.replace('_',' ')

def fill(path):
    profiles=read(FIXTURES/'profiles.json');results=read(OUT/'predictions.json');refs=read(OUT/'reference_schedules.json')
    by={r['profile_id']:r for r in results if r['mode']=='grounded'};references={r['profile_id']:r for r in refs}
    values=[]
    for p in profiles:
        r=by[p['profile_id']]
        try:model=json.loads(r['raw_model_response']).get('selected_options',[])
        except (ValueError,AttributeError):model=[]
        values.append({'id':p['profile_id'],'label':p['label'],'transcript':'; '.join(x['course_code']+' '+x['grade'] for x in p['transcript']),
            'model':model,'reference':references[p['profile_id']]['selected_options'],
            'passed':r['grading']['all_checks_passed'],'errors':[explanation(e) for e in r['grading']['errors']]})
    payload=json.dumps({'profiles':values},ensure_ascii=True,separators=(',',':')).replace('<',chr(92)+'u003c')
    markup=path.read_text(encoding='utf-8')
    updated,count=re.subn(r'(<script type="application/json" id="cm-schedule-data">).*?(</script>)',
                         lambda m:m[1]+payload+m[2],markup,flags=re.S)
    assert count==1;assert len(updated.encode())<1000000
    path.write_text(updated,encoding='utf-8');print('Filled measured data for',len(values),'profiles; bytes:',len(updated.encode()))

if __name__=='__main__':fill(Path(sys.argv[1]))
