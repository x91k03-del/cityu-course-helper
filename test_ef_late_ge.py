import copy,unittest
from degree_chain import terminal_audit
from ge_snapshot_options import options
from markov_planner import solve,validate_proposal
from profit_objective import settings,option_year_bonus,option_ge_progress
from timetable_grounded_training import problem_for

class LateEFGETests(unittest.TestCase):
    def profile(self):return {'programme':'CM','programme_code':'BSCSIU4','year':2,'term':'202702','completed_courses':[]}
    def test_timing_bonus_is_year4_only_and_not_an_eligibility_gate(self):
        o={'course_code':'EF3320'}
        for year in (1,2,3,4):
            p={**self.profile(),'year':year};q=problem_for(p)
            self.assertTrue(validate_proposal(q,{'selected_option_ids':['EF3320:11425']})['accepted'])
            self.assertEqual(option_year_bonus(o,settings(q)),4. if year==4 else 0.)
        q['programme']='CS';self.assertEqual(option_year_bonus(o,settings(q)),0.)
    def test_exact_reward_increment_and_reference_accounting(self):
        from scheduler import solve as reference
        p={**self.profile(),'year':4,'finance_background':True,'required_courses':['EF3320']}
        q=problem_for(p);q['options']=[o for o in q['options'] if o['course_code']=='EF3320']
        baseline=solve({**q,'ef3320_year4_bonus':0});r=solve(q)
        self.assertAlmostEqual(r['objective']-baseline['objective'],4.)
        self.assertAlmostEqual(reference(q)['profit_breakdown']['net_profit'],r['objective'])
    def test_ge_pool_never_invents_B_and_counts_all_captured_codes(self):
        p={**self.profile(),'term':'202609'};a=options(p)
        self.assertGreater(len(a),50);self.assertEqual(options({**p,'term':'202702'}),[])
        transcript=[{'id':code,'credits':3,'term':i+1} for i,code in enumerate(['GE1113','GE1202','GE1305','GE2134'])]
        audit=terminal_audit(p,transcript)
        self.assertEqual(audit['distribution_GE_count'],4)
        self.assertTrue(audit['checks']['GE_all_areas']);self.assertTrue(audit['checks']['GE_at_least_four'])
    def test_fourth_GE_reward_after_areas_already_covered(self):
        c=settings({**self.profile(),'student_year':2,'track_ge_graduation':True,'completed_GE_area_counts':{'1':1,'2':1,'3':1}})
        self.assertEqual(option_ge_progress({'ge_area':1},c),2.)
        c['completed_GE_area_counts']['1']=2
        self.assertEqual(option_ge_progress({'ge_area':1},c),0.)
    def test_one_GE_per_semester_is_preserved(self):
        p={**self.profile(),'term':'202609','include_GE_snapshot':True,'ge_candidate_courses':['GE1202','GE1305']}
        q=problem_for(p);q['options']=[o for o in q['options'] if o['course_code'].startswith('GE')]
        r=solve(q);self.assertEqual(r['course_count'],1)
        ids=[next(o['option_id'] for o in q['options'] if o['course_code']==code) for code in ['GE1202','GE1305']]
        self.assertIn('more_than_one_distribution_GE',validate_proposal(q,{'selected_option_ids':ids})['violations'])

if __name__=='__main__':unittest.main()
