import unittest,copy
from ge_pathways import recommend
from programme_policy import chain_reward
class PathTests(unittest.TestCase):
    def test_GE_finance_selects_finance_without_credit(self):
        p=recommend({'programme':'CM','completed_courses':['GE2260']})
        self.assertEqual(p['selected_stream'],'Financial Mathematics');self.assertEqual(p['stream_reward_multiplier'],3)
        from programme_policy import stream_result
        self.assertEqual(stream_result('CM',['GE2260'],'Financial Mathematics')['completed_slots'],0)
    def test_explicit_preference_wins(self):
        self.assertEqual(recommend({'programme':'CM','completed_courses':['GE2260'],'selected_stream':'Enriched Mathematics'})['selected_stream'],'Enriched Mathematics')
    def test_finance_prerequisite_bridge(self):
        self.assertEqual(recommend({'programme':'CM','completed_courses':['GE2260']})['prerequisite_bridge_bonus'],{'MA2510':3})
        self.assertEqual(recommend({'programme':'CM','completed_courses':['GE2260','MA2510']})['prerequisite_bridge_bonus'],{})
    def test_AI_minor_major_and_allowlist_gates(self):
        self.assertEqual(recommend({'programme':'CS','completed_courses':['GE2340']})['minor']['status'],'not_allowed_for_CS_major')
        self.assertEqual(recommend({'programme':'CM','completed_courses':['GE2340']})['minor']['status'],'interest_only_blocked_by_current_course_allowlist')
    def test_lambdas_change_controlled_plans(self):
        from run_pathway_lambda import controlled_problem
        from scheduler import solve
        base=controlled_problem('CM')
        def selected(b,d,w):
            return solve({**base,'weights':{'background_mismatch':b,'difficulty':d,'workload':w}})['course_codes']
        self.assertIn('MA3521',selected(1,1,1));self.assertIn('MA3523',selected(1,20,1));self.assertIn('MA3525',selected(1,1,20))
        self.assertNotEqual(selected(0,12,1),selected(12,12,1))
    def test_bad_lambdas_rejected(self):
        from run_pathway_lambda import controlled_problem
        from scheduler import solve
        for bad in [-1,float('nan'),float('inf')]:
            p=controlled_problem('CM');p['weights']={'difficulty':bad}
            with self.assertRaises(ValueError):solve(p)
if __name__=='__main__':unittest.main()
