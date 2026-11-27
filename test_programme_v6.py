import unittest,json,itertools
from pathlib import Path
from programme_policy import *
from scheduler import solve
from test_scheduler import option
class ProgrammeTests(unittest.TestCase):
    def test_membership_is_programme_specific(self):
        self.assertFalse(allowed('CM','CS2115'));self.assertTrue(allowed('CS','CS2115'))
        self.assertTrue(allowed('CM','MA4542'));self.assertFalse(allowed('CS','MA4542'))
        self.assertTrue(allowed('CM','GE1105'));self.assertFalse(allowed('CS','GE9999'))
    def test_block_forbidden_option_even_required(self):
        p={'programme':'CM','student_year':4,'term':'DEMO','completed_courses':[],'required_courses':['CS2115'],
          'course_min':1,'course_max':1,'credit_min':3,'credit_max':3,'options':[option('CS2115')]}
        self.assertEqual(solve(p)['status'],'infeasible')
    def test_stream_chain_completion_and_no_repeat(self):
        s='Data Science';done=['CS3481','CS4480']
        self.assertEqual(chain_reward('CS',done,s,['CS4487']),8)
        self.assertEqual(chain_reward('CS',done+['CS4487'],s,['CS4487']),0)
        self.assertEqual(chain_reward('CS',done,s,['CS4293']),0)
    def test_AI_core_cannot_double_count(self):
        self.assertEqual(stream_result('CS',['CS4487'],'Artificial Intelligence')['completed_slots'],1)
        self.assertFalse(stream_result('CS',['CS4487','CS4486'],'Artificial Intelligence')['stream_complete'])
        self.assertTrue(stream_result('CS',['CS4487','CS4486','CS3383'],'Artificial Intelligence')['stream_complete'])
    def test_CM_choose_one_not_all(self):
        done=['MA3523','MA4542','MA4545'];s='Enriched Mathematics'
        self.assertEqual(chain_reward('CM',done,s,['MA4528','MA4546']),8)
    def test_stream_MILP_matches_enumeration(self):
        codes=['CS3346','CS3356','CS4348','CS4389'];opts=[option(c,day=i+1) for i,c in enumerate(codes)]
        p={'programme':'CS','selected_stream':'Software Engineering and Project Management','student_year':4,'term':'DEMO',
           'required_courses':[],'completed_courses':[],'course_min':0,'course_max':4,'credit_min':0,'credit_max':12,'options':opts}
        result=solve(p)
        from profit_objective import components,settings
        expected=max(components(list(g),{},0,{'background_mismatch':1,'difficulty':1,'workload':1},settings(p))['net_profit']+
          chain_reward('CS',[],p['selected_stream'],[o['course_code'] for o in g]) for n in range(5) for g in itertools.combinations(opts,n))
        self.assertAlmostEqual(result['objective'],expected)
    def test_terms_and_major_restrictions_preserved(self):
        from ma_timetable import is_cm_section
        courses=json.loads((ROOT/'data/programme-v6/courses.json').read_text())
        for c in courses:
            self.assertIn(c['term_code'],['202609','202702'])
            for s in c['sections']:
                self.assertEqual(s['term_code'],c['term_code']);self.assertTrue(allowed(c['programme'],c['course_code']))
                if c['programme']=='CM':self.assertTrue(is_cm_section(s['restrictions']))
                for m in s['meetings']:self.assertTrue(m['start_date'].startswith('2027' if c['term_code']=='202702' else '2026'))
    def test_split_IDs_disjoint(self):
        sets=[{json.loads(x)['id'] for x in (ROOT/f'data/programme-v6/{s}.jsonl').read_text(encoding='utf-8').splitlines()} for s in ['train','validation','test']]
        for a,b in itertools.combinations(sets,2):self.assertFalse(a&b)
    def test_CM_mock_uses_document_courses_and_completes_one_stream(self):
        path=ROOT/'reports/programme-v6/CM_four_year_mock.json'
        if not path.exists():self.skipTest('Generate semester examples first')
        run=json.loads(path.read_text(encoding='utf-8'))
        self.assertTrue(all(allowed('CM',r['id']) for r in run['transcript']))
        self.assertTrue(run['audit']['all_encoded_requirements_met'])
        self.assertEqual(sum(s['profit']['stream_chain_bonus'] for s in run['steps']),14)
    def test_rule_tree_both_conditions_needed(self):
        from programme_v6 import lookup
        c=lookup('CM','202702','MA3511')
        self.assertIn(['MA2503','MA2508'],c['completion_alternatives'])
        self.assertIn(['MA2001'],c['completion_alternatives'])
    def test_snapshot_plan_succeeds_only_with_explicit_hypothetical_mode(self):
        from programme_v6 import plan
        profile={'programme':'CS','programme_code':'BSCCCU4','cohort':2025,'year':2,'term':'202702',
          'completed_courses':['CS1302A','CS2115','CS2310','CS2312','CS2402'],'selected_stream':'Data Science'}
        unbundled=plan(profile)
        self.assertEqual(unbundled['course_count'],0)
        self.assertFalse(unbundled['hypothetical_component_linkage'])
        result=plan(profile,True);self.assertEqual(result['status'],'optimal')
        self.assertFalse(result['official_registration_verified'])
        self.assertTrue(all(allowed('CS',c) for c in result['course_codes']))
    def test_new_audit_catches_foreign_free_elective(self):
        from four_year_markov import audit
        old=json.loads((ROOT/'reports/preparation-v5/model_rollouts.json').read_text(encoding='utf-8'))[0]
        self.assertFalse(audit(old['transcript'])['checks']['programme_document_membership'])
if __name__=='__main__':unittest.main()
