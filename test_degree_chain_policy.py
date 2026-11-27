import json,unittest
from pathlib import Path
from degree_chain_training import target
from degree_chain import coverage,simulate
from terminal_markov import search
from timetable_grounded_training import record_for,compatible_sections,problem_for
from markov_planner import validate_proposal

class DegreeChainTests(unittest.TestCase):
    def profile(self):return {'programme':'CM','programme_code':'BSCSIU4','cohort':2025,'year':1,'term':'202702','completed_courses':[]}
    def test_EF3320_non_business_section_corrected(self):
        p=self.profile();r=record_for(p,'EF3320');ss=compatible_sections(p,r)
        self.assertEqual([(s['section'],s['crn']) for s in ss],[('CA1','11425')])
        self.assertEqual(ss[0]['meetings'][0]['day'],'Fri');self.assertEqual(ss[0]['meetings'][0]['start_time'],'16:00')
        q={**p,'term':'202609'};self.assertIsNone(record_for(q,'EF3320'))
        problem=problem_for(p)
        self.assertIn('EF3320:11425',[o['option_id'] for o in problem['options']])
        self.assertTrue(validate_proposal(problem,{'selected_option_ids':['EF3320:11425']})['accepted'])
        self.assertFalse(validate_proposal(problem,{'selected_option_ids':['EF3320:10000']})['accepted'])
    def test_credit_boundary_and_other_requirements(self):
        for credits in [120,121,122,123]:
            self.assertEqual(target({'semester':8,'earned_credits':credits,'other_graduation_requirements_met':True})['chain_accepted'],credits>=122)
        self.assertFalse(target({'semester':7,'earned_credits':130,'other_graduation_requirements_met':True})['chain_accepted'])
        self.assertFalse(target({'semester':8,'earned_credits':130,'other_graduation_requirements_met':False})['chain_accepted'])
    def test_deprecated_five_course_profile_does_not_restore_minimum(self):
        p={**self.profile(),'term':'202609','course_min':5}
        self.assertEqual(problem_for(p)['course_min'],0)
    def test_terminal_search_takes_negative_reward_to_finish(self):
        r=search(0,2,lambda s,t:[0,3],lambda s,a,t:(s+a,-a),lambda s:s>=6,lambda s:s,width=10)
        self.assertEqual(r['status'],'complete');self.assertEqual(r['best']['state'],6)
        self.assertLess(r['best']['return'],0)
        bad=search(0,2,lambda s,t:[0,2],lambda s,a,t:(s+a,100),lambda s:s>=6,lambda s:s,width=10)
        self.assertEqual(bad['status'],'infeasible')
    def test_source_coverage_cannot_be_fixed_by_repeating_credits(self):
        p=self.profile();c=coverage(p);self.assertTrue(c['proof_of_insufficient_coverage'])
        self.assertLess(c['unique_source_credit_upper_bound'],122)
        r=simulate(p);self.assertFalse(r['whole_chain_accepted']);self.assertEqual(len(r['diagnostic_semesters']),8)
        self.assertEqual(r['recommended_semesters'],[])
        self.assertEqual(len({x['id'] for x in r['transcript']}),len(r['transcript']))
        self.assertTrue(any(s['course_count']<5 for s in r['diagnostic_semesters']))
        self.assertTrue(r['path_valid'])
        self.assertEqual(r['terminal_shortfall_penalty'],r['credit_shortfall']*1_000_000)
        self.assertAlmostEqual(r['penalised_objective'],r['discounted_academic_reward']-r['terminal_shortfall_penalty'])
    def test_extreme_penalty_guides_infeasible_candidate_without_approving_it(self):
        r=search(0,2,lambda s,t:[0,3],lambda s,a,t:(s+a,-a),lambda s:True,lambda s:s,width=10,
            terminal_reward=lambda s:-1_000_000*max(0,7-s))
        self.assertEqual(r['best']['state'],6)
        self.assertAlmostEqual(r['best']['return'],-1_000_000-3-.98*3)
if __name__=='__main__':unittest.main()
