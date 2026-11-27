import copy,json,unittest
from unittest.mock import patch
import transcript_parameter_pipeline as p

class TranscriptParameterPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=json.loads((p.OUT/'cases.json').read_text())

    def test_pdf_parser_matches_fictional_history_and_credit_total(self):
        for case in self.cases:
            facts=p.parse_transcript(p.extract_pdf(case['pdf']))
            self.assertEqual(facts['confirmed_earned_degree_credits'],30)
            positive={r['course_code'] for r in facts['rows'] if r['passed'] and r['earned_degree_credits']}
            self.assertEqual(positive,{r['id'] for r in case['source_profile']['historical_transcript']})

    def test_zero_credit_pass_and_in_progress_are_distinct(self):
        facts=self.cases[0]['facts']
        self.assertIn('CSCI1001',facts['completed_courses'])
        self.assertNotIn('MA2503',facts['completed_courses'])
        self.assertEqual(facts['in_progress_courses'],['MA2503'])

    def test_asterisk_alone_does_not_decide_degree_credit(self):
        text=self.cases[0]['text'].replace('Non-degree','Unspecified')
        facts=p.parse_transcript(text)
        self.assertIn('LC0200A',facts['unresolved_degree_credit_rows'])

    def test_model_cannot_return_a_student_profile_or_timetable(self):
        for key in ['student_profile','selected_courses','selected_option_ids','timetable','assignments','semester_courses']:
            value=p.parameter_target();value[key]=[]
            with self.assertRaises(ValueError):p.validate_parameters(value)

    def test_model_cannot_change_the_graduation_credit_requirement(self):
        value=p.parameter_target();value['reward_parameters']['minimum_degree_credits']=0
        with self.assertRaises(ValueError):p.validate_parameters(value)

    def test_course_relation_values_and_explicit_weights_are_checked(self):
        value=p.parameter_target();value['course_relations'][0]['benefit']=.9
        with self.assertRaises(ValueError):p.validate_parameters(value)
        value=p.parameter_target();value['penalty_weights']['workload']=float('nan')
        with self.assertRaises(ValueError):p.validate_parameters(value)
        value=p.parameter_target();value['penalty_weights']['workload']=2
        with self.assertRaises(ValueError):p.validate_parameters(value,p.parameter_target())

    def test_transcript_mode_has_only_a_user_turn(self):
        c=self.cases[0];messages=p.model_messages(c['text'],c['preferences'])
        self.assertEqual([m['role'] for m in messages],['user'])
        self.assertNotIn('configured_objective_policy',messages[0]['content'])

    def test_external_exact_optimizer_has_a_maximum_certificate(self):
        result=json.loads((p.OUT/'optimizer_control_F.json').read_text(encoding='utf-8'))
        self.assertTrue(result['audit']['all_encoded_requirements_met'])
        self.assertEqual(result['audit']['earned_credits'],122)
        self.assertFalse(result['pipeline_provenance']['LLM_selected_courses'])
        cert=result['completion_optimality_certificate']
        self.assertTrue(cert['optimality_proven']);self.assertEqual(cert['assignments_checked'],64)
        self.assertEqual(cert['optimality_gap'],0)

    def test_relation_array_order_does_not_change_parameters(self):
        expected=p.parameter_target();value=copy.deepcopy(expected)
        value['course_relations'].reverse();p.validate_parameters(value,expected)
        self.assertEqual(p.parameter_signature(value),p.parameter_signature(expected))

    def test_markov_objective_uses_the_supplied_relation_packet(self):
        from markov_planner import solve
        from test_scheduler import option
        problem={'student_year':2,'term':'DEMO','required_courses':[],'completed_courses':['MA2508'],
          'credit_min':0,'credit_max':18,'options':[option('MA3515')],'reward_course_relations':[]}
        empty=solve(problem)
        problem['reward_course_relations']=[{'source':'MA2508','target':'MA3515','benefit':.2}]
        linked=solve(problem)
        self.assertAlmostEqual(linked['objective']-empty['objective'],.2)

    def test_solver_invocation_does_not_call_a_language_model_or_milp(self):
        # Parameter generation ends before the external planning tool is invoked.
        c=self.cases[0]
        with patch('inference.generate',side_effect=AssertionError('Optimizer must not call Qwen')),patch('scheduler.solve',side_effect=AssertionError('MILP must not be called')):
            result=p.optimise_case(c,c['expected_parameters'])
        self.assertTrue(result['audit']['all_encoded_requirements_met'])

if __name__=='__main__':unittest.main()
