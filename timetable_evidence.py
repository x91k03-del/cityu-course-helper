"""Verify that a timetable record still matches a file in the supplied folders."""
import hashlib
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parent

@lru_cache(maxsize=256)
def _digest(path,size,mtime):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verified(record):
    path=(ROOT/Path(record['source_pdf'])).resolve()
    roots=[(ROOT/'GE_SEMA/MA').resolve(),(ROOT/'GE_SEMA/CS').resolve()]
    if not any(path.is_relative_to(root) for root in roots) or not path.is_file():return False
    stat=path.stat()
    return _digest(str(path),stat.st_size,stat.st_mtime_ns)==record.get('source_sha256')
