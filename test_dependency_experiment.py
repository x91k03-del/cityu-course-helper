import json,unittest
from dependency_experiment import OUT
class DependencyExperimentTests(unittest.TestCase):
    def test_predeclared_pair_effects_and_component_sum(self):
        rows=json.loads((OUT/'paired_results.json').read_text(encoding='utf-8'));self.assertEqual(len(rows),12)
        for r in rows:
            self.assertAlmostEqual(r['observed_delta'],r['expected_delta_predeclared'])
            delta=r['component_deltas'];self.assertAlmostEqual(sum(v for k,v in delta.items() if k!='fixed_cost_penalty')-delta['fixed_cost_penalty'],r['observed_delta'])
    def test_unlock_and_reward_are_separate(self):
        r=next(r for r in json.loads((OUT/'paired_results.json').read_text(encoding='utf-8')) if r['id']=='D06')
        self.assertIsNone(r['before']['usable_marginal_utility']);self.assertIsNotNone(r['after']['usable_marginal_utility'])
        self.assertEqual(r['observed_delta'],0)
    def test_interaction_and_grades(self):
        f=json.loads((OUT/'factorial.json').read_text(encoding='utf-8'));self.assertEqual(f['reward_interaction'],6.)
        grades=json.loads((OUT/'grade_controls.json').read_text(encoding='utf-8'))
        self.assertEqual([g['result']['components']['preparation_bonus'] for g in grades],[.15,0,0,0])
    def test_unchanged_scores_and_costs(self):
        for r in json.loads((OUT/'paired_results.json').read_text(encoding='utf-8')):
            self.assertEqual(r['before']['components']['fixed_cost_penalty'],r['after']['components']['fixed_cost_penalty'])
if __name__=='__main__':unittest.main()
