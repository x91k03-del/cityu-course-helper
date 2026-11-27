import copy,hashlib,json,unittest
from pathlib import Path
from degree_chain import terminal_audit
from markov_planner import Rules
from programme_policy import allowed
from timetable_grounded_training import problem_for
ROOT=Path(__file__).resolve().parent

class Curriculum122Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs=[json.loads((ROOT/'reports/curriculum-122-fix'/f'{name}_rollout.json').read_text()) for name in ('F','N','M')]
    def test_all_three_paths_reach_122_and_every_encoded_requirement(self):
        for r in self.runs:
            with self.subTest(stream=r['input_profile']['desired_stream']):
                a=terminal_audit(r['input_profile'],r['transcript'])
                self.assertTrue(a['all_encoded_requirements_met']);self.assertEqual(a['earned_credits'],122)
                self.assertEqual(sum(x['credits'] for x in r['transcript']),122)
                self.assertEqual(len({x['id'] for x in r['transcript']}),len(r['transcript']))
    def test_no_passes_invented_in_historical_input(self):
        for r in self.runs:
            self.assertEqual(r['historical_transcript'],r['input_profile']['historical_transcript'])
            self.assertEqual(r['transcript'][:len(r['historical_transcript'])],r['historical_transcript'])
            self.assertTrue(all(sum(x['credits'] for x in r['historical_transcript'] if x['term']==t)==15 for t in (1,2)))
    def test_semester_capacity_and_final_semester_are_not_empty(self):
        for r in self.runs:
            self.assertGreater(r['semesters'][-1]['credits'],0)
            for s in r['semesters']:
                self.assertLessEqual(s['credits'],18)
                self.assertLessEqual(sum(o['credits']>0 for o in s['course_evidence']),6)
                self.assertAlmostEqual(s['reward']['overload_penalty'],.25*max(0,s['credits']-(12 if s['year']==4 else 15))**2)
    def test_pending_never_contains_invented_meetings(self):
        for r in self.runs:
            self.assertTrue(r['curriculum_credit_plan_complete']);self.assertFalse(r['registration_timetable_complete'])
            for o in r['pending_courses']:
                self.assertIsNone(o['meetings']);self.assertIsNone(o['crn']);self.assertIsNone(o['option_id'])
                self.assertFalse(o['course_offering_verified']);self.assertTrue(Path(o['curriculum_source']).is_file())
                self.assertTrue(allowed('CM',o['course_code']) or o['course_code']=='GE1601')
            for path,digest in r['curriculum_source_sha256'].items():self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(),digest)
    def test_confirmed_sections_still_pass_independent_timetable_gate(self):
        for r in self.runs:
            done=[x['id'] for x in r['historical_transcript']]
            for s in r['semesters']:
                p={**r['input_profile'],'year':s['year'],'term':'202609' if s['term']%2 else '202702','completed_courses':done}
                q=problem_for(p);byid={o['option_id']:o for o in q['options']}
                confirmed=[o for o in s['course_evidence'] if o['evidence_status']=='saved_timetable_hypothetical_bundle']
                selected=[byid[o['option_id']] for o in confirmed]
                self.assertFalse(Rules(q).violations(selected))
                done=done+s['selected_courses']
    def test_removing_required_credit_cannot_be_compensated_by_reward(self):
        for r in self.runs:
            t=[x for x in r['transcript'] if x['id']!='MA4530:B']
            a=terminal_audit(r['input_profile'],t)
            self.assertFalse(a['all_encoded_requirements_met']);self.assertEqual(a['earned_credits'],119)
            self.assertFalse(a['checks']['credit_minimum']);self.assertFalse(a['checks']['capstone_six_credits'])
    def test_mode_requires_explicit_permission(self):
        from curriculum_chain import plan
        with self.assertRaises(ValueError):plan({'degree_mode':'saved_timetable_only'})
    def test_new_math_obeys_current_prerequisites_and_A_B_offering_pattern(self):
        evidence=json.loads((ROOT/'data/curriculum-pending-evidence.json').read_text())
        for r in self.runs:
            done={x['id'] for x in r['historical_transcript']}
            for s in r['semesters']:
                for o in s['course_evidence']:
                    code=o['course_code'].split(':')[0]
                    self.assertNotIn(code,evidence['not_offered_current_year'])
                    rule=evidence['courses'].get(code)
                    if rule:
                        self.assertIn(s['semester'],rule['semesters'])
                        self.assertTrue(any(set(a)<=done for a in rule['completion_alternatives']))
                done.update(s['selected_courses'])

if __name__=='__main__':unittest.main()
