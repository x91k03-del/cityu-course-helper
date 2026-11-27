import itertools,unittest
from profit_objective import settings,overload_penalty
from scheduler import solve
from test_scheduler import option
class YearSpecificTests(unittest.TestCase):
    def test_thresholds_and_legacy(self):
        for y in [1,2,3]:
            c=settings({'student_year':y})
            self.assertEqual([overload_penalty(6,c,k) for k in [12,15,16,18]],[0,0,.25,2.25])
            self.assertEqual(overload_penalty(6,settings({'student_year':y,'overload_mode':'year4_credits'}),18),0)
        c=settings({'student_year':4})
        self.assertEqual([overload_penalty(6,c,k) for k in [12,15,18]],[0,2.25,9])
    def test_solver_matches_enumeration_with_variable_credits(self):
        for year in [1,2,3,4]:
            opts=[option('DEMO'+str(i),day=i+1,cost=.2) for i in range(6)]
            for i,o in enumerate(opts):o.update(credits=3+(i%2),profit=2.5+.3*i)
            p={'student_year':year,'term':'DEMO','completed_courses':[],'required_courses':[],
               'credit_min':0,'credit_max':18,'course_min':0,'course_max':6,'options':opts}
            scores=[sum(o['profit']-.6 for o in g)-.25*max(0,sum(o['credits'] for o in g)-(12 if year==4 else 15))**2
                    for k in range(7) for g in itertools.combinations(opts,k) if sum(o['credits'] for o in g)<=18]
            self.assertAlmostEqual(solve(p)['objective'],max(scores))
if __name__=='__main__':unittest.main()
