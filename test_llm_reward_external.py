import copy,json,math,unittest
from pathlib import Path
from llm_reward_contract import validate,teacher_packet,apply
from profit_objective import settings,option_ge_progress,option_preparation
ROOT=Path(__file__).resolve().parent

class RewardOnlyTests(unittest.TestCase):
    def test_LLM_cannot_supply_paths_or_change_hard_constraints(self):
        p=teacher_packet();p['selected_courses']=['EF3320']
        with self.assertRaises(ValueError):validate(p)
        p=teacher_packet();p['reward_parameters']['minimum_degree_credits']=0
        with self.assertRaises(ValueError):validate(p)
    def test_numeric_and_relation_guards(self):
        for bad in [float('nan'),float('inf'),True,-1]:
            p=teacher_packet();p['reward_parameters']['base_course_profit']=bad
            with self.assertRaises(ValueError):validate(p)
        p=teacher_packet();p['course_relations'][0]['benefit']=.36
        with self.assertRaises(ValueError):validate(p)
        p=teacher_packet();p['course_relations'][0]['target']=p['course_relations'][0]['source']
        with self.assertRaises(ValueError):validate(p)
    def test_actual_Qwen_output_is_reward_only(self):
        p=json.loads((ROOT/'reports/llm-reward-external-search/qwen_parameters.json').read_text())
        self.assertTrue(p['accepted']);self.assertFalse(p['LLM_generated_path'])
        self.assertEqual(validate(json.loads(p['raw_model_response']),p['teacher_packet']),p['validated_parameters'])
    def test_external_DP_maximum_is_independently_certified(self):
        for name in ('F','N','M'):
            r=json.loads((ROOT/f'reports/llm-reward-external-search/{name}_exact.json').read_text())
            self.assertTrue(r['audit']['all_encoded_requirements_met']);self.assertEqual(r['audit']['earned_credits'],122)
            c=r['completion_optimality_certificate'];self.assertTrue(c['optimality_proven'])
            self.assertEqual(c['assignments_checked'],64);self.assertEqual(c['optimality_gap'],0)
            self.assertAlmostEqual(c['objective_upper_bound'],r['discounted_academic_reward'])
            self.assertFalse(r['global_optimality_claimed']);self.assertFalse(r['registration_timetable_complete'])
    def test_parameter_values_reach_numeric_critic(self):
        p={'student_year':2,'track_ge_graduation':True,'new_GE_area_bonus':8,'GE_count_progress_bonus':1}
        self.assertEqual(option_ge_progress({'ge_area':1},settings(p)),9)
        self.assertEqual(option_preparation({'course_code':'EF3320'},{'preparation_bonus_by_course':{'EF3320':.12}}),.12)
    def test_empty_relation_packet_does_not_reuse_another_active_graph(self):
        p=teacher_packet();p['course_relations']=[];r=apply({'historical_transcript':[]},p)
        self.assertEqual(r['reward_course_relations'],[]);self.assertEqual(r['path_selection_role'],'external_dynamic_programming')
    def test_numeric_penalty_change_changes_external_path(self):
        directory=ROOT/'reports/llm-reward-external-search'
        before=json.loads((directory/'F_exact.json').read_text());after=json.loads((directory/'F_low_year4_penalty.json').read_text())
        self.assertEqual(before['audit']['earned_credits'],after['audit']['earned_credits'])
        old={s['term']:s['credits'] for s in before['semesters']};new={s['term']:s['credits'] for s in after['semesters']}
        self.assertEqual(old[6],18);self.assertEqual(new[6],15)
        self.assertEqual(old[8],15);self.assertEqual(new[8],18)

if __name__=='__main__':unittest.main()
