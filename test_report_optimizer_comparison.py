import copy,json,unittest
from pathlib import Path
from curriculum_chain import plan
ROOT=Path(__file__).resolve().parent

class ComparisonTests(unittest.TestCase):
    def test_blind_GPT_answers_are_not_repaired_and_all_final_scores_match(self):
        rows=json.loads((ROOT/'reports/report-optimizer-comparison/comparison.json').read_text())
        self.assertEqual(len(rows),3)
        for r in rows:
            self.assertFalse(r['gpt_repaired']);self.assertFalse(r['gpt_evaluation']['optimizer_called'])
            self.assertFalse(r['gpt_evaluation']['proposal_repaired']);self.assertTrue(r['gpt_evaluation']['proposal_valid'])
            self.assertEqual(r['gpt_evaluation']['audit']['earned_credits'],122)
            self.assertAlmostEqual(r['reward_gap'],0)
    def test_evaluator_rejects_wrong_term_without_repair_or_search(self):
        out=ROOT/'reports/llm-reward-external-search'
        p=json.loads((out/'F_profile.json').read_text());base=json.loads((ROOT/'reports/ef-late-ge-examples/F_rollout.json').read_text())
        p['evaluate_completion_proposal']={'MA4528':8,'MA4529':6,'MA4537':6,'MA4546':8,'MA4550':8,'MA4551':8}
        r=plan(p,base);self.assertFalse(r['proposal_valid']);self.assertFalse(r['optimizer_called'])
        self.assertIn('Wrong offering term: MA4528',r['violations'])
    def test_common_critic_scores_optimizer_assignment_identically(self):
        out=ROOT/'reports/llm-reward-external-search'
        for n in ('F','N','M'):
            original=json.loads((out/f'{n}_exact.json').read_text());p=copy.deepcopy(original['input_profile'])
            codes=['MA4528','MA4529','MA4537','MA4546','MA4550','MA4551']
            p['evaluate_completion_proposal']={c:next(s['term'] for s in original['semesters'] if c in s['selected_courses']) for c in codes}
            base=json.loads((ROOT/f'reports/ef-late-ge-examples/{n}_rollout.json').read_text())
            r=plan(p,base);self.assertTrue(r['proposal_valid']);self.assertFalse(r['optimizer_called'])
            self.assertAlmostEqual(r['discounted_academic_reward'],original['discounted_academic_reward'])

if __name__=='__main__':unittest.main()
