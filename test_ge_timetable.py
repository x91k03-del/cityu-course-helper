"""Checks against known captured sections and missing-data boundary cases."""
import copy,json,unittest
from pathlib import Path
from ge_timetable import ROOT,DATA,REPORT,read,lookup,weekly_overlap,html_rows,codes_from_pdfs

class TimetableTests(unittest.TestCase):
    def test_coverage(self):
        sections=read(DATA/'sections.json')
        self.assertEqual({s['course_code'] for s in sections},codes_from_pdfs())
        self.assertEqual(len(read(DATA/'meeting_rows.json')),290)
        self.assertEqual(len(sections),287)
    def test_known_meeting(self):
        s=lookup('GE1356')['sections'][0]
        self.assertEqual(s['meetings'],[{'day':'Mon','start_time':'12:00','end_time':'14:50','building':'LI','room':'3505'}])
    def test_sample_summer_not_sema(self):
        self.assertEqual(html_rows(ROOT/'GE_SEMA/sampleGE/GE1101.html')['rows'],[])
        self.assertTrue(lookup('GE1101')['not_found'])
    def test_missing_does_not_mean_free(self):
        s=lookup('GE1601','14217C17')['sections'][0]
        self.assertIsNone(s['meetings'][0]['day'])
        self.assertIsNone(weekly_overlap(s,lookup('GE1356')['sections'][0])['weekly_overlap'])
    def test_multiple_room_records_preserved(self):
        s=lookup('GE1128')['sections'][0]
        self.assertEqual(len(s['meetings']),2)
        self.assertEqual({m['building'] for m in s['meetings']},{'CMC','LAU'})
    def test_known_overlap(self):
        a=lookup('GE1105')['sections'][0];b=lookup('GE1205','10598S02')['sections'][0]
        self.assertIs(weekly_overlap(a,b)['weekly_overlap'],True)
        self.assertIsNone(weekly_overlap(a,b)['calendar_conflict_confirmed'])
    def test_boundary_and_distinct_days(self):
        a=lookup('GE1356')['sections'][0];b=copy.deepcopy(a)
        b['meetings'][0].update(start_time='14:50',end_time='15:30')
        self.assertIs(weekly_overlap(a,b)['weekly_overlap'],False)
        b['meetings'][0].update(day='Tue',start_time='12:00')
        self.assertIs(weekly_overlap(a,b)['weekly_overlap'],False)
    def test_capacity_and_component_safety(self):
        sections=read(DATA/'sections.json')
        self.assertTrue(any(s['capacity']==0 for s in sections))
        self.assertTrue(all(s['component_linking_verified'] is False and s['eligibility_verified'] is False for s in sections))
        self.assertTrue(all(s['calendar_dates'] is None and s['teaching_weeks'] is None for s in sections))

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TimetableTests))
    (REPORT/'parser_tests.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)},indent=2))
    raise SystemExit(not result.wasSuccessful())
