"""Score saved responses with typed schemas and separate value-normalized fact checks."""
import json
import math
from pathlib import Path

from inference import validate_score, FIELDS

ROOT = Path(__file__).resolve().parent


def normalized_facts(value):
    result = dict(value)
    for k in ['credits', 'assessment_percent', 'exam_percent']:
        if isinstance(result.get(k), str):
            try:
                result[k] = float(result[k])
            except ValueError:
                pass
    return result


def valid_extraction(value, truth):
    if not isinstance(value, dict) or set(value) != set(truth):
        raise ValueError('Wrong extraction keys')
    if value['course_code'] != truth['course_code']:
        raise ValueError('Wrong course code')
    for k in ['credits', 'assessment_percent', 'exam_percent']:
        if value[k] is None and k != 'credits':
            continue
        if type(value[k]) not in (int, float) or not math.isfinite(value[k]) or value[k] < 0:
            raise ValueError('Extraction requires a numeric value: ' + k)
        if k != 'credits' and value[k] > 100:
            raise ValueError('Percentage out of range')
    if value['prerequisites_text'] is not None and not isinstance(value['prerequisites_text'], str):
        raise ValueError('Invalid prerequisite text')


def main():
    tests = {r['id']: r for r in [json.loads(x) for x in (ROOT / 'data/test.jsonl').read_text(encoding='utf-8').splitlines()]}
    preds = [json.loads(x) for x in (ROOT / 'reports/predictions.jsonl').read_text(encoding='utf-8').splitlines()]
    old = json.loads((ROOT / 'reports/evaluation.json').read_text())
    summary = {'evaluation_target': 'public_fact_extraction_and_synthetic_rubric_scores_not_real_student_workload',
               'test_examples': len(tests), 'seconds': old.get('seconds'),
               'schema_definition': 'Exact extraction keys and numeric JSON types; validated bounded scoring fields.',
               'numeric_normalization': 'Only numeric strings are converted for the separate factual-value comparison.',
               'methods': {}}
    for method in ['base', 'fine_tuned']:
        rows = [r for r in preds if r['method'] == method]
        assert len(rows) == len(tests) and {r['id'] for r in rows} == set(tests)
        squared = {k: [] for k in FIELDS}
        valid, exact, norm_match, valid_scores = 0, 0, 0, 0
        for row in rows:
            source = tests[row['id']]
            truth = json.loads(source['messages'][-1]['content'])
            try:
                value = json.loads(row['raw_response'])
                if source['task'] == 'extract':
                    if isinstance(value, dict):
                        norm_match += int(normalized_facts(value) == truth)
                    valid_extraction(value, truth)
                    exact += int(value == truth)
                else:
                    validate_score(value, source['course_code'])
                    valid_scores += 1
                    for k in FIELDS:
                        squared[k].append((value[k]-truth[k])**2)
                valid += 1
            except (ValueError, TypeError):
                pass
        summary['methods'][method] = {'valid_json_and_schema': valid, 'invalid': len(rows)-valid,
                 'valid_score_predictions': valid_scores,
                 'exact_fact_extractions': exact,
                 'fact_values_match_after_numeric_normalization': norm_match,
                 'fact_extraction_examples': sum(r['task'] == 'extract' for r in tests.values()),
                 'mse_on_valid_synthetic_targets': {k: sum(v)/len(v) if v else None for k, v in squared.items()}}
    (ROOT / 'reports/evaluation.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
