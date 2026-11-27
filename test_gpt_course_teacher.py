import copy,json,unittest
from pathlib import Path
from preparation import benefits,from_transcript,graph,profile_passes
from markov_planner import solve
from test_scheduler import option

class TeacherTests(unittest.TestCase):
    def test_direct_benefits_and_no_stacking(self):
        self.assertEqual(benefits(['MA2503'])['CS4487'],.25)
        self.assertEqual(benefits(['MA2503','MA2510','MA3515'])['CS4487'],.25)
        self.assertEqual(benefits(['GE1202'])['EF3320'],.10)
        self.assertEqual(benefits(['MA3515'])['EF3320'],.25)
        self.assertTrue(all(v<=.35 for v in benefits([e['source'] for e in graph()['edges']]).values()))

    def test_no_recursive_self_or_failed_pass(self):
        self.assertEqual(benefits(['MA2510'])['MA4529'],0)
        self.assertEqual(benefits(['MA3521','MA4529'])['MA4529'],0)
        self.assertEqual(from_transcript([{'id':'MA2503','grade':'F'}])['CS4487'],0)
        for grade in ['F','IP','W']:
            self.assertNotIn('MA2503',profile_passes({'completed_courses':['MA2503'],'transcript':[{'id':'MA2503','grade':grade}]}))

    def test_controlled_selection_flip(self):
        fixed=[option('DEMO'+str(i),day=i+1,cost=.1) for i in range(4)]
        ml=option('CS4487',day=5,cost=.1);other=option('DEMO_ALT',day=5,cost=.1);other['profit']=3.1
        p={'student_year':2,'term':'DEMO','required_courses':[o['course_code'] for o in fixed],
          'completed_courses':['CS3481'],'credit_min':15,'credit_max':15,'course_min':5,'course_max':5,'options':fixed+[ml,other]}
        before=solve(p);after=solve({**p,'completed_courses':['CS3481','MA2503']})
        self.assertIn('DEMO_ALT',before['course_codes']);self.assertIn('CS4487',after['course_codes'])
        self.assertEqual(after['profit_breakdown']['preparation_by_course']['CS4487'],.25)

    def test_bonus_never_unlocks_a_course(self):
        o=option('CS4487');p={'student_year':4,'term':'DEMO','required_courses':['CS4487'],'completed_courses':['MA2503'],
            'credit_min':3,'credit_max':3,'course_min':1,'course_max':1,'options':[o]}
        self.assertEqual(solve(p)['status'],'infeasible')

if __name__=='__main__':unittest.main()
