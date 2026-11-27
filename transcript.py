"""Optional text-only local extraction; nothing is uploaded or retained by default."""
import argparse
import json
import re
from pypdf import PdfReader


def candidate_codes(path):
    text = '\n'.join(p.extract_text() or '' for p in PdfReader(path).pages)
    if len(text.strip()) < 30:
        raise ValueError('No usable text layer; OCR is outside this prototype scope')
    # A match may be a failed or withdrawn course; completion always needs confirmation.
    return {'candidate_course_codes': sorted(set(re.findall(r'\b[A-Z]{2,5}\s?\d{4}[A-Z]?\b', text))),
            'completed_courses_verified': False,
            'warning': 'Confirm passing grades and completion; extracted codes alone are not proof.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    a = ap.parse_args()
    print(json.dumps(candidate_codes(a.pdf), indent=2))
