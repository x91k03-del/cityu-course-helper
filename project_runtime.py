"""Keep this project's temporary files and library caches on its own drive."""
import os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def configure():
    cache=ROOT/'.cache'
    locations={
        'TEMP':cache/'temp','TMP':cache/'temp','TMPDIR':cache/'temp',
        'HF_HOME':cache/'huggingface','HF_HUB_CACHE':cache/'huggingface/hub',
        'HF_DATASETS_CACHE':cache/'huggingface/datasets',
        'TORCH_HOME':cache/'torch','TORCH_EXTENSIONS_DIR':cache/'torch_extensions',
        'TORCHINDUCTOR_CACHE_DIR':cache/'torchinductor','TRITON_CACHE_DIR':cache/'triton',
        'CUDA_CACHE_PATH':cache/'cuda','XDG_CACHE_HOME':cache,
        'MPLCONFIGDIR':cache/'matplotlib','PIP_CACHE_DIR':cache/'pip','UV_CACHE_DIR':cache/'uv',
        'PYTHONPYCACHEPREFIX':cache/'pycache',
    }
    for key,path in locations.items():
        path.mkdir(parents=True,exist_ok=True);os.environ[key]=str(path)
    tempfile.tempdir=str(locations['TEMP'])
    sys.pycache_prefix=str(locations['PYTHONPYCACHEPREFIX'])
    return {key:str(value) for key,value in locations.items()}
configure()
