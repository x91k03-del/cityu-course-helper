"""Small synthetic options for solver checks."""

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
