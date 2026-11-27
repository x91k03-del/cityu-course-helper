"""Offline scoring and comparison using the same supplied evidence and profiles."""
import argparse
import contextlib
import json
import math
import os
import time
from pathlib import Path
import project_runtime

ROOT = Path(__file__).resolve().parent
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from build_dataset import messages, PROFILES

FIELDS = ['background_mismatch', 'difficulty', 'workload']


def current_timetable_adapter(fallback='adapters/bscm-timetable'):
    """Use the explicitly activated timetable adapter when present."""
    manifest = ROOT / 'data/active_timetable_adapter.json'
    if manifest.exists():
        value = json.loads(manifest.read_text(encoding='utf-8'))
        candidate = value['adapter']
        if (ROOT / candidate / 'adapter_config.json').is_file():
            return candidate
        raise ValueError('Active timetable adapter files are missing: ' + candidate)
    return fallback


def validate_score(value, code):
    if not isinstance(value, dict):
        raise ValueError('Score response must be a JSON object')
    if value.get('course_code') != code:
        raise ValueError('Incorrect course code')
    for key in FIELDS:
        if type(value.get(key)) not in (int, float) or not math.isfinite(value[key]) or not 0 <= value[key] <= 1:
            raise ValueError('Invalid score: ' + key)
    if value.get('label_type') != 'synthetic_rubric' or value.get('needs_review') is not True:
        raise ValueError('Missing synthetic label disclosure')
    return value


def load(adapter='adapters/bootstrap'):
    quantized=(ROOT / adapter / 'base_loading.json').exists() or os.environ.get('CITYU_QUANTIZE_4BIT')=='1'
    path = ROOT / 'models/Qwen3-8B'
    tok = AutoTokenizer.from_pretrained(path, local_files_only=True)
    from stream_base import load_base
    model = load_base(path,quantized=quantized)
    model = PeftModel.from_pretrained(model, ROOT / adapter, is_trainable=False)
    model.eval()
    return tok, model


def generate(tok, model, ms, baseline=False, max_tokens=160):
    text = tok.apply_chat_template(ms, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    batch = tok(text, return_tensors='pt').to('cuda')
    with (model.disable_adapter() if baseline else contextlib.nullcontext()), torch.inference_mode():
        ids = model.generate(**batch, max_new_tokens=max_tokens, do_sample=False,
                             pad_token_id=tok.eos_token_id, use_cache=True)
    return tok.decode(ids[0, batch.input_ids.shape[1]:], skip_special_tokens=True).strip()


def generate_batch(tok,model,conversations,max_tokens=420):
    """Greedy left-padded evaluation of independent prompts on the same adapter."""
    if not conversations:return []
    original_side=tok.padding_side;tok.padding_side='left'
    try:
        texts=[tok.apply_chat_template(ms,tokenize=False,add_generation_prompt=True,enable_thinking=False) for ms in conversations]
        batch=tok(texts,padding=True,return_tensors='pt').to('cuda')
        with torch.inference_mode():
            ids=model.generate(**batch,max_new_tokens=max_tokens,do_sample=False,pad_token_id=tok.pad_token_id,use_cache=True)
        return [tok.decode(row[batch.input_ids.shape[1]:],skip_special_tokens=True).strip() for row in ids]
    finally:tok.padding_side=original_side


def main():
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['evaluate', 'score', 'baseline-schedule', 'recommend'])
    p.add_argument('--course')
    p.add_argument('--profile')
    p.add_argument('--problem')
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--adapter', help='Optional local adapter path; BSCM profiles select adapters/bscm automatically.')
    a = p.parse_args()
    torch.set_num_threads(8)
    profile = json.loads(Path(a.profile).read_text(encoding='utf-8')) if a.profile else PROFILES[1]
    request_messages = messages
    use_bscm = False
    adapter = a.adapter or 'adapters/bootstrap'
    if a.command != 'evaluate':
        from bscm import canonical, score_messages, score_target
        normalized = canonical(profile)
        if normalized.get('major') == 'Computing Mathematics':
            profile = normalized
            use_bscm = True
            request_messages = score_messages
            if not a.adapter:
                adapter = 'adapters/bscm'
    tok, model = load(adapter)
    if a.command == 'evaluate':
        rows = [json.loads(x) for x in (ROOT / 'data/test.jsonl').read_text(encoding='utf-8').splitlines()]
        if a.limit:
            # Spread a limited run across courses and profiles, rather than taking one course.
            rows = rows[::max(1, len(rows)//a.limit)][:a.limit]
        result = {'evaluation_target': 'synthetic_rubric_only_not_real_student_workload',
                  'test_examples': len(rows), 'methods': {}}
        start = time.perf_counter()
        with (ROOT / 'reports/predictions.jsonl').open('w', encoding='utf-8') as f:
            for name in ['base', 'fine_tuned']:
                squared = {k: [] for k in FIELDS}
                valid = 0
                score_valid, extraction_count, extraction_exact = 0, 0, 0
                for row in rows:
                    raw = generate(tok, model, row['messages'][:-1], baseline=name == 'base', max_tokens=256)
                    record = {'id': row['id'], 'method': name, 'raw_response': raw}
                    try:
                        pred = json.loads(raw)
                        truth = json.loads(row['messages'][-1]['content'])
                        if row.get('task') == 'extract':
                            extraction_count += 1
                            if not isinstance(pred, dict) or set(pred) != set(truth):
                                raise ValueError('Invalid extraction schema')
                            extraction_exact += int(pred == truth)
                        else:
                            validate_score(pred, row['course_code'])
                            score_valid += 1
                            for key in FIELDS:
                                squared[key].append((pred[key]-truth[key])**2)
                        valid += 1
                        record['prediction'] = pred
                    except (ValueError, TypeError) as exc:
                        record['error'] = str(exc)
                    f.write(json.dumps(record, ensure_ascii=False)+'\n')
                    f.flush()
                    print(name, row['id'], 'valid', 'error' not in record, flush=True)
                result['methods'][name] = {'valid_json_and_schema': valid, 'invalid': len(rows)-valid,
                       'valid_score_predictions': score_valid, 'exact_fact_extractions': extraction_exact,
                       'fact_extraction_examples': sum(r.get('task') == 'extract' for r in rows),
                       'mse_on_valid_synthetic_targets': {k: sum(v)/len(v) if v else None for k, v in squared.items()}}
                (ROOT / 'reports/evaluation.json').write_text(json.dumps(result, indent=2))
        result['seconds'] = time.perf_counter()-start
        (ROOT / 'reports/evaluation.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
    else:
        courses = [json.loads(x) for x in (ROOT / 'data/courses.jsonl').read_text(encoding='utf-8').splitlines()]
        if a.command == 'recommend':
            from scheduler import solve
            if not a.problem:
                raise ValueError('--problem is required: normalized reviewed section bundles and constraints')
            problem = json.loads(Path(a.problem).read_text(encoding='utf-8'))
            from planning_policy import apply_profile_policy
            apply_profile_policy(problem,profile)
            if problem['completed_courses'] != profile['completed_courses']:
                raise ValueError('Student and scheduler completed-course lists differ')
            lookup = {c['code']: c for c in courses}
            scores = {}
            for option in problem['options']:
                code = option['course_code']
                if code not in lookup:
                    raise ValueError('No source course record for ' + code)
                if code not in scores:
                    raw = generate(tok, model, request_messages(lookup[code], profile))
                    scores[code] = validate_score(json.loads(raw), code)
                    if use_bscm:
                        scores[code] = score_target(lookup[code], profile)
                option['scores'] = {k: scores[code][k] for k in FIELDS}
            result = {'schedule': solve(problem), 'scores': scores,
                      'warning': 'All model scores are bootstrap estimates pending human review.'}
            (ROOT / 'reports/recommendation.json').write_text(json.dumps(result, indent=2))
            print(json.dumps(result, indent=2))
        elif a.command == 'score':
            course = next(c for c in courses if c['code'] == (a.course or 'CS3334'))
            raw = generate(tok, model, request_messages(course, profile))
            value = validate_score(json.loads(raw), course['code'])
            raw_value = value
            if use_bscm:
                value = score_target(course, profile)
            print(json.dumps({'prediction': value, 'source_url': course['source_url'],
                              **({'raw_model_prediction': raw_value, 'score_method': 'deterministic_synthetic_rubric_after_model_inference'} if use_bscm else {}),
                              'warning': 'Bootstrap estimate; reviewed workload labels and timetable required.'}, indent=2))
        else:
            context = [{'code': c['code'], 'credits': c['credits'], 'title': c['title'],
                        'prerequisites': c.get('prerequisites_text'), 'timetable': c.get('timetable')}
                       for c in courses[:8]]
            ms = [{'role': 'system', 'content': 'You are a local CityU course helper. Use only supplied facts. Return JSON with candidate_courses, explanation, missing_data and feasibility_verified. Do not invent meeting times, seats or prerequisites. Mark feasibility_verified false when data are incomplete.'},
                  {'role': 'user', 'content': json.dumps({'student': profile, 'courses': context})}]
            raw = generate(tok, model, ms, baseline=True, max_tokens=512)
            (ROOT / 'reports/pure_llm_example.txt').write_text(raw, encoding='utf-8')
            print(raw)


if __name__ == '__main__':
    main()
