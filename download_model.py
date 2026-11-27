"""Download an immutable revision of the official model; no remote model code."""
import os
from pathlib import Path
import project_runtime

ROOT = Path(__file__).resolve().parent
os.environ['HF_HOME'] = str(ROOT / '.cache' / 'huggingface')
os.environ['HF_HUB_DISABLE_XET'] = '1'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '120'
os.environ['HF_HUB_ETAG_TIMEOUT'] = '30'

if __name__ == '__main__':
    import json
    import hashlib
    import re
    import time
    import requests
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timezone
    from huggingface_hub import HfApi, snapshot_download
    info = HfApi().model_info('Qwen/Qwen3-8B', files_metadata=True)
    record = {'repo_id': info.id, 'revision': info.sha,
              'retrieved_at': datetime.now(timezone.utc).isoformat(),
              'official_url': 'https://huggingface.co/Qwen/Qwen3-8B'}
    (ROOT / 'sources' / 'model.json').write_text(json.dumps(record, indent=2))
    print(json.dumps(record), flush=True)
    dest = ROOT / 'models/Qwen3-8B'
    dest.mkdir(parents=True, exist_ok=True)
    files = [x for x in info.siblings if re.search(r'\.(json|safetensors|txt|jinja|md|model)$', x.rfilename) or x.rfilename == 'LICENSE']

    def download(item):
        target = dest / item.rfilename
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = item.lfs.sha256 if item.lfs else None
        if target.exists() and target.stat().st_size == item.size:
            if not expected or hashlib.sha256(target.read_bytes()).hexdigest() == expected:
                return {'file': item.rfilename, 'size': item.size,
                        'sha256': expected or hashlib.sha256(target.read_bytes()).hexdigest(), 'verified': True}
        url = f'https://huggingface.co/{info.id}/resolve/{info.sha}/{item.rfilename}'
        if not item.rfilename.endswith('.safetensors'):
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            target.write_bytes(r.content)
        else:
            part = target.with_suffix('.partial')
            size = part.stat().st_size if part.exists() else 0
            with part.open('ab') as f:
                while size < item.size:
                    end = min(size + 32*1024*1024, item.size) - 1
                    for attempt in range(4):
                        try:
                            r = requests.get(url, headers={'Range': f'bytes={size}-{end}'}, timeout=120)
                            r.raise_for_status()
                            if r.status_code != 206 or r.headers.get('Content-Range') != f'bytes {size}-{end}/{item.size}' or len(r.content) != end-size+1:
                                raise ValueError('Unexpected range response: ' + str(r.headers.get('Content-Range')))
                            break
                        except Exception:
                            if attempt == 3:
                                raise
                            time.sleep(2**attempt)
                    f.write(r.content)
                    f.flush()
                    size = end+1
                    if size % (256*1024*1024) == 0 or size == item.size:
                        print('DOWNLOADED', item.rfilename, size, '/', item.size, flush=True)
            digest = hashlib.sha256(part.read_bytes()).hexdigest()
            if digest != expected:
                raise ValueError('Weight hash mismatch: ' + item.rfilename)
            part.replace(target)
        if target.stat().st_size != item.size:
            raise ValueError('Size mismatch: ' + item.rfilename)
        return {'file': item.rfilename, 'size': item.size, 'sha256': expected or hashlib.sha256(target.read_bytes()).hexdigest(), 'verified': True}

    with ThreadPoolExecutor(max_workers=3) as pool:
        verified = list(pool.map(download, files))
    (ROOT / 'sources/model_files.json').write_text(json.dumps(verified, indent=2))
    print('MODEL_DOWNLOAD_COMPLETE', flush=True)
