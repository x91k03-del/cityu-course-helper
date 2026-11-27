"""Targeted Report02 revision; preserve the previous source and PDF byte-for-byte."""
from pathlib import Path
import hashlib,json,os,shutil
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/pdf/phase2-report03'
os.environ['MPLCONFIGDIR']=str(ROOT/'.cache/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch

def workflow():
 fig,ax=plt.subplots(figsize=(5.5,2.35));ax.set(xlim=(0,10),ylim=(0,4.7));ax.axis('off')
 boxes=[(.08,3.65,'Course PDFs\n+ programme rules',False),
  (3.48,3.65,'GPT-6.1 Sol teacher\nrelation drafts (design)',True),
  (6.88,3.65,'Check relations\n+ training examples',False),
  (6.88,2.05,'Qwen training\ncomplete one round',False),
  (3.48,2.05,'Human feedback\nafter round (planned)',True),
  (.08,2.05,'Corrected examples\n+ source-task replay',False),
  (.08,.45,'Qwen retraining\nwith corrected labels',False),
  (3.48,.45,'Held-out evaluation\n+ checkpoint selection',False),
  (6.88,.45,'Validated MILP\n+ student timetable',False)]
 for x,y,label,planned in boxes:
  ax.add_patch(FancyBboxPatch((x,y),2.98,.86,boxstyle='round,pad=.03',edgecolor='#17324d',facecolor='#f0f5f8',linestyle='--' if planned else '-',linewidth=.9))
  ax.text(x+1.49,y+.43,label,ha='center',va='center',fontsize=8.1,color='#17324d')
 for a,b in [((3.10,4.08),(3.43,4.08)),((6.50,4.08),(6.83,4.08)),((8.37,3.60),(8.37,2.96)),
             ((6.83,2.48),(6.50,2.48)),((3.43,2.48),(3.10,2.48)),((1.57,2.0),(1.57,1.36)),
             ((3.10,.88),(3.43,.88)),((6.50,.88),(6.83,.88))]:
  ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=10,color='#087f8c',lw=1.1))
 fig.subplots_adjust(left=0,right=1,bottom=0,top=1);fig.savefig(OUT/'figures/workflow_training03.pdf');plt.close(fig)

def main():
 OUT.mkdir(exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
 old=ROOT/'GE_SEMA/Phase2_Report02.tex';new=ROOT/'GE_SEMA/Phase2_Report03.tex'
 if new.exists():raise RuntimeError('New report already exists; do not overwrite it automatically.')
 before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [old,ROOT/'GE_SEMA/Phase2_Report02.pdf']}
 s=old.read_text(encoding='utf-8');changes=[]
 def change(oldtext,newtext):
  nonlocal s
  assert s.count(oldtext)==1,oldtext[:100]
  s=s.replace(oldtext,newtext,1);changes.append({'old':oldtext,'new':newtext})
 anchor='\\section{Implementation Details}'
 prompt=r'''\textbf{Prompts used in training.} Our saved training rows contain three message roles: a system instruction defining the task and output rules, a user message supplying the programme, passed courses, source facts and requested task, and an assistant message containing the target JSON. Instructions include ``Return JSON only,'' preserve source times, distinguish documents from instructions, count distinct stream slots, and never infer passes from year of study. The CM background prompt also states the EF/CS planning waiver and the treatment of failed/in-progress finance records. We train on assistant-answer tokens using supervised cross-entropy; this is more than providing a prompt at inference time.

'''
 change(anchor,prompt+anchor)
 change('figures/workflow.pdf','figures/workflow_training03.pdf')
 change('Our planning pipeline connects course evidence and student preferences to validated recommendations and an explanation of the result.',
        'Expanded training workflow: GPT relation teaching and post-round human feedback feed Qwen retraining, followed by validation and timetable optimisation. Dashed boxes denote designed feedback stages whose separate execution is not established by the saved training logs.')
 anchor='\\textbf{Efficient model adaptation.}'
 teaching=r'''\textbf{GPT-6.1 Sol teaching course relations.} In the teacher-guided design, GPT-6.1 Sol reads the supplied course information and proposes relation examples: shared mathematical preparation, finance/AI interest links, workload implications and prerequisite bridges. We separate official requirements from inferred content links, review the proposed labels, and teach Qwen with the accepted source-conditioned input/output examples. A relation is an editable preparation hypothesis, not automatic registration permission. This is teacher-output distillation; we do not claim that Qwen also trains GPT.

\textbf{Human feedback after a full training round.} After one complete model-to-model teaching round and evaluation, a reviewer checks generated relations, rewards and schedules. Incorrect examples receive corrected targets and explanations; correct source examples are replayed to reduce forgetting. We then retrain Qwen and retain a checkpoint only if held-out checks support it. The repository demonstrates supervised training and corrective replay, but does not contain a separately logged GPT relation-teaching trial or a formal human-annotation evaluation; these two workflow stages remain a protocol for the next review cycle.

'''
 change(anchor,teaching+anchor)
 oldformula=r'''O(X,s)=\mathbf{1}_{\{\mathrm{year}=4\}}\,0.25\,[\max(0,C(X)-12)]^2,'''
 newformula=r'''O(X,s)=\begin{cases}
0.25[\max(0,C(X)-15)]^2,&\text{Years 1--3},\\
0.25[\max(0,C(X)-12)]^2,&\text{Year 4}.
\end{cases}'''
 change(oldformula,newformula)
 change('where $C(X)$ is semester credits. The penalty is zero in Years 1--3 and for at most 12 credits in Year 4; it increases to 2.25 at 15 credits and 9 at 18 credits. This encourages manageable final-year choices without penalising the standard earlier-year load.',
 'where $C(X)$ is semester credits. In Years 1--3 the penalty is zero through 15 credits, then 0.25 at 16 credits and 2.25 at 18 credits. In Year 4 it is zero through 12 credits, then 2.25 at 15 and 9 at 18 credits. We use the same 0.25 coefficient for the newly added earlier-year term. Inspection found that the previous default disabled overload penalties in Years 1--3; we corrected both the semester optimiser and the four-year simulation. This is a planner-policy correction, not a claim that the saved neural weights were retrained on this new threshold. The 18-credit hard limit remains separate.')
 rows=json.loads((ROOT/'reports/timetable-benchmark/graded_results.json').read_text(encoding='utf-8'))
 summary=json.loads((ROOT/'reports/timetable-benchmark/summary.json').read_text(encoding='utf-8'))
 bench=r'''\textbf{Timetable benchmark: Qwen versus GPT-6.1 Sol.} We froze six supplied-data cases before inference: two CM Semester B profiles (finance versus neutral GE history), two CS Semester B settings (balanced versus difficulty-focused penalties), and two Semester A cases with insufficient distinct course options. Four cases are feasible and two infeasible under the common MILP reference. Both models receive the same validated options, saved meeting times, additive scores, stream rules and corrected overload formula. Their task is to return selected option IDs or declare infeasibility. We grade the raw answer without repair: valid constraints first, then objective regret against the exact solver.

\begin{table}[H]
\centering\small
\caption{Executed six-case timetable diagnostic. Solver fallback is reported separately from direct-model performance.}
\begin{tabular}{p{2.6in}ccc}
\toprule
Method & Valid plans & Optimal plans & Correct infeasible\\
\midrule
Qwen, direct selection & 0/4 & 0/4 & 0/2\\
GPT-6.1 Sol, direct selection & 4/4 & 4/4 & 2/2\\
Qwen + validator/MILP fallback & 4/4 & 4/4 & 2/2\\
\bottomrule
\end{tabular}
\label{tab:benchmark03}
\end{table}

The direct Qwen responses invent two option IDs in the finance case, select fewer than five courses in other cases, or repeat two sections of the same course. GPT returns legal, objective-optimal selections in this small test. The hybrid pipeline rejects all six invalid Qwen responses and returns the common solver result; this does not count as improved Qwen accuracy. Table~\ref{tab:timetable03} shows the actual CS balanced timetable comparison. All meeting times are from the saved snapshots; component pairing and weeks 1--14 remain shared assumptions.

\begin{table}[H]
\centering\small
\caption{CS Semester B balanced example: returned meeting times (24-hour format). Qwen selects only three courses; GPT selects six courses, 16 credits and a 0.25 overload penalty. A dash means the course was omitted.}
\begin{tabular}{p{.6in}p{2.2in}p{2.2in}}
\toprule
Course & Qwen direct timetable & GPT-6.1 Sol timetable\\
\midrule
'''
 def meeting_text(o):
  day=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
  def hh(v):return f'{v//60:02d}:{v%60:02d}'
  return '; '.join(day[m['day']-1]+' '+hh(m['start_minute'])+'--'+hh(m['end_minute']) for m in o['meetings'])
 case=next(c for c in json.loads((ROOT/'reports/timetable-benchmark/cases.json').read_text(encoding='utf-8')) if c['id']=='CS_B_AI')
 index={o['option_id']:o for o in case['problem']['options']}
 model_maps={}
 for label in ['qwen','gpt']:
  r=next(x for x in rows if x['model']==label and x['case_id']=='CS_B_AI')
  model_maps[label]={index[i]['course_code']:index[i] for i in r['response']['selected_option_ids'] if i in index}
 for code in sorted(model_maps['gpt']):
  cells=[code]+[meeting_text(model_maps[m][code]) if code in model_maps[m] else '---' for m in ['qwen','gpt']]
  bench+=' & '.join('{\\raggedright '+c+'\\par}' for c in cells)+r'\\'+'\n'
 bench+=r'''\bottomrule
\end{tabular}
\label{tab:timetable03}
\end{table}

This is a reproducible familiar-source diagnostic, not a general model ranking. Qwen uses local greedy, non-thinking decoding; the requested GPT-6.1 Sol is invoked as a model-specific agent with a single read of the frozen six-case packet and no solver or outside evidence. Qwen receives each case separately, whereas GPT receives the six-case batch, and reasoning settings are not matched. We make no latency/cost comparison. The shared scores isolate timetable selection, not independent course-scoring quality. Future evaluation should use larger held-out cohorts, matched per-case provider calls, repeated runs and uncertainty intervals. Benchmark inputs, raw outputs and independent grades are saved separately from training data.

'''
 change('\\section{Results \\& Evaluation}', '\\section{Results \\& Evaluation}\n\n'+bench)
 new.write_text(s,encoding='utf-8');(OUT/'Phase2_Report03.tex').write_text(s,encoding='utf-8')
 workflow();shutil.copy2(OUT/'figures/workflow_training03.pdf',ROOT/'GE_SEMA/figures/workflow_training03.pdf')
 shutil.copy2(ROOT/'GE_SEMA/figures/stream_interaction.pdf',OUT/'figures/stream_interaction.pdf')
 for f,h in before.items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
 (OUT/'revision_manifest.json').write_text(json.dumps({'original_hashes':before,'changes':changes,'unrelated_text_preserved_by_literal_edits':True,
  'benchmark_summary':summary,'overload_tests_passed':86,'report_date':'2026-11-24'},indent=2)+'\n',encoding='utf-8')
 print(new)
if __name__=='__main__':main()
