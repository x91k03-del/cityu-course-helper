import json,tempfile,unittest
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import patch
from import_ma_timetable import run_import,import_file
from test_banweb_collector import SAMPLE

BULK='''<table><tr><th>Term</th><th>Course Code</th><th>CRN</th><th>Section</th><th>Day</th><th>Time</th></tr>
<tr><td>202609</td><td>MA1502</td><td>12345</td><td>C01</td><td>Mon</td><td>09:00-11:50</td></tr>
<tr><td>202609</td><td>MA2508</td><td>12346</td><td>C01</td><td>Tue</td><td>14:00-16:50</td></tr>
<tr><td>202609</td><td>CS2360</td><td>12347</td><td>C01</td><td>Wed</td><td>09:00-11:50</td></tr>
<tr><td>202509</td><td>MA3515</td><td>12348</td><td>C01</td><td>Fri</td><td>09:00-11:50</td></tr></table>'''

class OfflineTests(unittest.TestCase):
    def test_bulk_import_subject_and_term_filter_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);src=d/'input';src.mkdir();(src/'all_ma.html').write_text(BULK,encoding='utf-8')
            with patch('socket.socket',side_effect=AssertionError('Network access forbidden')):
                r=run_import(src,d/'out')
            self.assertEqual(r['imported_courses'],2);self.assertEqual(r['meeting_rows'],2)
            rows=json.loads((d/'out/meeting_rows.json').read_text());self.assertEqual({x['course_code'] for x in rows},{'MA1502','MA2508'})
    def test_individual_file_and_unknown_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'MA1502.html';p.write_text(SAMPLE,encoding='utf-8')
            rs,issues=import_file(p,'202609','MA');self.assertFalse(issues);self.assertEqual(len(rs[0]['meeting_rows']),3)
            self.assertIsNone(rs[0]['meeting_rows'][-1]['start_date'])
    def test_blank_term_does_not_inherit_another_rows_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bulk.html'
            p.write_text(BULK.replace('<td>202609</td><td>MA2508</td>','<td></td><td>MA2508</td>'))
            records,_=import_file(p,'202609','MA')
            row=next(row for result in records for row in result['meeting_rows'] if row['course_code']=='MA2508')
            self.assertEqual(row['term_verification'],'user_selected_term_not_independently_verified')
    def test_mhtml_frame_and_credentials_not_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);src=d/'input';src.mkdir()
            m=EmailMessage();m.set_type('multipart/related')
            outer=EmailMessage();outer.set_content('<html><input type="password" value="DO_NOT_EXPORT_SECRET"></html>',subtype='html');outer['Content-Location']='https://www.cityu.edu.hk/portal/'
            frame=EmailMessage();frame.set_content(SAMPLE,subtype='html');frame['Content-Location']='https://banweb.cityu.edu.hk/pls/PROD/hwscrssh_cityu.P_DispOneSection?term=202609&subj=MA&crse=1502&session=DO_NOT_EXPORT_TOKEN'
            m.attach(outer);m.attach(frame);(src/'schedule.mhtml').write_bytes(m.as_bytes())
            r=run_import(src,d/'out');self.assertEqual(r['imported_courses'],1)
            all_output=''.join(p.read_text(encoding='utf-8') for p in (d/'out').rglob('*.json'))
            self.assertNotIn('DO_NOT_EXPORT_SECRET',all_output);self.assertNotIn('DO_NOT_EXPORT_TOKEN',all_output)
            self.assertEqual(r['source_term_verified_rows'],3)
    def test_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);src=d/'input';src.mkdir();(src/'first.html').write_text(BULK);(src/'second.html').write_text(BULK)
            self.assertEqual(run_import(src,d/'out')['meeting_rows'],2)
    def test_bad_source_term(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'MA1502.html'
            p.write_text('<!-- saved from url=(0123)https://banweb.cityu.edu.hk/x?term=202509&subj=MA&crse=1502 -->'+SAMPLE)
            rs,issues=import_file(p,'202609','MA');self.assertFalse(rs);self.assertTrue(issues)
    def test_filename_identity_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'MA1502.html'
            p.write_text('<!-- saved from url=(0123)https://banweb.cityu.edu.hk/x?term=202609&subj=MA&crse=2508 -->'+SAMPLE)
            self.assertFalse(import_file(p,'202609','MA')[0])
    def test_error_page_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);src=d/'input';src.mkdir();(src/'MA1502.html').write_text('A break-in attempt has been detected.')
            with self.assertRaises(ValueError):run_import(src,d/'out')
            report=json.loads((d/'out/offline_import.json').read_text());self.assertFalse(report['complete'])
    def test_stale_files_do_not_fill_missing_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);src=d/'input';src.mkdir();(src/'MA1502.html').write_text(SAMPLE)
            out=d/'out';(out/'courses').mkdir(parents=True);(out/'courses/MA2508.json').write_text('{}')
            expected=d/'expected.txt';expected.write_text('MA1502\nMA2508')
            report=run_import(src,out,expected_file=expected)
            self.assertEqual(report['missing_expected_courses'],['MA2508'])
            self.assertFalse(json.loads((out/'run.json').read_text())['all_requested_processed'])
    def test_five_digit_course(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'MA15020.html';p.write_text(SAMPLE)
            self.assertEqual(import_file(p,'202609','MA')[0][0]['course_code'],'MA15020')

if __name__=='__main__':unittest.main(verbosity=2)
