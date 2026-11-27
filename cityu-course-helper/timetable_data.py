"""Read saved timetable evidence and construct external planning problems."""
import copy,json
from pathlib import Path
import project_runtime

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/timetable-grounded'

def records():
    active=ROOT/'data/active_timetable_evidence.json'
    folder=ROOT/json.loads(active.read_text())['courses_dir'] if active.exists() else DATA/'snapshot'
    return json.loads((folder/'courses.json').read_text())


def compatible_sections(profile,record):
    if not record:return []
    from timetable_evidence import verified
    if not verified(record):return []
    from section_eligibility import preferred
    return preferred(record['sections'],profile)


def problem_for(profile):
    import programme_v6
    captured=[]
    def capture(p):captured.append(copy.deepcopy(p));return {'status':'infeasible'}
    original=programme_v6.solve
    try:programme_v6.solve=capture;programme_v6.plan(profile,True)
    finally:programme_v6.solve=original
    return captured[0]
