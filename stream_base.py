"""Load local BF16 safetensors one tensor at a time without whole-shard mmap."""
import json,struct,gc,os
def load_base(path,quantized=None):
    import torch
    from transformers import AutoConfig,AutoModelForCausalLM
    from accelerate import init_empty_weights
    from accelerate.utils import set_module_tensor_to_device
    config=AutoConfig.from_pretrained(path,local_files_only=True)
    with init_empty_weights():model=AutoModelForCausalLM.from_config(config,torch_dtype=torch.bfloat16,attn_implementation='sdpa')
    if quantized is None:quantized=os.environ.get('CITYU_QUANTIZE_4BIT')=='1'
    if quantized:
        import bitsandbytes as bnb
        for name,module in list(model.named_modules()):
            if isinstance(module,torch.nn.Linear) and name!='lm_head':
                parent,_,attribute=name.rpartition('.')
                target=model.get_submodule(parent) if parent else model
                setattr(target,attribute,bnb.nn.Linear4bit(module.in_features,module.out_features,bias=module.bias is not None,
                    compute_dtype=torch.bfloat16,compress_statistics=True,quant_type='nf4',device='meta'))
    count=0
    for shard in sorted(path.glob('model-*.safetensors')):
        with shard.open('rb') as f:
            length=struct.unpack('<Q',f.read(8))[0];header=json.loads(f.read(length));start=8+length
            for name,spec in header.items():
                if name=='__metadata__':continue
                if spec['dtype']!='BF16':raise ValueError('Unexpected base tensor dtype '+spec['dtype'])
                lo,hi=spec['data_offsets'];buffer=bytearray(hi-lo);f.seek(start+lo)
                if f.readinto(buffer)!=len(buffer):raise ValueError('Truncated model shard')
                tensor=torch.frombuffer(buffer,dtype=torch.bfloat16).reshape(spec['shape'])
                parent,_,attribute=name.rpartition('.');module=model.get_submodule(parent)
                if quantized and isinstance(module,bnb.nn.Linear4bit) and attribute=='weight':
                    module.weight=bnb.nn.Params4bit(tensor,requires_grad=False,compress_statistics=True,quant_type='nf4').to('cuda:0')
                else:set_module_tensor_to_device(model,name,'cuda:0',value=tensor,dtype=torch.bfloat16)
                del tensor,buffer;count+=1
        print('STREAMED_BASE_SHARD',shard.name,'tensors',count,flush=True);gc.collect()
    if any(p.is_meta for p in model.parameters()):raise RuntimeError('Unloaded model parameter')
    if quantized:
        model.is_loaded_in_4bit=True;model.quantization_method='bitsandbytes'
    for name,b in list(model.named_buffers()):
        if b.device.type!='cuda':
            parent,_,attribute=name.rpartition('.');module=model.get_submodule(parent) if parent else model
            setattr(module,attribute,b.to('cuda:0'))
    return model
