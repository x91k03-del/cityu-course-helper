"""New report revision with frozen updated-reward Qwen/GPT timetable comparison."""
import hashlib,json,re,shutil
from pathlib import Path
import project_runtime
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'reports/timetable-retest07';OUT=ROOT/'output/pdf/phase2-report07'
def esc(s):
    for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:s=s.replace(a,b)
    return s
def cell(s):return r'{\raggedright '+s+r'\par}'
def table(caption,label,widths,headings,rows):
    header=' & '.join(headings)+r'\\'
    body='\n'.join(' & '.join(cell(v) for v in row)+r'\\'+'\n\\addlinespace[4pt]' for row in rows)
    return r'''{\small
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.12}
\begin{longtable}{'''+widths+r'''}
\caption{'''+caption+r'''}\label{'''+label+r'''}\\
\toprule
'''+header+r'''
\midrule
\endfirsthead
\multicolumn{3}{l}{\textit{Continued}}\\
\toprule
'''+header+r'''
\midrule
\endhead
\midrule
\multicolumn{3}{r}{\textit{Continued on next page}}\\
\endfoot
\bottomrule
\endlastfoot
'''+body+'\n\\end{longtable}\n}\n\n'

def workflow():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    fig,ax=plt.subplots(figsize=(9,3.4));ax.set_xlim(0,10);ax.set_ylim(0,4);ax.axis('off')
    nodes=[(.1,2.5,'Student profile\nand preferences'),(2.65,2.5,'Saved course\nevidence'),(5.2,2.5,'Qwen structured\nproposal'),(7.75,2.5,'Markov search\nand validation'),(.1,.5,'GPT-authored\nrelation examples'),(2.65,.5,'Supervised Qwen\ndistillation'),(5.2,.5,'Corrective replay\nand held-out checks'),(7.75,.5,'Human feedback\n(review protocol)')]
    for x,y,t in nodes:
        ax.add_patch(FancyBboxPatch((x,y),2.1,1,boxstyle='round,pad=.08',facecolor='#edf4f7',edgecolor='#446575',linestyle='--' if x>7 and y<1 else '-'))
        ax.text(x+1.05,y+.5,t,ha='center',va='center',fontsize=9)
    for x in [.1,2.65,5.2]:ax.annotate('',xy=(x+2.5,3),xytext=(x+2.2,3),arrowprops={'arrowstyle':'->','color':'#446575'})
    for x in [.1,2.65]:ax.annotate('',xy=(x+2.5,1),xytext=(x+2.2,1),arrowprops={'arrowstyle':'->','color':'#446575'})
    ax.annotate('',xy=(6.25,2.4),xytext=(6.25,1.6),arrowprops={'arrowstyle':'->','color':'#446575'})
    fig.savefig(ROOT/'GE_SEMA/figures/workflow_training07.pdf',bbox_inches='tight');plt.close(fig)

def build():
    new=ROOT/'GE_SEMA/Phase2_Report07.tex'
    if new.exists():raise RuntimeError('Preserve the existing revision.')
    old=ROOT/'GE_SEMA/Phase2_Report06.tex';text=old.read_text(encoding='utf-8')
    cases=json.loads((DATA/'cases.json').read_text());results=json.loads((DATA/'comparison.json').read_text());summary=json.loads((DATA/'summary.json').read_text())
    labels=['CM1','CM2','CM3','CS1','CS2','CS3','CM4','CM5']
    start=text.index(r'\textbf{Year 2 profiles and Year 3 Semester A decisions.}')
    end=text.index(r'\textbf{Three penalties give students meaningful control.}',start)
    block=r'''\textbf{Updated Qwen--GPT comparison of timetable outputs.} We repeated the comparison after updating the GPT-authored preparation rewards. Eight synthetic end-of-Year-2 profiles are given a Year-3 Semester-A workload task: six familiar profiles and two additional missing-mathematics controls. Both models receive the same completed courses, exact snapshot option IDs, additive rewards, stream definitions and constraints. Neither sees the other model's output or the Markov reference. The GPT comparator is a separate agent configured as GPT-6.1 Sol; its provider-specific runtime revision is not exposed. Qwen uses the deployed timetable checkpoint and the updated preparation rewards; the separately trained relation checkpoint supplies the advisory reward policy.

The comparison uses the captured Semester-A term 202609 as a controlled workload scenario. It does not move those offerings into Semester A 2027 or certify a real future timetable. Table~\ref{tab:retest-input07} gives the complete profile and raw course selections. Table~\ref{tab:retest-path07} records the models' later academic-path explanations. Meeting times are checked for clashes but are omitted from the report tables.

'''
    rows=[]
    for label,c,r in zip(labels,cases,results):
        p=c['profile'];profile=r'\textbf{'+label+'; '+p['programme']+r'.} Passed: '+', '.join(p['completed_courses'])+r'. \textit{Preference:} '+p['desired_stream']+'.'
        outputs=[];known={o['option_id'] for o in c['problem']['options']}
        for name in ['qwen','gpt']:
            ans=r[name]['raw_answer']
            if ans['status']=='infeasible':s='No feasible five-course plan in supplied pool'
            else:s=', '.join(i.split(':')[0]+(r'$^{\dagger}$' if i not in known else '') for i in ans.get('selected_option_ids',[]))
            if not r[name]['accepted']:s+=r'. \textit{Rejected by validation.}'
            outputs.append(s)
        rows.append([profile,*outputs])
    block+=table('Completed Year 2 profiles and raw Year 3 Semester-A workload selections under the updated rewards.','tab:retest-input07',
        'p{2.45in}p{1.35in}p{1.35in}', ['Year 2 completed-course profile','Fine-tuned Qwen','GPT-6.1 Sol'],rows)
    block+=r'''\noindent\footnotesize $\dagger$ denotes an option ID absent from the supplied pool. Rejected outputs are displayed as generated; no planner repair is substituted into a model column. Every input is a Year 2 profile. The resulting course sets are snapshot-based Year 3 workload scenarios, not future registration approvals.\normalsize

'''
    block+=f"Across eight scenarios, Qwen returns {summary['qwen']['accepted']}/8 valid answers and GPT returns {summary['gpt']['accepted']}/8. Four scenarios admit a legal schedule: Qwen provides three valid schedules, of which two maximise the configured reward; GPT provides four, all matching the reference reward. Of four infeasible scenarios, Qwen identifies one and GPT identifies all four. Qwen's valid CM1 selection is 3.401 utility points below the reference. These small, source-conditioned tests do not establish unseen-cohort performance.\n\n"
    block+=r'\newpage'+'\n'
    rows=[[label,esc(r['qwen']['raw_answer']['future_path']),esc(r['gpt']['raw_answer']['future_path'])] for label,r in zip(labels,results)]
    block+=table('How the supplied histories and stream preferences affect the models\textquotesingle\ later academic-path explanations.','tab:retest-path07',
        'p{0.45in}p{2.35in}p{2.35in}',['Profile','Qwen: returned later path','GPT-6.1 Sol: returned later path'],rows)
    block+=r'''With Analysis passed (CM1), GPT selects MA4542; without it (CM2), GPT selects MA4545 and explicitly identifies recovery of MA3526. Changing the same completed profile to Enriched Mathematics (CM3) changes GPT's immediate choice from MA3521 to MA4545. Removing Probability and Statistics (CM4) leaves only four eligible subjects, so both models correctly report an incomplete source pool; GPT also identifies MA2510 recovery. Removing Linear Algebra (CM5) leaves a feasible five-course set but changes the later recovery advice.

Qwen's explanations remain advisory. Its CM1 sentence omits a second finance-option requirement, CM5 incorrectly treats foundation/introductory courses as sufficient stream completion, and CS2 describes CS3342 as an AI core slot. CS3342 is a bridge course here, not an AI stream requirement. Qwen also assigns unverified future semesters in some explanations. The table preserves these errors; no later path certifies completion, prerequisites or future offerings. The application validates timetable proposals and uses the Markov planner when a raw answer fails its hard constraints.

'''
    text=text[:start]+block+text[end:]
    text=text.replace('figures/workflow_training03.pdf','figures/workflow_training07.pdf')
    cap_start=text.index(r'\caption{Expanded training workflow:');cap_end=text.index('\n',cap_start)
    text=text[:cap_start]+r'\caption{Logged GPT-authored relation teaching, Qwen distillation and corrective replay feed source-based validation. Human feedback remains a separate review protocol.}'+text[cap_end:]
    s=text.index(r'\textbf{GPT-6.1 Sol teaching course relations.}');e=text.index(r'\end{samepage}',s)
    text=text[:s]+r'''\textbf{GPT teaching course relations.} The GPT assistant authored 26 directed preparation hypotheses using saved course aims, existing syllabus evidence and official catalogue descriptions. These are editable utility assumptions, rather than statistical correlations or measured workload reductions. Examples include MA2510 $\rightarrow$ MA3518 ($+0.30$), MA2503 $\rightarrow$ CS4487 ($+0.25$), MA3515 $\rightarrow$ EF3320 ($+0.25$), and finance GE $\rightarrow$ EF3320 ($+0.10$). The reward uses the strongest direct passed-source edge per target, capped at 0.35; it does not sum overlapping benefits, recurse through unstudied courses or award same-semester transfer. We distinguish this GPT-authored teacher from the separate GPT-6.1 Sol timetable comparator.

We distilled the policy into a separate Qwen relation checkpoint with 149 training and 20 validation examples over two epochs. Source-conditioned held-out checks improved from 17/20 to 20/20. A fresh three-source probe incorrectly summed three 0.25 benefits to 0.75; validation kept the correct 0.25. An 82-example corrective pass taught the maximum rule across passed-course combinations, fixed that familiar probe and retained 20/20 on the unchanged held-out set. The planner applies the checked policy, so neural arithmetic cannot inflate its reward.

'''+text[e:]
    text=text.replace('but does not contain a separately logged GPT relation-teaching trial or a formal human-annotation evaluation; these two workflow stages remain a protocol for the next review cycle.',
        'now includes logged GPT-authored relation distillation and corrective trials. A formal human-annotation evaluation remains a protocol for the next review cycle.')
    text=text.replace("The optimiser uses SciPy's mixed-integer linear programming interface\\citep{scipy}.",
        'The current planner uses deterministic Markov subset search over section bundles, with STOP unavailable below five credit-bearing courses in Years 1--3. It reports optimality only for unpruned searches; bounded searches report feasible output or search exhaustion. The earlier MILP implementation remains a reference baseline\\citep{scipy}.')
    text=text.replace('During the first round of training, we used GPT-6.1 Sol to deduce the relation between course and course.',
        'We use the logged GPT-authored content relationships to update preparation rewards.')
    text=text.replace('Pass MA2503; conceptual finance link & EF3320 & No preparation bonus from this link',
        'Pass MA2503; portfolio mathematics & EF3320 & GPT preparation reward $+0.20$')
    text=text.replace('An end-to-end schedule intervention remains future work, because a reward change does not necessarily change the best feasible timetable.',
        'A new saved-timetable intervention changes the CM finance profile with Analysis passed: MA4542 replaces MA4545, and net utility rises from 35.661 to 36.681 when only the preparation graph changes. The profile without Analysis keeps its selection. Thus a reward change can alter a close choice, while source constraints and stronger preferences can keep another timetable unchanged.')
    text=text.replace('In one document-filtered CM four-year simulation, the plan reaches 124 credits and completes a stream under the encoded requirements.',
        'Earlier curriculum-only CM simulations reach 124 or 127 credits under their encoded category rules. They do not establish actual timetable feasibility. Under the current literal MA/CS-only source pool, the entering Year 1 profile has only MA1300 and MA2509 eligible and cannot form a five-course semester; its graduation audit remains incomplete.')
    text=text.replace('Source checks keep these preferences connected to programme requirements.',
        'Source checks keep these preferences connected to programme requirements. EF courses without finance-study evidence also incur an extra $1.5\\lambda_b$ mismatch cost; finance preparation removes that extra cost, while section permission remains binding.')
    text=text.replace('Later profile failures identify where model reasoning still needs improvement.',
        'The updated eight-scenario timetable comparison accepts four raw Qwen answers and eight GPT answers; explicit source validation exposes unsupported sections, insufficient loads and clashes.')
    new.write_text(text,encoding='utf-8');OUT.mkdir(parents=True,exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
    workflow()
    for f in ['ge2340_project.sty','figures/workflow_training07.pdf','figures/stream_interaction.pdf']:
        shutil.copy2(ROOT/'GE_SEMA'/f,OUT/f)
    shutil.copy2(new,OUT/new.name)
    (OUT/'revision_manifest.json').write_text(json.dumps({'previous_tex_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
      'previous_pdf_sha256':hashlib.sha256((ROOT/'GE_SEMA/Phase2_Report06.pdf').read_bytes()).hexdigest(),
      'new_comparison_inputs_sha256':hashlib.sha256((DATA/'cases.json').read_bytes()).hexdigest(),
      'new_profiles':8,'previous_report_overwritten':False,'sections_updated':['model comparison','GPT reward teaching','current planner','degree evidence scope'],
      'summary':summary},indent=2)+'\n')
    print(new)
if __name__=='__main__':build()
