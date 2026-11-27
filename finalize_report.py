"""Write a concise report from measured artifacts; never manufacture run results."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / 'reports' / name).read_text(encoding='utf-8'))


def main():
    training = read('training.json')
    assert training['status'] == 'complete'
    evaluation = read('evaluation.json')
    comparison = read('method_comparison.json')
    audit = read('data_audit.json')
    tests = read('scheduler_tests.json')
    assert audit['status'] == 'passed' and tests['failures'] == tests['errors'] == 0
    b = evaluation['methods']['base']
    t = evaluation['methods']['fine_tuned']
    lines = [
        '# Completed local run', '',
        'Model: Qwen/Qwen3-8B with a locally trained BF16 LoRA adapter. Hardware: ' + training['gpu'] + '.', '',
        '**Status: bootstrap training and local evaluation completed. Reviewed-label validation and real-semester scheduling remain pending.**', '',
        '## Measured results', '',
        f"- Course data: {audit['courses']} parsed records; {audit['source_hashes_verified']} source hashes verified.",
        f"- Training: {training['train_examples']} examples, {training['args']['epochs']} epochs, {training['optimizer_steps']} optimizer steps.",
        f"- Trainable adapter parameters: {training['trainable_parameters']:,}.",
        f"- Selected epoch: {training['selected_epoch']}; initial validation loss {training['initial_validation_loss']:.5f}.",
        '- Validation loss after each pass: ' + '; '.join(f"pass {r['epoch']}: {r['validation_loss']:.5f}" for r in training['history']) + '.',
        f"- Training time: {training['seconds']/60:.1f} minutes; peak Torch GPU allocation {training['peak_gpu_allocated_gb']:.2f} GiB (excludes other applications and some reserved memory).",
        f"- Held-out examples: {evaluation['test_examples']}. Valid output schemas: base {b['valid_json_and_schema']}, tuned {t['valid_json_and_schema']}.",
        f"- Exact typed source-fact extractions: base {b['exact_fact_extractions']}/{b['fact_extraction_examples']}, tuned {t['exact_fact_extractions']}/{t['fact_extraction_examples']}.",
        f"- Fact value matches after converting numeric strings: base {b['fact_values_match_after_numeric_normalization']}/{b['fact_extraction_examples']}, tuned {t['fact_values_match_after_numeric_normalization']}/{t['fact_extraction_examples']}. This separates formatting gains from factual gains.",
        '- Synthetic-target MSE (base → tuned): ' + '; '.join(f"{k.replace('_', ' ')}: {b['mse_on_valid_synthetic_targets'][k]:.6f} → {t['mse_on_valid_synthetic_targets'][k]:.6f}" for k in ['background_mismatch', 'difficulty', 'workload']) + '.',
        f"- Scheduler: {tests['tests']} tests passed, including {tests['random_bruteforce_instances']} exhaustive-search comparisons.", '',
        'All numeric training labels and MSE targets are synthetic rubric estimates. Valid-only MSE excludes invalid responses; the invalid count is reported alongside it. These numbers do not establish real CityU workload prediction quality.', '',
        '## Proposal coverage', '',
        '| Requirement | Result |', '| --- | --- |',
        '| Local Qwen model and task adaptation | Installed official pinned base weights; trained a separate local adapter |',
        '| Public CityU course information | Collected syllabus sources and extracted fields |',
        '| LLM scoring + MILP | Implemented and tested; real term data still required |',
        '| Pure LLM baseline and same synthetic profiles | Compared on six profiles using the same simulated constraint fixtures |',
        '| Hard prerequisites, credits, required courses, clashes | Solver supports reviewed rules and complete section bundles; missing evidence fails closed |',
        '| Workload balance by assessment week | Cap constraints implemented; real timing data unavailable |',
        '| UIUC/CMU topic matching | Deferred: underlying data reuse permissions unverified |',
        '| Reviewed workload labels / real workload MSE | Not available; blank label review worksheet provided |',
        '| Student/senior-student rankings | Not collected |',
        '| Optional transcript | Local text extraction only; completion must be confirmed |', '',
        '## Synthetic schedule comparison', '',
        'The comparison uses real course descriptions but simulated eligibility and meetings, explicitly labelled as synthetic. No result is an actual CityU schedule.', '',
    ]
    for method, values in comparison['methods'].items():
        lines.append(f"- {method}: {values['schedules_with_violations']}/{values['schedules']} schedules with constraint violations; {values['total_constraint_violations']} total violations.")
    lines += ['', '## Run it', '', '```powershell', 'cd F:\\CODEX\\cityu-course-helper',
              '.\\run.ps1 -Action score -Course CS3334', '.\\run.ps1 -Action demo', '```', '',
              'See README.md for custom profiles, verified semester data, review labels, provenance and reproducibility.']
    (ROOT / 'RUN_REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    card = ('---\nbase_model: Qwen/Qwen3-8B\nlibrary_name: peft\nlicense: apache-2.0\n'
            'language:\n- en\ntags:\n- lora\n- education\n- experimental\n---\n\n'
            '# CityU course helper bootstrap adapter\n\n'
            'Locally trained rank-8 LoRA. Requires the separately installed Qwen3-8B base. '
            'Public course-fact extraction and synthetic-rubric scoring only. '
            'No human-reviewed workload labels, real schedule validation, or student preference validation. '
            'Do not describe this adapter as a validated CityU workload model.\n\n'
            f"Base revision: `{training['model']['revision']}`. Selected epoch: {training['selected_epoch']}. "
            'See ../../RUN_REPORT.md and ../../sources/README.md for measured results and source provenance.\n')
    (ROOT / 'adapters/bootstrap/README.md').write_text(card, encoding='utf-8')
    print('REPORTS_COMPLETE')


if __name__ == '__main__':
    main()
