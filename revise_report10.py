"""Focused changes only: old introduction, audited PDF counts, cost-to-reward derivation."""
import hashlib,json,re,shutil,zipfile
from collections import Counter
from pathlib import Path
import project_runtime
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'GE_SEMA/Phase2_Report10'

def audit_sources():
    courses=json.loads((ROOT/'data/programme-v6/courses.json').read_text())
    rows=[json.loads(x) for x in (ROOT/'data/programme-v6/train.jsonl').read_text(encoding='utf-8').splitlines()]
    used=set();documents=Counter()
    for row in rows:
        task=row['task']
        if task not in ('course_rules','section','source_excerpt'):continue
        query=json.loads(row['messages'][1]['content'])
        if task=='source_excerpt':documents[query['source_document']]+=1;continue
        fields=query['source_rules' if task=='course_rules' else 'source_section']
        used.update(c['source_sha256'] for c in courses if c['programme']==query['programme']
            and c['term_code']==fields['term_code'] and c['course_code']==fields['course_code'])
    imported=json.loads((ROOT/'reports/programme-v6/import.json').read_text())
    assert len(used)==82 and len(documents)==3
    return {'stage':'CM/CS programme fine-tuning, rather than a claim about every earlier checkpoint stage',
        'collected_distinct_timetable_PDFs':imported['deduplicated_timetable_files'],
        'successfully_parsed_timetable_PDFs':len({c['source_sha256'] for c in courses}),
        'quarantined_timetable_PDFs':imported['quarantined'],
        'timetable_PDF_sources_represented_in_training':len(used),
        'programme_PDF_sources_represented_in_training':len(documents),
        'total_PDF_sources_represented_in_this_training_split':len(used)+len(documents),
        'training_examples':len(rows),'programme_excerpt_counts':dict(documents),
        'training_source_PDF_hashes':sorted(used),
        'interpretation':'Extracted text/facts were converted to JSON examples; the language model did not ingest raw PDF files.',
        'training_file_sha256':hashlib.sha256((ROOT/'data/programme-v6/train.jsonl').read_bytes()).hexdigest()}

def main():
    import sys
    if (OUT/'Phase2_Report10.tex').exists() and '--refresh-draft' not in sys.argv:raise RuntimeError('Preserve existing report')
    OUT.mkdir(parents=True,exist_ok=True);previous=ROOT/'GE_SEMA/Phase2_Report09'
    old_path=ROOT/'GE_SEMA/Phase2_Report08.tex';old=old_path.read_text(encoding='utf-8')
    source=(previous/'Phase2_Report09.tex').read_text(encoding='utf-8')
    start=r'\section{Introduction \& Problem Recap}';end=r'\section{Data Collection \& Methodology}'
    old_intro=old[old.index(start):old.index(end)]
    source=source[:source.index(start)]+old_intro+source[source.index(end):]
    audit=audit_sources();(OUT/'PDF_source_audit.json').write_text(json.dumps(audit,indent=2))
    marker=r'\textbf{Model adaptation and prompts.}'
    pdf_text=r'''\textbf{PDFs used to teach Qwen.} The programme import collected 93 distinct timetable PDFs: 86 parsed successfully and seven were excluded. A split-level audit identifies 82 timetable PDFs and three programme PDFs represented in the 485 training examples: \textbf{85 PDF sources in this programme-training split}. The three programme sources are the CM course list, CS major requirements and CS suggested plan. We teach extracted text/facts as JSON examples, not raw PDF files. Earlier handbook, GE and study-path stages are outside this scoped count.

'''
    source=source.replace(marker,pdf_text+marker,1)
    # Move an unchanged paragraph to its natural results location, recovering
    # title-page space without rewriting unrelated prose.
    protocol_start=source.index(r'\textbf{Evaluation protocol.}')
    protocol_end=source.index(r'\newpage',protocol_start)
    protocol=source[protocol_start:protocol_end]
    source=source[:protocol_start]+source[protocol_end:]
    source=source.replace(r'\section{Results \& Evaluation}',r'\section{Results \& Evaluation}'+'\n'+protocol,1)
    source=source.replace(r'\maketitle',r'\maketitle'+'\n'+r'\vspace{-0.55in}',1)
    old_par=r'''\textbf{Reward and penalty function.} For semester course set $X$, the state $s$ records earlier passes, GE areas, year, credit progress and the selected stream. We maximise'''
    new_par=r'''\textbf{From the original penalty to net reward.} Our first draft minimised weighted penalty $P$ for binary course choices $x_i$. Introducing course reward $R_i(s)$ retains the same penalty as a deduction from profit:
\begin{align}
&\min_{\mathbf x\in\mathcal X}P(\mathbf x),\quad P(\mathbf x)=\sum_i x_i(\lambda_b b_i+\lambda_d d_i+\lambda_w w_i),\label{eq:originalpenalty}\\
&\max_{\mathbf x\in\mathcal X}\left[\sum_i x_iR_i(s)-P(\mathbf x)-O(\mathbf x,s)\right].\label{eq:rewardconversion}
\end{align}
Here $b,d,w$ denote background mismatch, difficulty and workload, with non-negative student-adjustable $\lambda$ weights. Higher cost lowers reward; degree constraints $\mathcal X$ remain binding. The simple loss is $L_0=P+O-\sum_i x_iR_i$; the expanded loss below is $L=-U$. Minimising each loss maximises its corresponding net reward. Penalty-only minimisation is a different objective, not a second hard constraint. Training cross-entropy remains separate.

\textbf{State-dependent reward function.} Expanding $R_i(s)$ into preparation, graduation and stream progress gives the implemented Markov-state utility. For selected courses $X$, we maximise'''
    if old_par not in source:raise ValueError('Reward paragraph changed unexpectedly')
    source=source.replace(old_par,new_par,1)
    # Compact the same workflow and local spacing; unrelated prose stays intact.
    source=source.replace(r'\section{Implementation Details}',r'\section{Implementation Details}'+'\n'+r'\begingroup\setlength{\parskip}{3pt}\setlength{\intextsep}{6pt}',1)
    marker=r'\newpage'+'\n'+r'\textbf{How we solve the optimisation problem.}'
    # Continue the unchanged component definitions/overload on the next
    # implementation page, keeping the restored derivation together.
    a=source.index('Base value $g$');b=source.index(marker,a)
    continuation=source[a:b]
    source=source[:a]+source[b:]
    source=source.replace(marker,r'\newpage'+'\n'+continuation+r'\textbf{How we solve the optimisation problem.}',1)
    source=source.replace(r'\section{Results \& Evaluation}',r'\endgroup'+'\n'+r'\section{Results \& Evaluation}',1)
    note_start=source.index('Twenty-five future credits still lack saved class details.')
    note_end=source.index(r'\newpage',note_start)
    note=source[note_start:note_end]
    source=source[:note_start]+source[note_end:]
    source=source.replace('All three repaired paths contain four distributional GE passes',note+'All three repaired paths contain four distributional GE passes',1)
    source=source.replace('figures/workflow_reward_optimizer.pdf','figures/workflow_reward_optimizer_compact.pdf',1)
    (OUT/'Phase2_Report10.tex').write_text(source,encoding='utf-8')
    for name in ['ge2340_project.sty','gpt_input_corrected.json','gpt_direct_corrected_raw.json','summary.json','protocol.json','comparison.json']:
        shutil.copy2(previous/name,OUT/name)
    (OUT/'figures').mkdir(exist_ok=True)
    shutil.copy2(previous/'figures/workflow_reward_optimizer.pdf',OUT/'figures/workflow_reward_optimizer.pdf')
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    c=canvas.Canvas(str(OUT/'figures/workflow_reward_optimizer_compact.pdf'),pagesize=(400,84))
    labels=[['GPT teacher','Reward policy','Course relations'],['Qwen reward model','8 settings, 26 links','Structured JSON'],
        ['Parameter checker','Schema and bounds','Rules stay fixed'],['External optimizer','Exact DP search','Path + certificate']]
    for i,lines in enumerate(labels):
        x=3+102*i;c.setFillColor(colors.HexColor('#edf4f6'));c.setStrokeColor(colors.HexColor('#5c7886'));c.roundRect(x,36,88,44,4,fill=1,stroke=1)
        c.setFillColor(colors.HexColor('#173d50'))
        for j,line in enumerate(lines):c.setFont('Helvetica-Bold' if j==0 else 'Helvetica',8);c.drawCentredString(x+44,67-11*j,line)
        if i<3:
            c.line(x+88,58,x+101,58);c.line(x+101,58,x+97,61);c.line(x+101,58,x+97,55)
    c.setFont('Helvetica',8);c.drawCentredString(200,20,'Human review and retraining follow evaluation.')
    c.drawCentredString(200,7,'Student records and official course facts constrain the optimizer.');c.save()
    # Content elsewhere is preserved: only two additions, one replacement,
    # the requested introduction and an unchanged paragraph relocation.
    new_intro=source[source.index(start):source.index(end)]
    assert new_intro==old_intro
    manifest={'base_report':'Phase2_Report09','introduction_restored_from':'Phase2_Report08',
        'old_introduction_preserved_verbatim':True,'PDF_training_source_count':85,
        'changes':['Restore the old introduction exactly','Add audited collected/parsed/training PDF counts',
            'Show original penalty and its conversion into net reward','Relocate unchanged evaluation protocol to Results',
            'Compact the workflow and local layout to retain the template page limit'],
        'latest_GPT_comparison_preserved':True,'old_three_lambda_penalty_restored':True,
        'current_Years1_to3_and_Year4_overload_rule_preserved':True,
        'prior_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [old_path,previous/'Phase2_Report09.tex',previous/'Phase2_Report09.pdf']}}
    (OUT/'revision_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(OUT/'Phase2_Report10.tex')

if __name__=='__main__':main()
