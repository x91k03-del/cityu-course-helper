import hashlib,json,unittest
from unittest.mock import patch
from ma_timetable import *

class MATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch('socket.socket',side_effect=AssertionError('Offline PDF import must not use network')):
            cls.courses={p.stem:parse_pdf(p) for p in SOURCE.glob('MA*.pdf')}

    def test_source_coverage(self):
        self.assertEqual(len(self.courses),17)
        self.assertEqual(sum(len(c['sections']) for c in self.courses.values()),16)
        self.assertEqual(sum(len(s['meetings']) for c in self.courses.values() for s in c['sections']),20)
        self.assertTrue(all(c['source_sha256']==hashlib.sha256(Path(c['source_pdf']).read_bytes()).hexdigest() for c in self.courses.values()))

    def test_cm_token_not_substring(self):
        self.assertFalse(is_cm_section([{'mode':'only','field':'major','values':['CRM1','SCM']}]))
        self.assertTrue(is_cm_section([{'mode':'only','field':'major','values':['CFFT','CM']}]))
        self.assertFalse(is_cm_section([{'mode':'only','field':'major','values':['CM']},{'mode':'not','field':'major','values':['CM']}]))

    def test_cm_all_alternatives_preserved_and_room_wrap(self):
        s={s['section']:s for s in self.courses['MA1300']['sections']}
        self.assertEqual(set(s),{'C01','T01','T02'})
        self.assertEqual(s['T02']['meetings'][0]['room'],'B5-211')
        self.assertEqual([(m['day'],m['start_time']) for m in s['C01']['meetings']],[('Fri','12:00'),('Wed','17:00')])
        self.assertFalse(s['C01']['web_registration'])

    def test_other_major_only_not_taught_as_cm(self):
        missing={code for code,c in self.courses.items() if not c['sections']}
        self.assertEqual(missing,{'MA1508','MA2001','MA2158','MA2172','MA2185','MA2510'})
        for c in self.courses.values():
            for s in c['excluded_sections']:self.assertNotIn('meetings',s)
            for s in c['sections']:self.assertTrue(is_cm_section(s['restrictions']))

    def test_cohort_and_programme_retained(self):
        s=self.courses['MA1502']['sections'][0]
        self.assertEqual(s['section'],'CB1')
        self.assertIn({'mode':'only','field':'cohort','raw':'2026','values':['2026']},s['restrictions'])
        self.assertEqual(s['meetings'][0]['day'],'Wed')

    def test_multimeeting_date_ranges_and_tutorial(self):
        s={s['section']:s for s in self.courses['MA2508']['sections']}
        self.assertEqual(set(s),{'CA1','TA1'})
        self.assertEqual([(m['day'],m['start_time'],m['end_time']) for m in s['CA1']['meetings']],
                         [('Sat','11:00','12:50'),('Tue','16:00','16:50')])
        self.assertEqual(s['CA1']['meetings'][0]['end_date'],'2026-12-05')
        self.assertEqual(s['TA1']['meetings'][0]['end_date'],'2026-11-28')
        self.assertFalse(s['TA1']['component_linking_verified'])

    def test_nested_rule_logic(self):
        self.assertEqual(alternatives(parse_rule('MA1201 or MA1301 or (MA1503 and MA1508)')),
                         [['MA1201'],['MA1301'],['MA1503','MA1508']])
        self.assertEqual(alternatives(parse_rule('MA2508 and (MA3526 or MA3524)')),
                         [['MA2508','MA3526'],['MA2508','MA3524']])
        for code in ['MA2508','MA2510','MA4542']:
            self.assertEqual(alternatives(self.courses[code]['requirement_expression']),self.courses[code]['completion_alternatives'])

    def test_unknown_rule_syntax_rejected(self):
        for text in ['MA1201 or','(MA1201','MA1201 grade C','MA1201 MA1301','MA1201 or Nil']:
            with self.assertRaises(ValueError):parse_rule(text)
        self.assertEqual(alternatives(parse_rule('Nil')),[[]])

    def test_missing_conjunct_and_exclusive_conflict(self):
        self.assertFalse(check('MA2508',['MA1503'])['requirement_expression_satisfied'])
        self.assertTrue(check('MA2508',['MA1503','MA1508'])['requirement_expression_satisfied'])
        self.assertFalse(check('MA4542',['MA3526'])['requirement_expression_satisfied'])
        self.assertTrue(check('MA4542',['MA2508','MA3524'])['requirement_expression_satisfied'])
        self.assertEqual(check('MA2508',['MA1201','MA1502'])['exclusive_course_conflicts'],['MA1502'])

    def test_unknown_completion_not_empty(self):
        self.assertIsNone(check('MA2508')['requirement_expression_satisfied'])
        self.assertFalse(check('MA2508',[])['requirement_expression_satisfied'])
        self.assertTrue(check('MA1502')['requirement_expression_satisfied'])
        self.assertIsNone(check('MA1502')['exclusive_course_conflicts'])
        self.assertTrue(check('MA1502',[])['requirement_expression_satisfied'])

    def test_major_does_not_override_cohort_programme(self):
        x=check('MA1502',[],section='CB1',programme='BSCSIU4',cohort='2025')
        self.assertFalse(x['section_checks'][0]['encoded_conditions_satisfied'])
        x=check('MA1502',[],section='CB1',programme='BSCSIU4',cohort='2026')
        self.assertTrue(x['section_checks'][0]['encoded_conditions_satisfied'])
        self.assertFalse(x['eligibility_verified'])
        self.assertIsNone(check('MA1502',[])['section_checks'][0]['encoded_conditions_satisfied'])

    def test_training_schedule_targets_are_only_selected(self):
        allowed={(c['course_code'],s['section']) for c in self.courses.values() for s in c['sections']}
        for split in ['train','validation','test']:
            for line in (DATA/(split+'.jsonl')).read_text(encoding='utf-8').splitlines():
                row=json.loads(line)
                if row['task'] in ['schedule_recall','grounded_schedule']:
                    target=json.loads(row['messages'][-1]['content'])
                    self.assertIn((target['course_code'],target['section']),allowed)
                    self.assertFalse(target['eligibility_verified'])

    def test_question_route_term_guard_and_section_filter(self):
        self.assertNotIn('sections',answer_question('When does MA2508 meet in Semester B 2026/27?'))
        self.assertNotIn('sections',answer_question('MA2508 timetable for 2025-26'))
        self.assertNotIn('sections',answer_question('MA2508 term 202709 timetable'))
        x=answer_question('When does MA1300 section T02 meet in 2026/27 Sem A?')
        self.assertEqual([s['section'] for s in x['sections']],['T02'])
        self.assertFalse(x['model_generated'])
        self.assertTrue(check('MA1300',[],section='CA1')['requested_section_not_found'])

if __name__=='__main__':unittest.main(verbosity=2)
