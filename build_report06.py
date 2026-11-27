"""Two tables: completed Year-2 profiles / Year-3 A selections; later-path effects."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'reports/year3-path-comparison06';OUT=ROOT/'output/pdf/phase2-report06'
def main():
 old=ROOT/'GE_SEMA/Phase2_Report05.tex';new=ROOT/'GE_SEMA/Phase2_Report06.tex'
 if new.exists():raise RuntimeError('Do not overwrite the new report.')
 a=old.read_text(encoding='utf-8');s=a.index('\\textbf{Blind comparison of selected course paths.}');e=a.index('\\textbf{Three penalties give students meaningful control.}',s)
 cases=json.loads((DATA/'cases.json').read_text(encoding='utf-8'))
 raw={}
 for m in ['qwen','gpt']:
  raw[m]={}
  for r in json.loads((DATA/(m+'_raw.json')).read_text(encoding='utf-8')):
   raw[m][r['case_id']]=json.loads(r['raw']) if 'raw' in r else r
 labels=['CM1','CM2','CM3','CS1','CS2','CS3']
 def cell(x):return '{\\raggedright '+x+'\\par}'
 def escape(x):
  for before,after in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:x=x.replace(before,after)
  return x
 def table_head(caption,label,widths,headings):
  return r'''{\small
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.12}
\begin{longtable}{'''+widths+r'''}
\caption{'''+caption+r'''}\label{'''+label+r'''}\\
\toprule
'''+headings+r'''\\
\midrule
\endfirsthead
\multicolumn{3}{l}{\textit{Continued}}\\
\toprule
'''+headings+r'''\\
\midrule
\endhead
\midrule
\multicolumn{3}{r}{\textit{Continued on next page}}\\
\endfoot
\bottomrule
\endlastfoot
'''
 close='\\end{longtable}\n}\n\n'
 block=r'''\textbf{Year 2 profiles and Year 3 Semester A decisions.} We ran a fresh blind comparison on six fictional Year 2 students, using their projected end-of-Year-2 passing transcripts to plan Year 3 Semester A. Neither model saw the other's output or the reference solution. The saved Semester A 2026 course options are used as a planning proxy; actual Semester A 2027 offerings are unverified. Table~\ref{tab:year3-input06} gives every completed-course profile and the resulting next-semester selection. Table~\ref{tab:future-effects06} then compares how matched profile differences change the later academic path. No meeting times are shown.

'''
 block+=table_head('Completed Year 2 profiles and Year 3 Semester A course selections.','tab:year3-input06',
                   'p{2.45in}p{1.35in}p{1.35in}',
                   'Year 2 student: completed courses and preference & Fine-tuned Qwen: Year 3 A & GPT-6.1 Sol: Year 3 A')
 rows=[]
 for label,c in zip(labels,cases):
  p=c['profile'];known={o['id'] for o in c['query']['options']}
  profile=r'\textbf{'+label+'; '+p['programme']+r'.} Passed: '+', '.join(p['completed_courses'])+r'. \textit{Preference:} '+p['desired_stream']+'.'
  paths=[]
  for m in ['qwen','gpt']:
   v=raw[m][c['id']]
   if v['status']=='infeasible':text='No feasible five-course plan in supplied pool'
   else:
    text=', '.join(i.split(':')[0]+(r'$^{\dagger}$' if i not in known else '') for i in v['selected_option_ids']) or 'No courses selected'
   paths.append(text)
  block+=' & '.join(cell(x) for x in [profile,*paths])+r'\\'+'\n\\addlinespace[3pt]\n'
  rows.append({'label':label,'case_id':c['id'],'completed_courses':p['completed_courses'],'planning_year':3,'planning_semester':'A','qwen':raw['qwen'][c['id']],'gpt':raw['gpt'][c['id']]})
 block+=close+r'''\noindent\footnotesize All six inputs are Year 2 profiles; all selections target Year 3 Semester A. $\dagger$ Qwen returned an option ID outside the supplied candidate set. Outputs are preserved as generated, including incomplete or unsupported selections; no automatic correction is substituted.\normalsize

\newpage
'''
 block+=table_head('How completed study and stated preferences affect the later path: matched-profile observations.','tab:future-effects06',
                   'p{1.05in}p{2.05in}p{2.05in}',
                   'Profile factor & Fine-tuned Qwen: observed later path & GPT-6.1 Sol: observed later path')
 effects=[
 ('Analysis pass: CM1 versus CM2',
  'CM1 proposes MA4529 and later options, but incorrectly includes MA4542/MA4545 among finance options. CM2 shifts toward EF3320/EF4821 and does not identify recovery of missing MA3526.',
  'The immediate Year 3 A selection is unchanged. Both paths continue toward MA4529 and finance options, but CM2 explicitly requires MA3526 before analysis-dependent upper-level study.'),
 ('Explicit CM stream: CM1 versus CM3',
  'With the same completed courses and finance GE, the Enriched preference changes the selection toward MA4542/MA4545 and the later proposal to MA3523 plus MA4546/MA4551.',
  'The Enriched preference replaces MA3521 with MA4542 in Year 3 A. The later route changes from finance courses to MA3523 plus one of MA4528, MA4546 or MA4551, conditional on passing the selected courses.'),
 ('CS3342 pass: CS1 versus CS2',
  'CS1 proposes CS3383 and later AI core study. When CS3342 is missing, CS2 still proposes later CS4486/CS4487 and CS4386/CS4490 without a CS3342-recovery step.',
  'CS1 can access CS3383, but the current proxy pool has a clash that prevents a five-course plan. CS2 has only three distinct candidates and needs CS3342 recovery before CS3383, plus a revised candidate pool.'),
 ('Explicit CS stream: CS1 versus CS3',
  'With the same completed courses and AI GE, the Data Science preference changes the later proposal from CS4486/CS4487 toward CS3481, CS4480 and CS4487.',
  'The later goal changes from AI core CS4486/CS4487 to the Data Science chain CS3481, CS4480 and CS4487. Neither profile has a complete feasible plan in the supplied Semester A pool.')]
 for factor,q,g in effects:
  block+=' & '.join(cell(escape(x)) for x in [factor,q,g])+r'\\'+'\n\\addlinespace[5pt]\n'
 block+=close+r'''The second table summarises the models' returned explanations and the observed course-set changes; it does not certify stream completion or future availability. In particular, changing a profile can alter the later prerequisite-recovery advice without changing the immediate semester selection, as CM1 versus CM2 demonstrates.

'''
 revised=a[:s]+block+a[e:]
 new.write_text(revised,encoding='utf-8');OUT.mkdir(parents=True,exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
 (OUT/'Phase2_Report06.tex').write_text(revised,encoding='utf-8')
 for f in ['ge2340_project.sty','figures/workflow_training03.pdf','figures/stream_interaction.pdf']:
  shutil.copy2(ROOT/'output/pdf/phase2-report05'/f,OUT/f)
 manifest={'previous_tex_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
  'previous_pdf_sha256':hashlib.sha256((ROOT/'GE_SEMA/Phase2_Report05.pdf').read_bytes()).hexdigest(),
  'only_changed_model_comparison_subsection':True,'input_year':2,'output_year':3,'output_semester':'A',
  'proxy_source_term':'202609','unverified_target_term':'202709','tables':2,'rows':rows,'matched_effects':effects}
 (OUT/'revision_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print('Created two tables for six Year-2 -> Year-3 A profiles.')
if __name__=='__main__':main()
