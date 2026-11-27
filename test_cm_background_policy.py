import copy
import unittest
from cm_background_policy import finance_background,waives_prerequisites,target
from ge_pathways import recommend,course_scores
from scheduler import solve
from stream_path import plan_stream
from test_scheduler import option

class CMBackgroundTests(unittest.TestCase):
    def problem(self,major,code):
        return {'programme':major,'student_year':4,'term':'DEMO','completed_courses':[],
          'required_courses':[code],'course_min':1,'course_max':1,'credit_min':3,'credit_max':3,
          'options':[option(code)]}
    def test_CM_EF_and_CS_prerequisites_waived_in_solver(self):
        for code in ['EF3320','EF4821','CS4487']:
            p=self.problem('CM',code);p['options'][0]['prerequisites_all']=['MISSING1001']
            r=solve(p);self.assertEqual(r['status'],'optimal')
            self.assertEqual(r['prerequisite_waivers_assumed'],[code])
            p['cm_ef_cs_prerequisite_waiver']=False
            self.assertEqual(solve(p)['status'],'infeasible')
    def test_CS_and_math_are_not_waived(self):
        self.assertEqual(solve(self.problem('CS','CS4487'))['status'],'infeasible')
        self.assertFalse(waives_prerequisites({'programme':'CM'},'MA3521'))
    def test_membership_exclusion_and_missing_meetings_still_apply(self):
        self.assertEqual(solve(self.problem('CM','CS2115'))['status'],'infeasible')
        p=self.problem('CM','EF3320');p['completed_courses']=['GE1105'];p['options'][0]['exclusive_courses']=['GE1105']
        self.assertEqual(solve(p)['status'],'infeasible')
        p=self.problem('CM','EF3320');p['options'][0]['timetable_verified']=False
        self.assertEqual(solve(p)['status'],'infeasible')
    def test_source_prerequisite_facts_unchanged(self):
        from course_relations import check_rules
        self.assertFalse(check_rules('EF3320',[])['known_prerequisites_satisfied'])
        self.assertEqual(target({'programme':'CM','completed_courses':[]},'EF3320')['additional_missing_prerequisite_penalty'],0)
    def test_finance_evidence_grades_and_self_report(self):
        self.assertEqual(finance_background({'completed_courses':['GE2260']})['level'],'introductory')
        self.assertEqual(finance_background({'completed_courses':['EF3320']})['level'],'advanced')
        self.assertEqual(finance_background({'completed_courses':[],'finance_background':{'studied':True}})['level'],'introductory')
        for grade in ['F','IP','W']:
            p={'completed_courses':['GE2260'],'GE_history':[{'course_code':'GE2260','grade':grade}]}
            self.assertEqual(finance_background(p)['level'],'none')
    def test_finance_background_changes_score_not_formal_prerequisite(self):
        c={'course_code':'EF3320','completion_alternatives':[['CB3410']],'sections':[]}
        p={'programme':'CM','completed_courses':[]};q={**p,'completed_courses':['GE2260']}
        a=course_scores(p,c);b=course_scores(q,c)
        self.assertEqual(a['difficulty'],b['difficulty']);self.assertEqual(a['workload'],b['workload'])
        self.assertAlmostEqual(a['background_mismatch']-b['background_mismatch'],.30)
        # Merely editing the prerequisite list adds no score penalty in waived CM mode.
        self.assertEqual(a,course_scores(p,{**c,'completion_alternatives':[['CB3410','FB3410','MISSING1001']]}))
    def test_finance_path_expands_without_forbidden_EF_bridges(self):
        p={'programme':'CM','completed_courses':['MA1301','MA2503','MA2510','GE2260'],'desired_stream':'finance'}
        r=plan_stream(p)
        self.assertEqual(r['path']['status'],'academic_path_assuming_CM_prerequisite_waiver')
        self.assertTrue(r['path']['stream_complete_if_all_passed'])
        self.assertFalse(set(r['path']['remaining_courses'])&{'CB3410','FB3410','EF4820'})
        self.assertFalse(r['declaration_or_graduation_verified'])
    def test_explicit_stream_beats_finance_background(self):
        p={'programme':'CM','completed_courses':['GE1202'],'desired_stream':'Enriched Mathematics'}
        self.assertEqual(recommend(p)['selected_stream'],'Enriched Mathematics')
        self.assertEqual(recommend({'programme':'CM','completed_courses':[],'finance_background':True})['selected_stream'],'Financial Mathematics')
    def test_model_context_materialises_default_and_uses_background_fields(self):
        import json
        from cm_finance_training import messages
        p={'programme':'CM','completed_courses':['GE2260'],'desired_stream':'Financial Mathematics','year':2}
        q=json.loads(messages(p,'EF3320')[1]['content'])
        self.assertTrue(q['profile']['cm_ef_cs_prerequisite_waiver'])
        self.assertNotIn('desired_stream',q['profile'])

if __name__=='__main__':unittest.main()
