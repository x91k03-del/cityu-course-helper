import copy,itertools,math,random,unittest
from scheduler import solve,conflict
from profit_objective import settings,overload_penalty
from test_scheduler import option

def fixture(count=8):
    return {'overload_mode':'course_count','term':'DEMO','required_courses':[],'completed_courses':[],
            'course_min':5,'course_max':count,'credit_min':15,'credit_max':3*count,
            'options':[option('DEMO'+str(1000+i),day=1+i//5,start=480+(i%5)*75,cost=.1) for i in range(count)]}

class ProfitTests(unittest.TestCase):
    def test_increasing_overload(self):
        config=settings({'overload_mode':'course_count'});self.assertEqual([overload_penalty(n,config) for n in [5,6,7,8]],[0,3,12,27])
    def test_penalty_prevents_collecting_every_positive_profit_course(self):
        p=fixture();p['overload_penalty_weight']=0
        self.assertEqual(solve(p)['course_count'],8)
        p['overload_penalty_weight']=3
        r=solve(p);self.assertEqual(r['course_count'],5);self.assertEqual(r['objective_sense'],'maximize')
        self.assertAlmostEqual(r['profit_breakdown']['net_profit'],13.5)
        self.assertAlmostEqual(r['profit_breakdown']['schedule_loss'],-13.5)
    def test_high_extra_profit_can_justify_overload(self):
        p=fixture();p['base_course_profit']=8
        r=solve(p);self.assertEqual(r['course_count'],6)
        self.assertAlmostEqual(r['profit_breakdown']['overload_penalty'],3.)
        # The seventh course offers 7.7 but increases the penalty by 9.
    def test_per_course_profit_override(self):
        p=fixture(6);p['course_max']=5;p['options'][-1]['profit']=20
        self.assertIn('DEMO1005',solve(p)['course_codes'])
    def test_profit_never_overrides_eligibility_or_minimum(self):
        p=fixture(6);p['options'][-1].update(profit=1e6,prerequisites_all=['PASS1001'])
        r=solve(p);self.assertEqual(r['course_count'],5);self.assertNotIn('DEMO1005',r['course_codes'])
        p['options'][0]['timetable_verified']=False
        self.assertEqual(solve(p)['status'],'infeasible')
    def test_alternative_sections_dont_duplicate_profit_or_count(self):
        p=fixture(5);duplicate=copy.deepcopy(p['options'][0]);duplicate['option_id']='ALT';p['options'].append(duplicate)
        r=solve(p);self.assertEqual(r['course_count'],5);self.assertAlmostEqual(r['profit_breakdown']['course_profit'],15)
    def test_exact_milp_matches_bruteforce(self):
        rng=random.Random(2026111603)
        for i in range(16):
            p=fixture(8);p.update(base_course_profit=rng.uniform(.5,9),overload_penalty_weight=rng.uniform(0,5),
                course_priority_weights={'MA3512':3},graduation_priority_weight=2.)
            p['options'][0]['course_code']='MA3512'
            for o in p['options']:
                o['profit']=rng.uniform(.2,10)
                o['scores']={k:rng.random() for k in o['scores']}
                o['meetings'][0]['day']=rng.randint(1,4)
                o['meetings'][0]['start_minute']=rng.choice([540,600,660])
                o['meetings'][0]['end_minute']=o['meetings'][0]['start_minute']+60
            possible=[]
            for count in range(5,9):
                for group in itertools.combinations(p['options'],count):
                    if any(conflict(a['meetings'],b['meetings']) for a,b in itertools.combinations(group,2)):continue
                    gross=sum(o['profit']+2*p['course_priority_weights'].get(o['course_code'],0) for o in group)
                    cost=sum(sum(o['scores'].values()) for o in group)
                    penalty=p['overload_penalty_weight']*max(0,count-5)**2
                    possible.append(gross-cost-penalty)
            result=solve(p)
            if not possible:self.assertEqual(result['status'],'infeasible')
            else:self.assertAlmostEqual(result['objective'],max(possible),places=6)
    def test_invalid_profit_settings_fail(self):
        for field,value in [('overload_penalty_weight',-1),('base_course_profit',math.nan),('overload_reference_courses',True)]:
            p=fixture();p[field]=value
            with self.assertRaises(ValueError):solve(p)
        p=fixture();p['options'][0]['profit']=float('inf')
        with self.assertRaises(ValueError):solve(p)

if __name__=='__main__':unittest.main(verbosity=2)
