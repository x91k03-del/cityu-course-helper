"""Verify the released current adapter without loading a GPU model."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/active_objective_parameter_adapter.json').read_text())
file=ROOT/manifest['adapter']/'adapter_model.safetensors'
assert manifest['role']=='objective_parameters_only' and manifest['accepted_for_activation']
assert hashlib.sha256(file.read_bytes()).hexdigest()==manifest['sha256']
print('Current checkpoint verified:',manifest['adapter'])
print('SHA-256:',manifest['sha256'])
