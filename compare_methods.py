"""Compare both proposal approaches on identical explicitly synthetic schedules."""
import copy
import itertools
import json
from pathlib import Path

from build_dataset import PROFILES, course_input, messages
from inference import generate, load, validate_score, FIELDS
from scheduler import solve, conflict

ROOT = Path(__file__).resolve().parent


def violations(p, selected):
    errors = []
    lookup = {o['option_id']: o for o in p['options']}
    if not isinstance(selected, list) or any(not isinstance(x, str) for x in selected):
        return ['invalid_selection_schema']
    if len(set(selected)) != len(selected):
        errors.append('duplicate_options')
    if any(x not in lookup for x in selected):
        errors.append('invented_options')
    chosen = [lookup[x] for x in set(selected) if x in lookup]
    codes = [o['course_code'] for o in chosen]
    if len(codes) != len(set(codes)):
        errors.append('duplicate_courses')
    if not set(p['required_courses']) <= set(codes):
        errors.append('required_course_missing')
    if not p['credit_min'] <= sum(o['credits'] for o in chosen) <= p['credit_max']:
        errors.append('credit_bound')
    if any(conflict(a['meetings'], b['meetings']) for a, b in itertools.combinations(chosen, 2)):
        errors.append('timetable_conflict')
    return errors


def main():
    tok, model = load()
    test_codes = set(json.loads((ROOT / 'data/splits.json').read_text())['test'])
    cs = [json.loads(x) for x in (ROOT / 'data/courses.jsonl').read_text(encoding='utf-8').splitlines()]
    cs = [c for c in cs if c['code'] in test_codes and c['credits'] == 3][:4]
    if len(cs) != 4:
        raise ValueError('Need four three-credit held-out courses')
    rows = []
    for profile in PROFILES:
        options = []
        for i, c in enumerate(cs):
            options.append({'option_id': c['code']+'-SIM', 'course_code': c['code'], 'credits': c['credits'],
                            'term': 'SIMULATED', 'rules_reviewed': True, 'prerequisites_all': [],
                            'prerequisites_any_groups': [], 'corequisites': [], 'exclusive_courses': [],
                            'timetable_verified': True,
                            'meetings': [{'day': 1 if i < 2 else i, 'weeks': list(range(1, 14)),
                                          'start_minute': 540, 'end_minute': 600}],
                            'scores': {k: .5 for k in FIELDS}})
        p = {'data_mode': 'synthetic_constraint_fixture_not_real_CityU_timetable_or_eligibility',
             'objective_mode':'legacy_cost',
             'term': 'SIMULATED', 'options': options, 'required_courses': [cs[0]['code']],
             'completed_courses': profile['completed_courses'], 'credit_min': 9, 'credit_max': 9,'course_min':3,'course_max':3}
        # Both methods see the same course records, student and simulated constraints.
        ms = [{'role': 'system', 'content': 'Choose a course schedule from the supplied facts and synthetic constraints. Return JSON with selected_options (a list of exact option IDs) and explanation. Satisfy required courses, credits and non-overlapping meetings. All simulated rules and times override actual course eligibility for this synthetic test only.'},
              {'role': 'user', 'content': json.dumps({'student': profile, 'courses': [course_input(c) for c in cs], 'problem': p})}]
        raw = generate(tok, model, ms, baseline=True, max_tokens=384)
        try:
            selected = json.loads(raw)['selected_options']
            errs = violations(p, selected)
        except (ValueError, KeyError, TypeError):
            selected, errs = [], ['invalid_json_or_schema']
        rows.append({'profile': profile['id'], 'method': 'pure_llm_base', 'selection': selected,
                     'violations': errs, 'raw_response': raw})
        for c, o in zip(cs, p['options']):
            score_raw = generate(tok, model, messages(c, profile))
            pred = validate_score(json.loads(score_raw), c['code'])
            o['scores'] = {k: pred[k] for k in FIELDS}
        result = solve(p)
        errs = violations(p, result.get('selected_options', []))
        rows.append({'profile': profile['id'], 'method': 'fine_tuned_scores_milp',
                     'selection': result.get('selected_options'), 'violations': errs, 'solver': result})
        print('COMPARED', profile['id'], flush=True)
    summary = {'data_mode': 'synthetic_fixture_only', 'profiles': len(PROFILES),
               'methods': {method: {'schedules': len(rs := [r for r in rows if r['method'] == method]),
                                    'schedules_with_violations': sum(bool(r['violations']) for r in rs),
                                    'total_constraint_violations': sum(len(r['violations']) for r in rs)}
                           for method in ['pure_llm_base', 'fine_tuned_scores_milp']},
               'human_rankings': None, 'real_workload_mse': None,
               'limitations': 'Synthetic constraints do not measure real-student performance or score accuracy.', 'details': rows}
    (ROOT / 'reports/method_comparison.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != 'details'}, indent=2))


if __name__ == '__main__':
    main()
