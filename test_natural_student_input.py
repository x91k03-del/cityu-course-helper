import copy,unittest
from natural_language_training import canonical,validate,validate_profile
from natural_student_input import render,source_titles

class NaturalInputTests(unittest.TestCase):
    def setUp(self):
        self.profile={'programme':'CM','year':2,'semester':None,'cohort':None,'desired_stream':None,
          'transcript':[{'course_code':'MA2510','grade':'P'},{'course_code':'GE2260','grade':'F'}],
          'target':'CS4487','request':'preparation'}
        self.text='I am a Year 2 CM student. MA2510: P, GE2260: F. How ready am I for CS4487?'

    def test_p_counts_as_pass_and_failure_does_not(self):
        result=validate(canonical(self.profile),self.text)
        self.assertEqual(result['completed_courses'],['MA2510'])
        self.assertEqual(result['preparation_bonus'],.25)

    def test_unmentioned_transcript_course_is_rejected(self):
        p=copy.deepcopy(self.profile);p['transcript'].append({'course_code':'MA3515','grade':'A'})
        with self.assertRaisesRegex(ValueError,'Unmentioned'):validate(canonical(p),self.text)

    def test_model_cannot_set_a_preparation_reward_inconsistent_with_passes(self):
        result=canonical(self.profile);result['preparation_bonus']=.35
        with self.assertRaises(ValueError):validate(result,self.text)

    def test_deployed_profile_interface_delegates_arithmetic_to_external_code(self):
        proposal=canonical(self.profile);proposal['preparation_bonus']=.35
        checked=validate_profile(proposal,self.text)
        self.assertEqual(checked['preparation_bonus'],.25)
        self.assertEqual(proposal['preparation_bonus'],.35)

    def test_profile_interface_still_rejects_invented_passes(self):
        proposal=canonical(self.profile);proposal['completed_courses'].append('GE2260')
        with self.assertRaises(ValueError):validate_profile(proposal,self.text)

    def test_failed_grade_cannot_be_changed_to_a_pass(self):
        p=copy.deepcopy(self.profile);p['transcript'][1]['grade']='P'
        with self.assertRaisesRegex(ValueError,'explicit input grade'):validate(canonical(p),self.text)

    def test_explicit_failed_course_cannot_be_omitted(self):
        p=copy.deepcopy(self.profile);p['transcript']=p['transcript'][:1]
        with self.assertRaisesRegex(ValueError,'explicit input grade'):validate(canonical(p),self.text)

    def test_entry_cohort_cannot_be_inferred_from_study_year(self):
        p=copy.deepcopy(self.profile);p['cohort']=2025
        with self.assertRaisesRegex(ValueError,'Unmentioned entry cohort'):validate(canonical(p),self.text)

    def test_semester_cannot_be_guessed(self):
        p=copy.deepcopy(self.profile);p['semester']='A'
        with self.assertRaisesRegex(ValueError,'Unmentioned semester'):validate(canonical(p),self.text)

    def test_missing_planning_context_requests_clarification(self):
        p=copy.deepcopy(self.profile);p.update(request='plan',target=None)
        self.assertEqual(canonical(p)['missing_fields'],['semester','cohort'])

    def test_unknown_grade_is_not_a_pass(self):
        p=copy.deepcopy(self.profile);p['transcript'][0]['grade']='UNKNOWN'
        result=canonical(p)
        self.assertEqual(result['completed_courses'],[])
        self.assertIn('grade:MA2510',result['missing_fields'])

    def test_output_does_not_invent_course_titles(self):
        titles=source_titles({'EF3320','MA2510'})
        self.assertEqual(titles['EF3320'],'Security Analysis and Portfolio Management')
        self.assertEqual(titles['MA2510'],'Probability and Statistics')
        output=render(canonical(self.profile),titles)
        self.assertIn('MA2510: P -- Probability and Statistics',output)

if __name__=='__main__':unittest.main()
