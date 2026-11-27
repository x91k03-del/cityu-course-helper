"""One student-profile/path table, using the existing blinded model outputs."""
from pathlib import Path
from collections import Counter
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output/pdf/phase2-report05'
def main():
 old=ROOT/'GE_SEMA/Phase2_Report04.tex';new=ROOT/'GE_SEMA/Phase2_Report05.tex'
 if new.exists():raise RuntimeError('Preserve the existing new revision.')
 original=old.read_text(encoding='utf-8');start=original.index('\\textbf{Timetable outputs: fine-tuned Qwen versus GPT-6.1 Sol.}')
 end=original.index('\\textbf{Three penalties give students meaningful control.}',start)
 data=ROOT/'reports/timetable-comparison04';cases=json.loads((data/'cases.json').read_text(encoding='utf-8'))
 outputs={}
 for model in ['qwen','gpt']:
  outputs[model]={}
  for r in json.loads((data/(model+'_raw.json')).read_text(encoding='utf-8')):
   outputs[model][r['case_id']]=json.loads(r['raw']) if 'raw' in r else r
 profiles={
 'CM_B_finance':r'Year 2 CM; finance GE (GE2260) passed.',
 'CM_B_no_finance':r'Year 2 CM; non-finance GE; Enriched Mathematics inferred.',
 'CS_B_AI':r'Year 2 CS; AI GE (GE2340) passed; AI interest.',
 'CS_B_difficulty':r'Year 2 CS; AI interest; higher difficulty weight ($\lambda_d=20$).',
 'CM_A_missing_options':r'Year 2 CM; finance interest; Semester A candidates.',
 'CS_A_missing_options':r'Year 2 CS; AI interest; Semester A candidates.',
 'CM_early_analysis':r'Year 2 CM; finance GE and Analysis (MA3526) passed.',
 'CM_calculus_not_passed':r'Year 2 CM; finance GE passed; MA2508 not passed.',
 'CM_final_year':r'Year 4 CM; finance interest; unfinished core courses.',
 'CM_enriched_despite_finance_GE':r'Year 2 CM; finance GE passed; explicitly prefers Enriched Mathematics.',
 'CS_data_science':r'Year 2 CS; AI GE passed; explicitly prefers Data Science.',
 'CS_missing_programming':r'Year 2 CS; AI interest; CS2310 not passed.',
 'CS_workload_priority':r'Year 2 CS; AI interest; higher workload weight ($\lambda_w=20$).',
 'CS_final_year':r'Year 4 CS; AI interest; unfinished core courses.'}
 block=r'''\textbf{Blind comparison of selected course paths.} We tested 14 fictional student profiles. Neither model was shown the other model's answer or the reference solution. Both received the same profile-specific course data and rules. Table~\ref{tab:paths05} lists every student's profile and the original course selection returned by fine-tuned Qwen and GPT-6.1 Sol, without meeting times or corrected outputs. Here, ``path'' means the selected next-semester courses, not a verified full-degree sequence. This is answer-blinded testing over familiar course information, rather than unseen-document validation.

{\small
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.12}
\begin{longtable}{p{1.67in}p{1.75in}p{1.75in}}
\caption{Student profiles and course paths returned in the blind output comparison.}\label{tab:paths05}\\
\toprule
Student profile & Fine-tuned Qwen selected path & GPT-6.1 Sol selected path\\
\midrule
\endfirsthead
\multicolumn{3}{l}{\textit{Student profiles and selected paths (continued)}}\\
\toprule
Student profile & Fine-tuned Qwen selected path & GPT-6.1 Sol selected path\\
\midrule
\endhead
\midrule
\multicolumn{3}{r}{\textit{Continued on next page}}\\
\endfoot
\bottomrule
\endlastfoot
'''
 evidence=[]
 def cell(s):return '{\\raggedright '+s+'\\par}'
 for c in cases:
  known={o['id'] for o in c['query']['options']};results=[]
  for model in ['qwen','gpt']:
   response=outputs[model][c['id']]
   if response['status']=='infeasible':text='No feasible selection returned'
   else:
    ids=response['selected_option_ids'];codes=[i.split(':')[0] for i in ids];counts=Counter(codes);parts=[]
    for code in dict.fromkeys(codes):
     part=code
     if any(i not in known for i in ids if i.split(':')[0]==code):part+=r'$^{\dagger}$'
     if counts[code]>1:part+=r' ($\times'+str(counts[code])+'$ sections)'
     parts.append(part)
    text=', '.join(parts) if parts else 'No courses returned'
   results.append(text)
  block+=' & '.join(cell(v) for v in [profiles[c['id']],*results])+r'\\'+'\n'
  evidence.append({'case_id':c['id'],'student':profiles[c['id']],'qwen_path':results[0],'gpt_path':results[1]})
 block+=r'''\end{longtable}
}
\noindent\footnotesize $\dagger$ A returned section ID was outside the supplied candidate set; its course code is shown as generated. Repeated sections are retained explicitly. These are model outputs, not approved study paths. Year 4 profiles retain only the recorded passes; additional completed courses are not inferred.\normalsize

'''
 revised=original[:start]+block+original[end:]
 revised=revised.replace('\\usepackage{booktabs}','\\usepackage{booktabs}\n\\usepackage{longtable}',1)
 new.write_text(revised,encoding='utf-8');OUT.mkdir(parents=True,exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
 (OUT/'Phase2_Report05.tex').write_text(revised,encoding='utf-8')
 for f in ['ge2340_project.sty','figures/workflow_training03.pdf','figures/stream_interaction.pdf']:
  shutil.copy2(ROOT/'output/pdf/phase2-report04'/f,OUT/f)
 manifest={'prior_tex_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
  'prior_pdf_sha256':hashlib.sha256((ROOT/'GE_SEMA/Phase2_Report04.pdf').read_bytes()).hexdigest(),
  'only_changes':'Replace model comparison with one 14-profile path table; add longtable package.',
  'blind_definition':'Other-model answers and solver reference withheld from each model; no claim of unseen documents or blinded human grading.',
  'rows':evidence}
 (OUT/'revision_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print('Created report with',len(evidence),'student/path rows.')
if __name__=='__main__':main()
