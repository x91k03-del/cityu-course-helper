"""Bounded, source-informed preparation hypotheses; never registration rules."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PASS={'A+','A','A-','B+','B','B-','C+','C','C-','D','P'}
def graph():
    active=ROOT/'data/active_preparation_graph.json'
    path=ROOT/json.loads(active.read_text())['path'] if active.exists() else ROOT/'data/preparation-v5.json'
    return json.loads(path.read_text(encoding='utf-8'))
def benefits(passed):
    done=set(passed);out={};g=graph();graph_cap=g.get('max_preparation_benefit',.35)
    for edge in g['edges']:
        target=edge['target'];out.setdefault(target,0.)
        if edge['source'] in done and target not in done and edge['source']!=target:out[target]=min(graph_cap,max(out[target],edge['benefit']))
    return dict(sorted(out.items()))
def from_transcript(rows):return benefits(r['id'] for r in rows if r['grade'] in PASS)

def profile_passes(profile):
    done=set(profile.get('completed_courses',[]))
    for field in ['failed_courses','in_progress_courses','withdrawn_courses']:done-=set(profile.get(field,[]))
    observations={}
    for field in ['transcript','course_results','GE_history']:
        for row in profile.get(field,[]):
            code=row.get('course_code',row.get('id'));grade=str(row.get('grade','')).upper()
            if code and grade:observations.setdefault(code,[]).append(grade)
    for code,grades in observations.items():
        if not any(g in PASS for g in grades):done.discard(code)
    return sorted(done)
def grade(expected,value):
    if isinstance(expected,dict):return isinstance(value,dict) and set(expected)==set(value) and all(grade(v,value[k]) for k,v in expected.items())
    import math
    return type(value) in (int,float) and math.isfinite(value) and abs(value-expected)<1e-7
