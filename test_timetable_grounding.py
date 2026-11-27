import copy,json,unittest
from pathlib import Path
from cm_background_policy import ef_mismatch_penalty
from profit_objective import components,settings
from markov_planner import solve
from test_scheduler import option
from timetable_grounded_training import assessment,problem_for,records
ROOT=Path(__file__).resolve().parent

class GroundingTests(unittest.TestCase):
    def profile(self):return {'programme':'CM','programme_code':'BSCSIU4','cohort':2025,'year':1,'term':'202609','completed_courses':[]}

    def test_EF_penalty_respects_study_passes_and_weight(self):
        p=self.profile();self.assertEqual(ef_mismatch_penalty(p,'EF3320'),1.5)
        self.assertEqual(ef_mismatch_penalty({**p,'weights':{'background_mismatch':2}},'EF3320'),3)
        self.assertEqual(ef_mismatch_penalty({**p,'completed_courses':['GE1202']},'EF3320'),0)
        self.assertEqual(ef_mismatch_penalty({**p,'finance_background':True},'EF4821'),0)
        for grade in ['F','IP','W']:
            q={**p,'completed_courses':['GE1202'],'GE_history':[{'course_code':'GE1202','grade':grade}]}
            self.assertEqual(ef_mismatch_penalty(q,'EF3320'),1.5)
        self.assertEqual(ef_mismatch_penalty(p,'MA1300'),0)

    def test_EF_penalty_changes_net_profit_without_prerequisite_fee(self):
        # Synthetic unit fixture, not an offered EF registration recommendation.
        o=option('EF3320');o['profit']=1.8
        p={**self.profile(),'student_year':2,'term':'DEMO','credit_min':0,'credit_max':3,'course_min':0,'course_max':1,
            'required_courses':[],'options':[o]}
        r=solve(p);self.assertEqual(r['course_count'],0)
        q={**p,'finance_background':True};self.assertEqual(solve(q)['course_count'],1)
        a=components([o],{},0,{'background_mismatch':1,'difficulty':1,'workload':1},settings(p))
        b=components([o],{},0,{'background_mismatch':1,'difficulty':1,'workload':1},settings(q))
        self.assertAlmostEqual(b['net_profit']-a['net_profit'],1.5)

    def test_semester_and_major_are_not_interchangeable(self):
        p=self.profile()
        self.assertTrue(assessment(p,'MA3512')['timetable_available'])
        self.assertFalse(assessment({**p,'term':'202702'},'MA3512')['timetable_available'])
        self.assertFalse(assessment({**p,'term':'202709'},'MA3512')['timetable_available'])
        self.assertFalse(assessment(p,'EF4821')['timetable_available'])
        self.assertTrue(assessment({**p,'term':'202702'},'EF3320')['timetable_available'])

    def test_entering_profile_does_not_invent_five_courses(self):
        from grounded_degree import simulate
        r=simulate(self.profile());self.assertFalse(r['audit']['all_encoded_requirements_met'])
        self.assertEqual(len(r['diagnostic_semesters']),8)
        self.assertLess(r['diagnostic_semesters'][0]['course_count'],5)
        self.assertFalse(r['whole_chain_accepted'])
        self.assertIn('GE1401',r['coverage_certificate']['mandatory_without_compatible_timetable'])

    def test_every_production_option_has_current_source_and_term(self):
        from timetable_evidence import verified
        profile=json.loads((ROOT/'reports/year3-path-comparison06/cases.json').read_text())[0]['profile']
        p=problem_for(profile);byhash={(c['source_sha256'],c['programme']):c for c in records()}
        for o in p['options']:
            r=byhash[(o['source_sha256'],'CM')];self.assertTrue(verified(r));self.assertEqual(o['term'],r['term_code'])
            self.assertEqual(o['course_code'],r['course_code']);self.assertEqual(r['programme'],'CM')

    def test_changed_source_fails_closed(self):
        from timetable_evidence import verified
        c=copy.deepcopy(records()[0]);self.assertTrue(verified(c));c['source_sha256']='0'*64;self.assertFalse(verified(c))

    def test_correct_model_refusal_is_verified_not_repaired(self):
        from markov_planner import plan_from_proposal
        p=problem_for(self.profile())
        r=plan_from_proposal(p,{'status':'infeasible','selected_option_ids':[],'course_count':0})
        self.assertFalse(r['model_output_accepted']);self.assertTrue(r['policy_fallback_used'])

    def test_default_lambda_is_explicit_in_model_input(self):
        from timetable_grounded_training import messages
        p={**self.profile(),'desired_stream':'Enriched Mathematics'}
        q=json.loads(messages(p,'EF3320')[1]['content'])
        self.assertEqual(q['profile']['weights']['background_mismatch'],1.)
        self.assertNotIn('desired_stream',q['profile'])

if __name__=='__main__':unittest.main()
