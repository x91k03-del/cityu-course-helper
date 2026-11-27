"""Independent checks that the scenario grader rejects plausible but wrong plans."""
import copy,json,unittest
from test_cm_profiles import completed,make_profiles,reference,grade

class GraderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p={p['profile_id']:p for p in make_profiles()}
    def answer(self,pid):
        p=self.p[pid];r=reference(p)
        return {'profile_id':pid,'completed_courses':completed(p),
                'selected_options':[{k:o[k] for k in ['course_code','class_section','tutorial_section','meetings']} for o in r['selected_options']],
                'needs_confirmation':True,'feasibility_verified':False}
    def test_reference_answers_pass(self):
        for pid in self.p:self.assertTrue(grade(self.p[pid],json.dumps(self.answer(pid)))['all_checks_passed'],pid)
    def test_matched_analysis_pair(self):
        a=reference(self.p['CM01']);b=reference(self.p['CM02'])
        self.assertIn('MA4542',a['available_course_codes']);self.assertNotIn('MA4542',b['available_course_codes'])
        for pid in ['CM03','CM04','CM05']:self.assertNotIn('MA4542',reference(self.p[pid])['available_course_codes'])
        self.assertEqual(self.p['CM01']['transcript'][:-1],self.p['CM02']['transcript'])
    def test_failed_and_ip_not_completed(self):
        for pid in ['CM03','CM04']:self.assertNotIn('MA3526',completed(self.p[pid]))
    def test_illegal_analysis_selection_rejected(self):
        answer=self.answer('CM01');answer['profile_id']='CM02';answer['completed_courses']=completed(self.p['CM02'])
        result=grade(self.p['CM02'],json.dumps(answer))
        self.assertFalse(result['selection_rules_passed'])
        self.assertTrue(any('combined_requirement_not_satisfied' in e for e in result['errors']))
    def test_fabricated_time_rejected(self):
        answer=self.answer('CM01');answer['selected_options'][0]['meetings'][0]['start_time']='03:00'
        self.assertFalse(grade(self.p['CM01'],json.dumps(answer))['meeting_times_exact'])
    def test_missing_tutorial_rejected(self):
        answer=self.answer('CM02');target=next(o for o in answer['selected_options'] if o['tutorial_section'])
        target['tutorial_section']=None
        self.assertFalse(grade(self.p['CM02'],json.dumps(answer))['selection_rules_passed'])
    def test_claimed_feasibility_rejected(self):
        answer=self.answer('CM01');answer['feasibility_verified']=True
        self.assertFalse(grade(self.p['CM01'],json.dumps(answer))['all_checks_passed'])
    def test_empty_schedule_does_not_pass_optimization(self):
        answer=self.answer('CM01');answer['selected_options']=[]
        self.assertFalse(grade(self.p['CM01'],json.dumps(answer))['maximum_course_count_met'])
    def test_malformed_options_do_not_crash(self):
        for bad in [None,[1],[{'course_code':{}}],[{'course_code':['MA4542']}]]:
            answer=self.answer('CM01');answer['selected_options']=bad
            self.assertFalse(grade(self.p['CM01'],json.dumps(answer))['all_checks_passed'])
    def test_and_exclusion_and_cohort_controls(self):
        self.assertIn('MA2508',reference(self.p['CM08'])['available_course_codes'])
        for pid in ['CM09','CM12']:self.assertNotIn('MA2508',reference(self.p[pid])['available_course_codes'])
        self.assertIn('MA1502',reference(self.p['CM10'])['available_course_codes'])
        self.assertNotIn('MA1502',reference(self.p['CM11'])['available_course_codes'])

if __name__=='__main__':unittest.main(verbosity=2)
