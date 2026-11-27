import copy,itertools,random,unittest
from scheduler import solve,conflict
from test_scheduler import option
from planning_policy import cm_priority_weights,apply_profile_policy

def full_problem():
    return {'overload_mode':'course_count','term':'DEMO','required_courses':[],'completed_courses':[],'credit_min':15,'credit_max':18,
            'options':[option('MA'+str(3500+i),day=1+i//5,start=480+75*(i%5),cost=.1) for i in range(7)]}

class FiveCourseTests(unittest.TestCase):
    def test_default_five_distinct_courses(self):
        r=solve(full_problem());self.assertEqual(r['course_count'],5);self.assertEqual(r['credits'],15)
    def test_tutorials_and_alternatives_do_not_pad_count(self):
        p=full_problem();p['options']=p['options'][:4]
        duplicate=copy.deepcopy(p['options'][0]);duplicate['option_id']+='ALT';p['options'].append(duplicate)
        tutorial=copy.deepcopy(p['options'][0]);tutorial.update(course_code='MA9999',option_id='TUT',credits=0);p['options'].append(tutorial)
        r=solve(p);self.assertEqual(r['status'],'infeasible');self.assertEqual(r['eligible_course_count'],4)
    def test_five_not_relaxed_for_credit_limit(self):
        p=full_problem();p['credit_max']=12;p['credit_min']=9
        self.assertEqual(solve(p)['status'],'infeasible')
    def test_priority_can_outweigh_easy_elective(self):
        p=full_problem();p.update(course_max=5,course_priority_weights={'MA3506':3},graduation_priority_weight=3)
        for k in p['options'][-1]['scores']:p['options'][-1]['scores'][k]=1.
        self.assertIn('MA3506',solve(p)['course_codes'])
    def test_priority_never_bypasses_prerequisite(self):
        p=full_problem();p.update(course_priority_weights={'MA3506':100},graduation_priority_weight=100)
        p['options'][-1]['prerequisites_all']=['PASS1001']
        self.assertNotIn('MA3506',solve(p)['course_codes'])
    def test_year_weights_and_completed_core(self):
        p=cm_priority_weights(2,[]);self.assertGreater(p['MA2508'],p['MA3512'])
        p=cm_priority_weights(3,['MA3512']);self.assertNotIn('MA3512',p);self.assertEqual(p['MA3518'],3)
        p=apply_profile_policy({}, {'major':'Computing Mathematics','year':2,'completed_courses':[]})
        self.assertEqual(p['course_min'],5);self.assertEqual(p['course_max'],6)
    def test_objective_matches_enumeration(self):
        rng=random.Random(20261116)
        for _ in range(10):
            p=full_problem();p.update(objective_mode='legacy_cost',course_priority_weights={'MA3500':3,'MA3506':1},graduation_priority_weight=2.)
            for o in p['options']:
                for key in o['scores']:o['scores'][key]=rng.random()
            choices=[]
            for n in [5,6]:
                for group in itertools.combinations(p['options'],n):
                    cost=sum(sum(o['scores'].values()) for o in group)+2*sum(v for c,v in p['course_priority_weights'].items() if c not in {o['course_code'] for o in group})
                    choices.append(cost)
            self.assertAlmostEqual(solve(p)['objective'],min(choices),places=6)

if __name__=='__main__':unittest.main(verbosity=2)
