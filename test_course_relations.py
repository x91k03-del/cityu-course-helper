import unittest,copy
from course_relations import *
from scheduler import solve
from test_scheduler import option
class RelationTests(unittest.TestCase):
    def test_GE_is_not_EF_prerequisite_substitution(self):
        self.assertFalse(check_rules('EF3320',['GE2260'])['known_prerequisites_satisfied'])
        self.assertTrue(check_rules('EF3320',['CB3410'])['known_prerequisites_satisfied'])
        self.assertTrue(check_rules('EF3320',['FB3410'])['known_prerequisites_satisfied'])
    def test_finance_GE_exclusion_both_directions(self):
        self.assertEqual(check_rules('CB3410',['GE2260'])['exclusive_conflicts'],['GE2260'])
        self.assertEqual(check_rules('GE2260',['CB3410'])['exclusive_conflicts'],['CB3410'])
    def test_EF_chain_all_not_any(self):
        self.assertFalse(check_rules('EF4820',['EF3520'])['known_prerequisites_satisfied'])
        self.assertTrue(check_rules('EF4820',['EF3520','EF4321'])['known_prerequisites_satisfied'])
        self.assertFalse(check_rules('EF4821',['GE2260','MA4529'])['known_prerequisites_satisfied'])
    def test_CM_route_blocked_despite_high_finance_interest(self):
        a=finance_audit('CM',['GE2260','MA1301','MA2510'],{'cm_ef_cs_prerequisite_waiver':False})
        self.assertTrue(all(r['no_currently_allowed_prerequisite_route'] for r in a['EF_options']))
    def test_scheduler_rejects_fake_reviewed_EF_option(self):
        for code,major,done in [('EF3320','CM',['GE2260']),('CB3410','CS',['GE2260'])]:
            o=option(code)
            p={'programme':major,'cm_ef_cs_prerequisite_waiver':False,'student_year':4,'term':'DEMO','completed_courses':done,'required_courses':[code],
              'course_min':1,'course_max':1,'credit_min':3,'credit_max':3,'options':[o]}
            self.assertEqual(solve(p)['status'],'infeasible')
    def test_precursor_not_promoted_to_hard_prerequisite(self):
        self.assertIsNone(check_rules('CS4335',[])['known_prerequisites_satisfied'])
        self.assertTrue(any(r['target']=='CS4335' for r in graph()['advisory_precursors']))
    def test_inferred_math_background_does_not_unlock_ML(self):
        self.assertFalse(check_rules('CS4487',['MA2503','MA3515','MA2510'])['known_prerequisites_satisfied'])
        self.assertTrue(check_rules('CS4487',['CS3481'])['known_prerequisites_satisfied'])
    def test_conflicting_GE_PDF_is_not_claimed_as_certain(self):
        self.assertEqual(check_rules('GE2260',['GE1202'])['source_conflict_courses_needing_confirmation'],['GE1202'])
if __name__=='__main__':unittest.main()
