"""Restore the exact frozen base revision used with the released adapter."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import project_runtime
import hashlib,json
from huggingface_hub import snapshot_download

def main():
    source=json.loads((ROOT/'sources/model.json').read_text(encoding='utf-8'))
    records=json.loads((ROOT/'sources/model_files.json').read_text(encoding='utf-8'))
    destination=ROOT/'models/Qwen3-8B'
    snapshot_download(repo_id=source['repo_id'],revision=source['revision'],
                      local_dir=destination,allow_patterns=[r['file'] for r in records],max_workers=2)
    for record in records:
        file=destination/record['file'];digest=hashlib.sha256()
        with file.open('rb') as stream:
            for block in iter(lambda:stream.read(8*1024*1024),b''):digest.update(block)
        if file.stat().st_size!=record['size'] or digest.hexdigest()!=record['sha256']:
            raise RuntimeError('Frozen base integrity mismatch: '+record['file'])
        print('Verified',record['file'],flush=True)
    print('Exact frozen base restored:',source['revision'])

if __name__=='__main__':main()
