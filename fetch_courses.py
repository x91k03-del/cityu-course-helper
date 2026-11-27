"""Fetch public catalogue pages slowly, preserving snapshots and provenance."""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
BASE = 'https://www.cityu.edu.hk/catalogue/ug/202627/'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=80)
    args = parser.parse_args()
    raw = ROOT / 'data' / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers['User-Agent'] = 'CityUCourseHelperResearch/0.1 (local academic prototype)'
    robots = s.get('https://www.cityu.edu.hk/robots.txt', timeout=30)
    robots.raise_for_status()
    rp = RobotFileParser()
    rp.parse(robots.text.splitlines())
    (ROOT / 'sources' / 'cityu-robots.txt').write_text(robots.text, encoding='utf-8')

    def get(url):
        if urlparse(url).hostname != 'www.cityu.edu.hk' or not rp.can_fetch(s.headers['User-Agent'], url):
            raise ValueError('URL outside allowed public catalogue: ' + url)
        time.sleep(.5)
        r = s.get(url, timeout=45)
        r.raise_for_status()
        r.encoding = 'utf-8'
        return r

    links = {}
    indexes = ['catalogue/B/B_course_CS.htm', 'catalogue/B/B_ge_course_index.htm']
    for index in indexes:
        url = urljoin(BASE, index)
        r = get(url)
        (raw / Path(index).name).write_bytes(r.content)
        soup = BeautifulSoup(r.content, 'html.parser')
        # Indexes may point to discipline subindexes rather than individual courses.
        all_links = [(a.get_text(' ', strip=True), urljoin(url, a['href']))
                     for a in soup.select('a[href]')]
        print('INDEX', url, len(all_links), all_links[:12], flush=True)
        for label, link in all_links:
            if re.search(r'/course/[A-Z]{2,5}\d{4}[A-Z]?\.htm$', link):
                code = Path(urlparse(link).path).stem
                links[code] = urljoin(BASE, 'course/' + code + '.htm')
        for label, link in all_links:
            if '?page=' in link:
                link = urljoin(BASE + 'catalogue/', link.split('?page=', 1)[1])
            if re.search(r'B_(?:ge_course|course_GE)[A-Za-z_0-9]*\.htm$', link) and 'index' not in link:
                r2 = get(link)
                (raw / Path(urlparse(link).path).name).write_bytes(r2.content)
                sub = BeautifulSoup(r2.content, 'html.parser')
                for a in sub.select('a[href]'):
                    u = urljoin(link, a['href'])
                    if re.search(r'/course/[A-Z]{2,5}\d{4}[A-Z]?\.htm$', u):
                        code = Path(urlparse(u).path).stem
                        links[code] = urljoin(BASE, 'course/' + code + '.htm')
    (ROOT / 'data' / 'catalogue_links.json').write_text(json.dumps(links, indent=2))
    # Selected CS/GE prototype scope, not the entire university catalogue.
    chosen = sorted(c for c in links if c.startswith('CS'))[:args.limit // 2]
    chosen += sorted(c for c in links if c.startswith('GE'))[:args.limit - len(chosen)]
    if not chosen:
        raise RuntimeError('No course links discovered; inspect saved index snapshots')
    courses = []
    failures = []
    for code in chosen:
        try:
            url = links[code]
            r = get(url)
            (raw / (code + '.html')).write_bytes(r.content)
            soup = BeautifulSoup(r.content, 'html.parser')
            content = soup.select_one('#cityu-content')
            if content is None:
                raise ValueError('No catalogue content')
            text = content.get_text(' ', strip=True)
            lines = list(content.stripped_strings)
            title = text.split('Offering Academic Unit')[0].strip()
            credit = re.search(r'Credit Units\s+(\d+(?:\.\d+)?)', text)
            if not credit or code not in title:
                raise ValueError('Missing code or credits')
            course = {'code': code, 'title': re.sub('^' + code + r'\s*[-:]\s*', '', title),
                      'credits': float(credit.group(1)), 'catalogue_year': '2026/27',
                      'source_url': url, 'fetched_at': datetime.now(timezone.utc).isoformat(),
                      'source_sha256': hashlib.sha256(r.content).hexdigest(),
                      'catalogue_text': text, 'catalogue_lines': lines,
                      'timetable': None, 'workload_label': None,
                      'review_status': 'public_facts_only_not_human_reviewed'}
            for key, start, stops in [
                ('aims', 'Course Aims', ['Assessment', 'Detailed Course Information']),
                ('prerequisites_text', 'Prerequisites', ['Precursors', 'Equivalent Courses', 'Exclusive Courses', 'Course Offering Term', 'Course Aims']),
                ('precursors_text', 'Precursors', ['Equivalent Courses', 'Exclusive Courses', 'Course Offering Term', 'Course Aims']),
                ('exclusive_text', 'Exclusive Courses', ['Course Offering Term', 'Course Aims']),
                ('offering_text', 'Course Offering Term', ['* The offering', 'Course Aims']),
            ]:
                if start not in text:
                    course[key] = None
                    continue
                value = text.split(start, 1)[1].lstrip(' :*')
                end = min([value.index(x) for x in stops if x in value] or [len(value)])
                course[key] = value[:end].strip()
            for field, label in [('assessment_percent', 'Continuous Assessment'), ('exam_percent', 'Examination')]:
                m = re.search(label + r':\s*(\d+(?:\.\d+)?)%', text)
                course[field] = float(m.group(1)) if m else None
            course['detail_pdf_url'] = next((urljoin(url, a['href']) for a in content.select('a[href]')
                                             if a['href'].lower().endswith('.pdf')), None)
            courses.append(course)
            print('COURSE', len(courses), code, course['title'], flush=True)
        except Exception as exc:
            failures.append({'code': code, 'error': str(exc)})
    with (ROOT / 'data' / 'courses.jsonl').open('w', encoding='utf-8') as f:
        for row in courses:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    (ROOT / 'reports' / 'fetch.json').write_text(json.dumps({'courses': len(courses), 'discovered_links': len(links), 'failures': failures}, indent=2))


if __name__ == '__main__':
    main()
