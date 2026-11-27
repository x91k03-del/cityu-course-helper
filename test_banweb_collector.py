import tempfile,unittest
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from collect_banweb_timetable import course_url,course_from_link,course_file,parse_html,parse_times,parse_days,parse_date,aggregate

SAMPLE='''<html><body><h1>MA1502 Algebra</h1><table>
<tr><th>CRN</th><th>Section</th><th>Type</th><th>Days</th><th>Time</th><th>Start Date</th><th>End Date</th><th>Building</th><th>Room</th></tr>
<tr><td rowspan="2">12345</td><td rowspan="2">C01</td><td>Lecture</td><td>Mon Wed</td><td>09:00 - 10:50</td><td>31-AUG-2026</td><td>28-NOV-2026</td><td>YEUNG</td><td>LT-1</td></tr>
<tr><td>Lecture</td><td>Fri</td><td>14:00 - 14:50</td><td>31-AUG-2026</td><td>28-NOV-2026</td><td>LI</td><td>2405</td></tr>
<tr><td>12346</td><td>T01</td><td>Tutorial</td><td>TBA</td><td>Arranged</td><td></td><td></td><td></td><td></td></tr>
</table></body></html>'''

class CollectorTests(unittest.TestCase):
    def test_correct_course_url(self):
        u=urlparse(course_url('202609','MA','1502'));q=parse_qs(u.query,keep_blank_values=True)
        self.assertEqual(q['crse'],['1502']);self.assertEqual(q['camp'],['%']);self.assertEqual(q['web_avail'],[''])
    def test_url_validation(self):
        for term,subj,crse in [('202609','MA&x=bad','1502'),('202609','MA','%'),('invalid','MA','1502')]:
            with self.assertRaises(ValueError):course_url(term,subj,crse)
    def test_discovery_scope(self):
        u=course_url('202609','MA','1502')
        self.assertEqual(course_from_link(u,u,'202609','MA'),('MA','1502'))
        self.assertIsNone(course_from_link(u,u,'202509','MA'))
        self.assertIsNone(course_from_link(u,u,'202609','CS'))
        self.assertIsNone(course_from_link(u.replace('banweb.cityu.edu.hk','evil.example'),u,'202609','ALL'))
        self.assertEqual(course_from_link("javascript:window.open('"+u+"')",u,'202609','MA'),('MA','1502'))
        self.assertEqual(course_from_link("javascript:window.open('"+u.split('/pls/PROD/')[1]+"')",u,'202609','MA'),('MA','1502'))
    def test_spans_and_meetings(self):
        r=parse_html(SAMPLE,'MA','1502','202609');a,b,c=r['meeting_rows']
        self.assertEqual(a['days'],['Mon','Wed']);self.assertEqual(b['crn'],'12345');self.assertEqual(b['section'],'C01')
        self.assertEqual(a['start_time'],'09:00');self.assertEqual(a['start_date'],'2026-08-31')
        self.assertEqual(b['room'],'2405');self.assertIsNone(c['days']);self.assertIsNone(c['start_time'])
        self.assertEqual(r['status'],'parsed_with_warnings')
    def test_clock_variants(self):
        self.assertEqual(parse_times('0900-1150'),('09:00','11:50'))
        self.assertEqual(parse_times('1:00 PM - 2:50 PM'),('13:00','14:50'))
        self.assertEqual(parse_times('11:00 - 1:50 PM'),(None,None))
        self.assertEqual(parse_times('15:00-09:00'),(None,None))
    def test_days_dates(self):
        self.assertEqual(parse_days('MWF'),['Mon','Wed','Fri']);self.assertEqual(parse_days('TR'),['Tue','Thu'])
        self.assertEqual(parse_days('Thursday'),['Thu']);self.assertIsNone(parse_days('TBA'))
        self.assertEqual(parse_date('31-AUG-26'),'2026-08-31');self.assertIsNone(parse_date('09/10/2026'))
    def test_unknown_layout_not_success(self):
        self.assertEqual(parse_html('<form><input type="password"></form>','MA','1502','202609')['status'],'unrecognized_layout')
        self.assertEqual(parse_html('<p>No classes found</p>','MA','1502','202609')['status'],'not_offered')
    def test_separate_time_columns(self):
        h='<table><tr><th>CRN</th><th>Section</th><th>Day</th><th>Start Time</th><th>End Time</th></tr><tr><td>10000</td><td>C02</td><td>Tue</td><td>13:00</td><td>14:50</td></tr></table>'
        self.assertEqual(parse_html(h,'MA','1502','202609')['meeting_rows'][0]['end_time'],'14:50')
    def test_multiline_and_nested_tables(self):
        nested='<table><tr><td>'+SAMPLE+'</td></tr></table>'
        self.assertEqual(len(parse_html(nested,'MA','1502','202609')['meeting_rows']),3)
    def test_mixed_course_rows_not_mislabelled(self):
        h='<table><tr><th>Subj</th><th>Crse</th><th>CRN</th><th>Section</th><th>Day</th><th>Time</th></tr>'
        h+='<tr><td>CS</td><td>1502</td><td>11111</td><td>C01</td><td>Mon</td><td>09:00-10:50</td></tr>'
        h+='<tr><td>MA</td><td>2508</td><td>11112</td><td>C01</td><td>Mon</td><td>09:00-10:50</td></tr>'
        h+='<tr><td>MA</td><td>1502</td><td>11113</td><td>C01</td><td>Tue</td><td>14:00-16:50</td></tr></table>'
        rows=parse_html(h,'MA','1502','202609')['meeting_rows']
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['crn'],'11113')
    def test_course_file_and_coverage(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);f=d/'list.txt';f.write_text('MA1502\nMA2508\nCS2360',encoding='utf-8')
            self.assertEqual(course_file(f,'MA'),[('MA','1502'),('MA','2508')])
            (d/'courses').mkdir();(d/'courses/MA1502.json').write_text(json.dumps(parse_html(SAMPLE,'MA','1502','202609')),encoding='utf-8')
            aggregate(d,[('MA','1502'),('MA','2508')],{'source':'fixture'})
            r=json.loads((d/'run.json').read_text());self.assertFalse(r['all_requested_processed']);self.assertEqual(r['pending_courses'],['MA2508'])
            self.assertEqual(len(json.loads((d/'sections.json').read_text())),2)

if __name__=='__main__':unittest.main(verbosity=2)
