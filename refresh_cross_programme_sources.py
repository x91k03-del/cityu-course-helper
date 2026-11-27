"""Assess each saved course for every document-allowed programme, regardless of folder."""
import hashlib,json
from pathlib import Path
import project_runtime
from ma_timetable import parse_pdf
from programme_policy import policy
ROOT=Path(__file__).resolve().parent
def main():
    folder=ROOT/'data/degree-chain-policy/snapshot';old=json.loads((folder/'courses.json').read_text());p=policy()
    sources={(c['source_pdf'],c['term_code']) for c in old};out=[];seen=set()
    for path,term in sorted(sources):
      digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
      code=Path(path).stem.upper().removesuffix('_SEMB')
      for major in ['CM','CS']:
        if code not in p['allowlists'][major] and code not in p['GE_codes']:continue
        if (digest,term,major) in seen:continue
        seen.add((digest,term,major))
        c=parse_pdf(Path(path),term,major);c.update(programme=major,document_allowed=True);out.append(c)
    new=ROOT/'data/degree-chain-policy/snapshot_cross';new.mkdir(parents=True,exist_ok=True)
    (new/'courses.json').write_text(json.dumps(out,indent=2))
    (new/'policy.json').write_text((folder/'policy.json').read_text())
    active=ROOT/'data/active_timetable_evidence.json';v=json.loads(active.read_text());v.update(courses_dir='data/degree-chain-policy/snapshot_cross',policy_path='data/degree-chain-policy/snapshot_cross/policy.json',cross_folder_programme_assessment=True);active.write_text(json.dumps(v,indent=2))
    print('Cross-programme records',len(out),'CM',sum(c['programme']=='CM' for c in out),flush=True)
if __name__=='__main__':main()
