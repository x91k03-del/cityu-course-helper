import copy,itertools,json,unittest
from pathlib import Path
from unittest.mock import patch
from markov_planner import solve,validate_proposal,plan_from_proposal,Rules
from markov_degree import audit_sequence
from tests.helpers import option,problem

class MarkovPlannerTests(unittest.TestCase):
    def normal(self):
        return {'student_year':2,'term':'DEMO','required_courses':[],'completed_courses':[],
            'credit_min':0,'credit_max':18,'options':[option('DEMO'+str(i),day=i+1,cost=.1) for i in range(6)]}

    def test_three_course_raw_proposal_is_legal_after_policy_change(self):
        p=self.normal();raw={'selected_option_ids':[o['option_id'] for o in p['options'][:3]]}
        with patch('scheduler.milp',side_effect=AssertionError('MILP must not be used')):r=plan_from_proposal(p,raw)
        self.assertTrue(r['model_output_accepted']);self.assertEqual(r['course_count'],3)
        r=solve(p)
        self.assertAlmostEqual(sum(x['reward'] for x in r['marginal_rewards']),r['objective'])

    def test_sixth_course_depends_on_profit_and_overload(self):
        p=self.normal();p['options'][-1]['profit']=0
        r=solve(p);self.assertEqual(r['course_count'],5)
        for o in p['options']:o['profit']=8
        self.assertEqual(solve(p)['course_count'],6)

    def test_flexible_semester_with_three_eligible_courses(self):
        p=self.normal();p['course_min']=0;p['options']=p['options'][:3]
        self.assertEqual(solve(p)['course_count'],3)

    def test_valid_proposal_and_production_route(self):
        p=self.normal();raw={'selected_option_ids':[o['option_id'] for o in p['options'][:5]]}
        r=plan_from_proposal(p,raw);self.assertTrue(r['model_output_accepted']);self.assertFalse(r['policy_fallback_used'])
        root=Path(__file__).resolve().parents[1]
        case=json.loads((root/'reports/year3-path-comparison06/cases.json').read_text())[0]
        from programme_v6 import plan
        r=plan(case['profile'],True,{'selected_option_ids':['INVENTED']})
        self.assertFalse(r['model_output_accepted']);self.assertGreaterEqual(r['course_count'],5)

    def test_year4_stop_can_be_empty(self):
        p=self.normal();p['student_year']=4
        for o in p['options']:o['profit']=0
        self.assertEqual(solve(p)['course_count'],0)

    def test_unknown_duplicate_and_clashing_proposal(self):
        p=self.normal();ids=[o['option_id'] for o in p['options']]
        self.assertIn('unknown_option_ids',validate_proposal(p,{'selected_option_ids':ids+['INVENTED']})['violations'])
        self.assertIn('duplicate_course_or_option',validate_proposal(p,{'selected_option_ids':ids[:5]+ids[:1]})['violations'])
        p['options'][1]['meetings']=copy.deepcopy(p['options'][0]['meetings'])
        self.assertIn('meeting_clash',validate_proposal(p,{'selected_option_ids':ids})['violations'])

    def test_matches_exhaustive_and_milp(self):
        from scheduler import solve as reference
        from profit_objective import components,settings
        for year in (2,4):
            p=self.normal();p['student_year']=year
            for i,o in enumerate(p['options']):o.update(profit=2+i*.2,credits=3+i%2)
            rules=Rules(p);scores=[]
            for n in range(7):
                for group in itertools.combinations(p['options'],n):
                    if not rules.violations(group):scores.append(components(group,{},0,{'background_mismatch':1,'difficulty':1,'workload':1},settings(p))['net_profit'])
            r=solve(p);self.assertAlmostEqual(r['objective'],max(scores));self.assertAlmostEqual(r['objective'],reference(p)['objective'])

    def test_prior_passes_cannot_be_replaced_by_current_choices(self):
        p=self.normal();p['options'][1]['prerequisites_all']=['DEMO0']
        self.assertIn(p['options'][1]['option_id'],Rules(p).rejected)
        p['completed_courses']=['DEMO0'];self.assertNotIn(p['options'][1]['option_id'],Rules(p).rejected)

    def test_corequisites_exclusions_and_workload_caps(self):
        p=problem();p['options'][0]['corequisites']=['DEMO1002']
        self.assertEqual(solve(p)['status'],'infeasible')
        p['options'][1]['meetings'][0]['day']=3
        self.assertEqual(solve(p)['status'],'optimal')
        p['weekly_workload_caps']={'6':10}
        with self.assertRaises(ValueError):solve(p)
        for o in p['options']:o['workload_by_week']={'6':6}
        self.assertEqual(solve(p)['status'],'infeasible')

    def test_cm_waiver_does_not_extend_to_cs(self):
        base=self.normal();base.update(programme='CM',completed_courses=[])
        o=option('CS2468');o['prerequisites_all']=['MISSING'];base['options']=[o]
        self.assertNotIn(o['option_id'],Rules(base).rejected)
        base['cm_ef_cs_prerequisite_waiver']=False
        self.assertIn(o['option_id'],Rules(base).rejected)
        base.update(programme='CS',cm_ef_cs_prerequisite_waiver=True);o=option('CS3342');o['prerequisites_all']=['MISSING'];base['options']=[o]
        self.assertIn(o['option_id'],Rules(base).rejected)

    def test_GE_cap_and_language_exception(self):
        p=self.normal();p['options'][0]['course_code']='GE1105';p['options'][1]['course_code']='GE1202'
        self.assertIn('more_than_one_distribution_GE',Rules(p).violations(p['options']))
        p['options'][1]['course_code']='GE1401'
        self.assertNotIn('more_than_one_distribution_GE',Rules(p).violations(p['options']))

    def test_stream_complementarity(self):
        p=self.normal();p.update(programme='CS',student_year=4,selected_stream='Data Science',completed_courses=['CS3481','CS4480'])
        p['options']=[option('CS4487',day=1),option('CS4293',day=2)]
        r=solve(p)
        self.assertEqual(r['profit_breakdown']['stream_chain_bonus'],8)

    def test_saved_degree_and_independent_audit_reject_mutation(self):
        root=Path(__file__).resolve().parents[1]
        r=json.loads((root/'reports/markov-repair/year1_simulation.json').read_text())
        a=audit_sequence(r['input_profile'],r['steps'],r['transcript'])
        self.assertTrue(a['all_encoded_requirements_met'],a)
        bad=copy.deepcopy(r['steps']);bad[0]['selected_courses']=bad[0]['selected_courses'][:2]
        self.assertFalse(audit_sequence(r['input_profile'],bad,r['transcript'])['all_encoded_requirements_met'])

if __name__=='__main__':unittest.main()
