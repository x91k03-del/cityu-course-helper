import json,unittest
from cm_planning_update import *

class PlanningUpdateTests(unittest.TestCase):
    def test_reference_respects_minimum_and_grades(self):
        for split in ['train','validation','test']:
            for p in read(DATA/(split+'_profiles.json')):
                r=reference(p)
                self.assertTrue(grade_plan(p,r)['passed'],p['profile_id'])
                self.assertTrue(r['status']=='infeasible' or 5<=len(r['selected_options'])<=6)
    def test_holdout_groups_are_disjoint(self):
        groups={s:{group_key(p) for p in read(DATA/(s+'_profiles.json'))} for s in ['train','validation','test']}
        old={group_key(p) for p in make_profiles()}
        self.assertFalse(groups['train']&groups['test']);self.assertFalse(groups['validation']&groups['test'])
        self.assertFalse(groups['train']&groups['validation'])
        self.assertFalse(old&(groups['validation']|groups['test']))
    def test_historical_wrong_answers_are_only_negative_inputs(self):
        rs=[json.loads(x) for x in (DATA/'train.jsonl').read_text(encoding='utf-8').splitlines()]
        corrections=[r for r in rs if r['task']=='failure_correction'];self.assertEqual(len(corrections),10)
        for r in corrections:
            user=json.loads(r['messages'][-2]['content']);target=json.loads(r['messages'][-1]['content'])
            self.assertIn('incorrect_previous_answer',user);self.assertIs(target['valid'],False)
            self.assertIn('requires_at_least_five_courses_under_updated_policy',target['errors'])
    def test_three_course_output_cannot_pass(self):
        p=next(p for p in read(DATA/'test_profiles.json') if reference(p)['status']=='candidate')
        r=reference(p);r['selected_options']=r['selected_options'][:3]
        self.assertFalse(grade_plan(p,r)['passed'])
    def test_infeasible_is_not_empty_success(self):
        p=next(p for p in read(DATA/'test_profiles.json') if reference(p)['status']=='candidate')
        r=reference(p);r.update(status='infeasible',selected_options=[])
        self.assertIn('false_infeasibility',grade_plan(p,r)['errors'])
    def test_duplicate_courses_cannot_satisfy_five(self):
        p=next(p for p in read(DATA/'test_profiles.json') if reference(p)['status']=='candidate')
        r=reference(p);r['selected_options']=[r['selected_options'][0]]*5
        self.assertFalse(grade_plan(p,r)['passed'])

if __name__=='__main__':unittest.main(verbosity=2)
