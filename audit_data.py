"""Verify sources, field validity, disjoint course groups, and loss masks."""
import hashlib
import json
import re
from pathlib import Path

from transformers import AutoTokenizer
from train import tokenize_rows

ROOT = Path(__file__).resolve().parent


def main():
    courses = [json.loads(x) for x in (ROOT / 'data/courses.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len({c['code'] for c in courses}) == len(courses)
    for c in courses:
        assert c['credits'] >= 0
        assert c.get('aims') and c.get('prerequisites_text')
        assert '202627' in c['source_url']
        pdf = ROOT / 'data/raw/syllabi' / (c['code']+'.pdf')
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == c['source_sha256']
        assert c['timetable'] is None and c['workload_label'] is None
        a, b = c['assessment_percent'], c['exam_percent']
        if a is not None and b is not None:
            assert 0 <= a <= 100 and 0 <= b <= 100 and abs(a+b-100) < .01, c['code']
    tok = AutoTokenizer.from_pretrained(ROOT / 'models/Qwen3-8B', local_files_only=True)
    groups = {}
    lengths = {}
    for split in ['train', 'validation', 'test']:
        rows = [json.loads(x) for x in (ROOT / f'data/{split}.jsonl').read_text(encoding='utf-8').splitlines()]
        codes = {r['course_code'] for r in rows}
        groups[split] = {re.sub(r'\W+', '', c['aims'].lower()) for c in courses if c['code'] in codes}
        tokenized = tokenize_rows(ROOT / f'data/{split}.jsonl', tok)
        assert all(r['labels'][0] == -100 and any(y != -100 for y in r['labels']) for r in tokenized)
        lengths[split] = {'min': min(len(r['input_ids']) for r in tokenized),
                          'max': max(len(r['input_ids']) for r in tokenized)}
    assert not groups['train'] & groups['validation']
    assert not groups['train'] & groups['test']
    assert not groups['validation'] & groups['test']
    report = {'status': 'passed', 'courses': len(courses), 'source_hashes_verified': len(courses),
              'disjoint_normalized_aims_groups': True, 'assistant_only_loss_masks': True,
              'token_lengths': lengths,
              'missing_assessment_percentages': [c['code'] for c in courses if c['assessment_percent'] is None],
              'real_timetables': 0, 'human_reviewed_workload_labels': 0}
    (ROOT / 'reports/data_audit.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
