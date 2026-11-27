"""Use the catalogue's publicly linked downloadable syllabi, at a modest rate."""
import hashlib
import io
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
logging.getLogger('pypdf').setLevel(logging.ERROR)


def extract(text, label, next_labels):
    m = re.search(r'(?m)^\s*(?:\d+\.\s*)?' + re.escape(label) + r'\s*:?\s*\n', text)
    if not m:
        return None
    rest = text[m.end():]
    ends = [p.start() for next_label in next_labels
            if (p := re.search(r'(?m)^\s*(?:\d+\.\s*)?' + re.escape(next_label) + r'\s*:?\s*\n', rest))]
    rest = rest[:min(ends)] if ends else rest
    rest = re.sub(r'(?m)^\d+\s+[^\n]+\n', '', rest)
    return ' '.join(rest.replace('(Course Code and Title)', '').split())


def main():
    links = json.loads((ROOT / 'data/catalogue_links.json').read_text())
    selected = sorted(c for c in links if c.startswith('CS'))[:40] + sorted(c for c in links if c.startswith('GE'))[:40]
    existing = {c['code']: c for c in [json.loads(x) for x in (ROOT / 'data/courses.jsonl').read_text(encoding='utf-8').splitlines()]}
    out = ROOT / 'data/raw/syllabi'
    out.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers['User-Agent'] = 'CityUCourseHelperResearch/0.1 (local academic prototype)'
    failures = []
    for code in selected:
        url = f'https://www.cityu.edu.hk/ug/202627/course/{code}.pdf'
        try:
            path = out / (code + '.pdf')
            if path.exists():
                content = path.read_bytes()
            else:
                time.sleep(2)
                r = session.get(url, timeout=45)
                r.raise_for_status()
                content = r.content
                if not content.lstrip().startswith(b'%PDF'):
                    raise RuntimeError('Public PDF unavailable or access declined; stopping fetch')
                path.write_bytes(content)
            pdf = PdfReader(io.BytesIO(content))
            text = '\n'.join(p.extract_text() or '' for p in pdf.pages)
            if code not in text:
                raise ValueError('Course code does not match syllabus')
            (out / (code + '.txt')).write_text(text, encoding='utf-8')
            # A page header can fall between a field name and its value.
            text = re.sub(r'(?m)^\d+\s+' + re.escape(code) + r':[^\n]*\n', '', text)
            title = extract(text, 'Course Title', ['Subject Code', 'Course Code'])
            credit = extract(text, 'Credit Units', ['Level'])
            if credit and re.fullmatch(r'\d+-\d+', credit):
                raise ValueError('Variable-credit course excluded from the fixed-credit single-semester prototype: ' + credit)
            if not title or not credit or not re.fullmatch(r'\d+(?:\.\d+)?', credit):
                raise ValueError('Unsupported syllabus layout')
            c = existing.get(code, {'code': code, 'offering_text': None, 'timetable': None, 'workload_label': None})
            c.update(title=title, credits=float(credit), catalogue_year='2026/27',
                     source_url=url, detail_pdf_url=url, fetched_at=datetime.now(timezone.utc).isoformat(),
                     source_sha256=hashlib.sha256(content).hexdigest(),
                     review_status='public_facts_only_not_human_reviewed',
                     effective_term=extract(text, 'Effective Term', ['Part I Course Overview']),
                     aims=extract(text, 'Abstract', ['Course Intended Learning Outcomes (CILOs)']),
                     prerequisites_text=extract(text, 'Prerequisites', ['Precursors']),
                     precursors_text=extract(text, 'Precursors', ['Equivalent Courses']),
                     equivalent_text=extract(text, 'Equivalent Courses', ['Exclusive Courses']),
                     exclusive_text=extract(text, 'Exclusive Courses', ['Part II Course Details']),
                     syllabus_text=text)
            for field, label in [('assessment_percent', 'Continuous Assessment (%)'), ('exam_percent', 'Examination (%)')]:
                m = re.search(re.escape(label) + r'\s*\n(\d+(?:\.\d+)?)', text)
                c[field] = float(m.group(1)) if m else c.get(field)
            existing[code] = c
            print('SYLLABUS', code, title, flush=True)
        except Exception as exc:
            failures.append({'code': code, 'error': str(exc)})
            print('FAILED', code, str(exc), flush=True)
            if 'stopping fetch' in str(exc) or isinstance(exc, requests.HTTPError) and exc.response.status_code in [403, 429]:
                break
    courses = [existing[c] for c in sorted(existing)]
    (ROOT / 'data/courses.jsonl').write_text(''.join(json.dumps(c, ensure_ascii=False)+'\n' for c in courses), encoding='utf-8')
    (ROOT / 'reports/syllabi.json').write_text(json.dumps({'courses': len(courses), 'failures': failures}, indent=2))


if __name__ == '__main__':
    main()
