"""Show three illustrative paired-model examples in both comparison tables."""
import hashlib,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output/pdf/phase2-report08'
def main():
    previous=ROOT/'GE_SEMA/Phase2_Report07.tex';target=ROOT/'GE_SEMA/Phase2_Report08.tex'
    if target.exists():raise RuntimeError('Preserve the existing revision.')
    s=previous.read_text(encoding='utf-8');keep={'CM1','CM2','CS2'}
    for label,pattern in [('tab:retest-input07',r'\\textbf\{(CM\d|CS\d);'),('tab:retest-path07',r'\\raggedright (CM\d|CS\d)\\par')]:
        marker=s.index(r'\label{'+label+'}')
        start=s.index(r'\endlastfoot',marker)+len(r'\endlastfoot')
        end=s.index(r'\end{longtable}',start)
        chunks=s[start:end].strip().split(r'\addlinespace[4pt]')
        selected=[]
        for chunk in chunks:
            match=re.search(pattern,chunk)
            if match and match[1] in keep:selected.append(chunk.strip())
        assert len(selected)==3,(label,len(selected))
        s=s[:start]+'\n'+('\n'+r'\addlinespace[4pt]'+'\n').join(selected)+'\n'+s[end:]
    start=s.index(r'\textbf{Updated Qwen--GPT comparison of timetable outputs.}')
    end=s.index(r'\textbf{Completed-course bases',start)
    intro=r'''\textbf{Updated Qwen--GPT comparison of timetable outputs.} We show three illustrative examples from the eight-scenario rerun: a CM finance profile with Analysis passed (CM1), its matched profile without Analysis (CM2), and a CS AI profile without CS3342 (CS2). Both models receive identical completed courses, updated rewards, stream rules and snapshot options, without seeing each other's output or the Markov reference. GPT uses the requested GPT-6.1 Sol agent configuration; Qwen uses its deployed timetable checkpoint with the checked GPT-teacher reward graph.

The inputs are synthetic end-of-Year-2 histories for a Year-3 Semester-A workload task. Only captured Semester-A term 202609 options are used; these scenarios do not certify future-year offerings. Table~\ref{tab:retest-input07} compares raw course sets; Table~\ref{tab:retest-path07} compares later academic paths. Meeting times are omitted.

'''
    s=s[:start]+intro+s[end:]
    start=s.index('Across eight scenarios, Qwen returns')
    end=s.index('{\\small',start)
    s=s[:start]+'''In the complete eight-scenario rerun, Qwen returns 4/8 valid answers and GPT returns 8/8, including correct infeasibility answers. The tables show only three illustrative cases; these selected examples do not replace the full-study totals. Qwen's valid CM1 schedule is 3.401 utility points below the reference.

'''+s[end:]
    start=s.index('With Analysis passed (CM1), GPT selects MA4542;')
    end=s.index(r'\newpage',start)
    s=s[:start]+r'''CM1 and CM2 differ only in the Analysis pass. GPT changes MA4542 to MA4545 and identifies MA3526 recovery. Qwen proposes an unsupported EF3320 option in CM2. In CS2, Qwen returns only three courses with a clash, while GPT correctly reports an infeasible source pool and identifies CS3342 recovery.

The later-path explanations are preserved as generated. Qwen's CM1 sentence omits a second finance-option requirement, and CS2 treats the bridge course CS3342 as an AI core slot and assigns an unverified future semester. No explanation certifies stream completion or future offerings. Invalid raw timetables trigger the application's validated Markov fallback.

'''+s[end:]
    target.write_text(s,encoding='utf-8');OUT.mkdir(parents=True,exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
    shutil.copy2(target,OUT/target.name)
    for f in ['ge2340_project.sty','figures/workflow_training07.pdf','figures/stream_interaction.pdf']:shutil.copy2(ROOT/'GE_SEMA'/f,OUT/f)
    manifest={'previous_tex_sha256':hashlib.sha256(previous.read_bytes()).hexdigest(),
      'previous_pdf_sha256':hashlib.sha256((ROOT/'GE_SEMA/Phase2_Report07.pdf').read_bytes()).hexdigest(),
      'displayed_examples':['CM1','CM2','CS2'],'rows_per_comparison_table':3,'full_benchmark_size':8,
      'benchmark_results_changed':False,'previous_report_overwritten':False}
    (OUT/'revision_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(target)
if __name__=='__main__':main()
