"""Reproduce report figures from saved experiment results; no model inference."""
import hashlib
import json
import os
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache' / 'matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

FIG = HERE / 'figures'
FIG.mkdir(exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                     'pdf.fonttype': 42, 'axes.spines.top': False,
                     'axes.spines.right': False})
navy, teal, grey = '#17324d', '#087f8c', '#566575'

fig, ax = plt.subplots(figsize=(5.5, 1.55))
ax.set(xlim=(0, 10), ylim=(0, 3)); ax.axis('off')
boxes = [
    (0.05, 1.8, 'Saved CityU sources\n+ fictional transcript'),
    (3.45, 1.8, 'Qwen3-8B + QLoRA\nsource-conditioned JSON'),
    (6.85, 1.8, 'Exact source/policy check\nreject or use lookup'),
    (6.85, 0.15, 'MILP / dependency path\nhard constraints + utility'),
    (3.45, 0.15, 'Explain output\nreward, blocks, assumptions'),
    (0.05, 0.15, 'User preference\nstream + three lambdas'),
]
for x, y, label in boxes:
    ax.add_patch(FancyBboxPatch((x, y), 3.0, 0.90, boxstyle='round,pad=0.04',
                               facecolor='#f0f5f8', edgecolor=navy, linewidth=0.9))
    ax.text(x+1.5, y+.45, label, ha='center', va='center', color=navy, fontsize=8.3)
for a, b in [((3.10,2.25),(3.37,2.25)), ((6.50,2.25),(6.77,2.25)),
             ((8.35,1.73),(8.35,1.10)), ((6.80,.60),(6.54,.60))]:
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=10,color=teal,lw=1.2))
ax.plot([1.55,1.55,7.85],[1.10,1.42,1.42],color=teal,lw=1.2)
ax.add_patch(FancyArrowPatch((7.85,1.42),(7.85,1.10),arrowstyle='-|>',
                            mutation_scale=10,color=teal,lw=1.2))
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
fig.savefig(FIG/'workflow.pdf'); plt.close(fig)

factor = json.loads((ROOT/'reports/dependency-experiment/factorial.json').read_text(encoding='utf-8'))
model = json.loads((ROOT/'reports/dependency-experiment/model_results.json').read_text(encoding='utf-8'))
expected = [r['result']['components']['stream_chain_bonus'] for r in factor['cases']]
observed = [r['raw_target_stream_bonus'] for r in model['results']]
assert expected == [2, 2, 2, 8] and observed == expected
fig, ax = plt.subplots(figsize=(5.5, 1.85))
x = list(range(4))
ax.bar(x, expected, width=.55, color=teal, label='Exact policy')
ax.scatter(x, observed, s=40, marker='D', facecolor='white', edgecolor=navy,
           zorder=3, label='Raw model')
for i, v in enumerate(expected): ax.text(i,v+.32,str(v),ha='center',color=navy,fontsize=9)
ax.set_xticks(x, ['Neither pass', 'CS3346 only', 'CS3356 only', 'Both passes'])
ax.set_ylabel('Target stream bonus')
ax.set_ylim(0, 10.5); ax.set_yticks([0, 2, 4, 6, 8, 10])
ax.grid(axis='y', alpha=.18); ax.set_axisbelow(True)
ax.legend(loc='upper left', frameon=False, ncol=2, fontsize=8)
ax.text(2.8, 9.7, 'Interaction = +6', ha='center', color=navy, fontsize=9)
fig.tight_layout(pad=.5); fig.savefig(FIG/'stream_interaction.pdf'); plt.close(fig)

style = Path('C:/Users/BILLY/Downloads/ge2340_project.sty')
shutil.copy2(style, HERE/style.name)
evidence = ['reports/programme-v6/release.json', 'reports/programme-v6/training.json',
            'reports/programme-v6/evaluation.json', 'reports/programme-v6/validation.json',
            'reports/desired-stream/summary.json', 'reports/desired-stream/generation_protocol.json',
            'reports/ge-pathway-lambda/controlled_sensitivity.json',
            'reports/ge-pathway-lambda/validation.json',
            'reports/dependency-experiment/protocol.json',
            'reports/dependency-experiment/paired_results.json',
            'reports/dependency-experiment/factorial.json',
            'reports/dependency-experiment/model_results.json',
            'reports/dependency-experiment/summary.json',
            'data/four_year_policy.json', 'data/active_programme_adapter.json']
manifest = {'template': {'path': 'GE_SEMA/Phase2_Template.tex',
                        'sha256': hashlib.sha256((ROOT/'GE_SEMA/Phase2_Template.tex').read_bytes()).hexdigest()},
            'style_sha256': hashlib.sha256(style.read_bytes()).hexdigest(),
            'evidence': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in evidence},
            'report_date': '2026-11-21', 'figure_builder_runs_model_training_or_inference': False,
            'model_base_revision': json.loads((ROOT/'reports/programme-v6/training.json').read_text(encoding='utf-8'))['model']['revision']}
(HERE/'evidence_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n',encoding='utf-8')
print('Created two vector figures, copied original course style, and recorded evidence hashes.')
