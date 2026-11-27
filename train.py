"""Local BF16 LoRA fine tuning with assistant-only loss and disjoint validation."""
import argparse
import json
import os
import random
import time
from pathlib import Path
import project_runtime

ROOT = Path(__file__).resolve().parent
os.environ['HF_HOME'] = str(ROOT / '.cache/huggingface')
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer


def tokenize_rows(path, tokenizer, max_length=1152):
    result = []
    for line in path.read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        ms = row['messages']
        prompt = tokenizer.apply_chat_template(ms[:-1], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        # In non-thinking mode the generation prompt already includes the empty think block.
        prompt_ids = tokenizer(prompt, add_special_tokens=False)['input_ids']
        answer_ids = tokenizer(ms[-1]['content'] + tokenizer.eos_token, add_special_tokens=False)['input_ids']
        ids = prompt_ids + answer_ids
        if len(ids) > max_length:
            raise ValueError(f"Example {row['id']} has {len(ids)} tokens; increase max length, do not truncate labels")
        result.append({'input_ids': ids, 'attention_mask': [1]*len(ids),
                       'labels': [-100]*len(prompt_ids) + answer_ids})
    return result


def collate(rows, pad_id):
    n = max(len(x['input_ids']) for x in rows)
    return {key: torch.tensor([x[key] + [pad_id if key == 'input_ids' else 0 if key == 'attention_mask' else -100] * (n-len(x[key])) for x in rows], device='cuda')
            for key in ['input_ids', 'attention_mask', 'labels']}


def assistant_loss(model,batch):
    """Equivalent next-token masked CE, without unused prompt-vocabulary logits."""
    targets=batch['labels'][:,1:]
    positions=(targets!=-100).any(dim=0).nonzero(as_tuple=False).flatten()
    if positions.numel()==0:raise ValueError('No supervised assistant tokens')
    output=model(input_ids=batch['input_ids'],attention_mask=batch['attention_mask'],
                 logits_to_keep=positions,use_cache=False)
    return torch.nn.functional.cross_entropy(output.logits.float().reshape(-1,output.logits.shape[-1]),
                                            targets[:,positions].reshape(-1),ignore_index=-100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--epochs', type=int, default=2)
    ap.add_argument('--accumulation', type=int, default=4)
    ap.add_argument('--max-length', type=int, default=1152)
    ap.add_argument('--lr', type=float, default=1e-4)
    ap.add_argument('--data-dir', default='data')
    ap.add_argument('--output-dir', default='adapters/bootstrap')
    ap.add_argument('--report-dir', default='reports')
    ap.add_argument('--init-adapter')
    ap.add_argument('--assistant-logits-only',action='store_true',help='Compute equivalent masked loss using only supervised next-token logits; retain the full context.')
    args = ap.parse_args()
    random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(8)
    torch.backends.cuda.matmul.allow_tf32 = True
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA GPU required for local 8B training')
    model_dir = ROOT / 'models/Qwen3-8B'
    tok = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    tok.pad_token = tok.eos_token
    train = tokenize_rows(ROOT / args.data_dir / 'train.jsonl', tok, args.max_length)
    val = tokenize_rows(ROOT / args.data_dir / 'validation.jsonl', tok, args.max_length)
    print('TOKEN_LENGTHS', min(len(x['input_ids']) for x in train), max(len(x['input_ids']) for x in train), flush=True)
    from stream_base import load_base
    model = load_base(model_dir)
    model.config.use_cache = False
    if args.init_adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, ROOT / args.init_adapter, is_trainable=True)
    else:
        model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=.05,
                     target_modules='all-linear', task_type='CAUSAL_LM', bias='none'))
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    model.print_trainable_parameters()
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.lr, weight_decay=.01)
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    report_dir = ROOT / args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    record = {'model': json.loads((ROOT / 'sources/model.json').read_text()), 'args': vars(args),
              'label_type': ({'data/ge-timetable':'published_GE_timetable_snapshot_with_BSCM_replay',
                              'data/ma-timetable':'user_saved_AIMS_CM_schedules_and_combined_requirements_with_GE_BSCM_replay',
                              'data/cm-planning-v2':'synthetic_transcript_failure_correction_and_source_grounded_five_course_plans_with_replay',
                              'data/markov-v4':'user_rule_distillation_of_Markov_profit_parameters_with_synthetic_transcript_states',
                              'data/preparation-v5':'user_rule_distillation_GE_cap_and_PDF_index_informed_preparation_hypotheses_not_empirical_workload',
                              'data/programme-v6':'user_PDF_conditioned_CM_CS_curriculum_timetables_requirements_and_single_stream_utility_distillation',
                              'data/cm-finance-background':'user_authorised_CM_advisory_EF_CS_prerequisite_waiver_and_synthetic_finance_background_policy_with_source_replay',
                              'data/timetable-grounded':'saved_exact_term_CM_CS_timetable_evidence_and_synthetic_EF_mismatch_policy_with_corrective_rollout_replay'}.get(args.data_dir,'synthetic_rubric_not_human_reviewed')), 'torch': torch.__version__,
              'gpu': torch.cuda.get_device_name(), 'train_examples': len(train), 'validation_examples': len(val),
              'training_method': ('NF4 frozen base with BF16 compute and rank-8 QLoRA' if os.environ.get('CITYU_QUANTIZE_4BIT')=='1' else 'BF16 frozen base with rank-8 LoRA on all linear layers'),
              'trainable_parameters': sum(p.numel() for p in model.parameters() if p.requires_grad),
              'history': [], 'status': 'running'}
    record['loss_method']='assistant_positions_only_equivalent_masked_CE' if args.assistant_logits_only else 'standard_full_logits_masked_CE'

    def loss_for(batch):
        return assistant_loss(model,batch) if args.assistant_logits_only else model(**batch).loss

    def evaluate():
        model.eval()
        total, tokens = 0., 0
        with torch.no_grad():
            for row in val:
                batch = collate([row], tok.pad_token_id)
                count = (batch['labels'][:, 1:] != -100).sum().item()
                loss = loss_for(batch)
                total += loss.item() * count
                tokens += count
        model.train()
        return total/tokens

    record['initial_validation_loss'] = evaluate()
    (report_dir / 'training.json').write_text(json.dumps(record, indent=2))
    print('INITIAL_VALIDATION', record['initial_validation_loss'], flush=True)
    best = float('inf')
    log = (report_dir / 'train-progress.jsonl').open('w', encoding='utf-8')
    step = 0
    for epoch in range(args.epochs):
        order = list(range(len(train)))
        random.Random(42+epoch).shuffle(order)
        model.train()
        optimizer.zero_grad(set_to_none=True)
        losses = []
        for i, index in enumerate(order):
            batch = collate([train[index]], tok.pad_token_id)
            loss = loss_for(batch)
            if not torch.isfinite(loss):
                raise RuntimeError('Non-finite loss')
            # Correctly normalize the final partial accumulation window.
            window = min(args.accumulation, len(order) - (i//args.accumulation)*args.accumulation)
            (loss/window).backward()
            losses.append(loss.item())
            if (i+1) % args.accumulation == 0 or i+1 == len(order):
                torch.nn.utils.clip_grad_norm_((p for p in model.parameters() if p.requires_grad), 1.)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                step += 1
                progress = {'epoch': epoch+1, 'example': i+1, 'optimizer_step': step,
                            'loss': sum(losses[-window:])/window,
                            'elapsed_seconds': round(time.perf_counter()-start, 1)}
                log.write(json.dumps(progress)+'\n')
                log.flush()
                if step % 5 == 0:
                    print(json.dumps(progress), flush=True)
        score = evaluate()
        record['history'].append({'epoch': epoch+1, 'train_loss': sum(losses)/len(losses), 'validation_loss': score})
        if score < best:
            best = score
            record['selected_epoch'] = epoch+1
            model.save_pretrained(out, safe_serialization=True)
            tok.save_pretrained(out)
        record.update(seconds=time.perf_counter()-start, peak_gpu_allocated_gb=torch.cuda.max_memory_allocated()/2**30,
                      optimizer_steps=step)
        (report_dir / 'training.json').write_text(json.dumps(record, indent=2))
        print('EPOCH_COMPLETE', json.dumps(record['history'][-1]), flush=True)
    record['status'] = 'complete'
    (report_dir / 'training.json').write_text(json.dumps(record, indent=2))
    print('TRAINING_COMPLETE', json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
