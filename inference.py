"""Load the released adapter and generate objective-parameter responses."""
import contextlib,json,os
from pathlib import Path
import project_runtime

ROOT=Path(__file__).resolve().parent
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TOKENIZERS_PARALLELISM']='false'

import torch
from peft import PeftModel
from transformers import AutoTokenizer

def load(adapter=None):
    if adapter is None:
        manifest=json.loads((ROOT/'data/active_objective_parameter_adapter.json').read_text())
        if not manifest.get('accepted_for_activation') or manifest.get('role')!='objective_parameters_only':
            raise ValueError('No validated objective-parameter checkpoint is active')
        adapter=manifest['adapter']
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
