import copy
import itertools
import json
import random
import unittest
from pathlib import Path

from scheduler import conflict, solve


def option(code, day=1, start=540, cost=.4):
    return {'option_id': code+'-01', 'course_code': code, 'credits': 3,
            'term': 'DEMO', 'rules_reviewed': True, 'prerequisites_all': [],
            'prerequisites_any_groups': [], 'corequisites': [], 'exclusive_courses': [],
            'timetable_verified': True, 'meetings': [{'day': day, 'weeks': list(range(1, 14)),
                  'start_minute': start, 'end_minute': start+60}],
            'scores': {'background_mismatch': cost, 'difficulty': cost, 'workload': cost}}


def problem():
    return {'data_mode': 'synthetic_test_fixture_not_actual_CityU_timetable',
            'objective_mode':'legacy_cost',
            'term': 'DEMO', 'required_courses': ['DEMO1001'], 'completed_courses': [],
            'credit_min': 6, 'credit_max': 6,'course_min':2,'course_max':2,
            'options': [option('DEMO1001'), option('DEMO1002', cost=.1), option('DEMO1003', day=2)]}


class SchedulerTests(unittest.TestCase):
    def test_conflict_and_required(self):
        r = solve(problem())
        self.assertEqual(r['course_codes'], ['DEMO1001', 'DEMO1003'])

    def test_missing_timetable_fails_closed(self):
        p = problem()
        p['options'][0]['timetable_verified'] = False
        self.assertEqual(solve(p)['status'], 'infeasible')

    def test_missing_prerequisite(self):
        p = problem()
        p['options'][0]['prerequisites_any_groups'] = [['PASS1001', 'PASS1002']]
        self.assertEqual(solve(p)['status'], 'infeasible')
        p['completed_courses'] = ['PASS1002']
        self.assertEqual(solve(p)['status'], 'optimal')

    def test_corequisite_and_exclusions(self):
        p = problem()
        p['options'][0]['corequisites'] = ['DEMO1002']
        self.assertEqual(solve(p)['status'], 'infeasible')
        p['options'][1]['meetings'][0]['day'] = 3
        self.assertEqual(solve(p)['status'], 'optimal')
        p['options'][0]['exclusive_courses'] = ['DEMO1002']
        self.assertEqual(solve(p)['status'], 'infeasible')

    def test_weekly_caps(self):
        p = problem()
        p['weekly_workload_caps'] = {'6': 10}
        with self.assertRaises(ValueError):
            solve(p)
        for o in p['options']:
            o['workload_by_week'] = {'6': 6}
        self.assertEqual(solve(p)['status'], 'infeasible')

    def test_meeting_boundaries_and_weeks(self):
        a = option('A')['meetings']
        b = copy.deepcopy(a)
        b[0]['start_minute'] = 600
        b[0]['end_minute'] = 660
        self.assertFalse(conflict(a, b))
        b[0]['start_minute'] = 599
        self.assertTrue(conflict(a, b))
        b[0]['weeks'] = [14]
        self.assertFalse(conflict(a, b))

    def test_alternative_sections(self):
        p = problem()
        second = copy.deepcopy(p['options'][0])
        second['option_id'] = 'DEMO1001-02'
        second['meetings'][0]['day'] = 4
        p['options'].append(second)
        r = solve(p)
        self.assertEqual(r['course_codes'].count('DEMO1001'), 1)
        self.assertIn('DEMO1002', r['course_codes'])

    def test_objective_against_exhaustive_search(self):
        rng = random.Random(21)
        for _ in range(15):
            opts = [option(f'DEMO{i}', day=rng.randint(1, 3), start=rng.choice([540, 600]), cost=rng.random()) for i in range(6)]
            p = {'objective_mode':'legacy_cost','term': 'DEMO', 'required_courses': [], 'completed_courses': [], 'credit_min': 9, 'credit_max': 9,'course_min':3,'course_max':3, 'options': opts}
            values = []
            for chosen in itertools.combinations(opts, 3):
                if not any(conflict(a['meetings'], b['meetings']) for a, b in itertools.combinations(chosen, 2)):
                    values.append(sum(sum(o['scores'].values()) for o in chosen))
            result = solve(p)
            if values:
                self.assertAlmostEqual(result['objective'], min(values), places=6)
            else:
                self.assertEqual(result['status'], 'infeasible')


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    (root / 'data/synthetic_schedule_demo.json').write_text(json.dumps(problem(), indent=2))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.defaultTestLoader.loadTestsFromTestCase(SchedulerTests))
    report = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'random_bruteforce_instances': 15, 'synthetic_demo_result': solve(problem())}
    (root / 'reports/scheduler_tests.json').write_text(json.dumps(report, indent=2))
    raise SystemExit(not result.wasSuccessful())
