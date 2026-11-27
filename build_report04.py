"""Replace only the model comparison subsection with timetable differences."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'reports/timetable-comparison04';OUT=ROOT/'output/pdf/phase2-report04'
def main():
 source=ROOT/'GE_SEMA/Phase2_Report03.tex';destination=ROOT/'GE_SEMA/Phase2_Report04.tex'
 if destination.exists():raise RuntimeError('New report already exists; preserve it.')
 old=source.read_text(encoding='utf-8');start=old.index('\\textbf{Timetable benchmark: Qwen versus GPT-6.1 Sol.}')
 end=old.index('\\textbf{Three penalties give students meaningful control.}',start)
 cases=json.loads((DATA/'cases.json').read_text(encoding='utf-8'))
 raw={m:json.loads((DATA/(m+'_raw.json')).read_text(encoding='utf-8')) for m in ['qwen','gpt']}
 assert len(cases)==14 and all(len(raw[m])==14 for m in raw)
 selections={}
 for m,rows in raw.items():
  selections[m]={}
  for r in rows:
   try:value=json.loads(r['raw']) if 'raw' in r else r
   except ValueError:value={'status':'unparseable','selected_option_ids':[]}
   selections[m][r['case_id']]=value
 descriptions=[
  ('CM_early_analysis','Example 1: CM student with Analysis already completed',
   r'Year 2 CM; GE2260 (Introduction to Finance) and MA3526 (Analysis) are passed. GPT selects MA3511, MA2507 and MA3530, whereas Qwen includes MA3515. Both outputs include MA2510, MA3517 and MA3523 with identical meetings; those unchanged entries are omitted below. Qwen\textquotesingle s MA3515 also overlaps the shared MA2510 on Thursday.'),
  ('CM_enriched_despite_finance_GE','Example 2: CM student choosing Enriched Mathematics',
   r'Year 2 CM; GE2260 is passed, but the student explicitly requests Enriched Mathematics. Qwen includes MA2510 and MA3526. GPT instead includes MA2507, MA3511 and MA3530. MA3515, MA3517 and MA3523 have identical meetings in both outputs and are omitted below.'),
  ('CS_data_science','Example 3: CS student choosing Data Science after an AI GE',
   r'Year 2 CS; GE2340 is passed, but Data Science is explicitly selected. Qwen returns CS3103, CS3402 and CS3481. GPT also includes CS2613, CS3342 and CS3391. Even the three shared course codes have different tutorial choices, as the meeting times show.'),
  ('CS_workload_priority','Example 4: CS student placing higher weight on workload',
   r'Year 2 CS with AI interest; the workload penalty is raised to $\lambda_w=20$, with $\lambda_b=\lambda_d=1$. Qwen returns CS3103 and CS3342. GPT includes those courses with different tutorials, together with CS2613, CS3402 and CS3481.')]
 block=r'''\textbf{Timetable outputs: fine-tuned Qwen versus GPT-6.1 Sol.} We compared 14 fictional profiles: six existing cases and eight additional profiles varying prior mathematics study, stream preference, workload priority and final-year status. Both models receive the same profile-specific course options, meeting times and planning rules. Below we present only four illustrative examples where their timetable outputs differ, without replacing either model's answer with an optimiser result. All 14 inputs and outputs are retained separately; these selected examples are not an overall performance estimate.

The tables show only changed courses or class sessions. A dash means the model did not select that course. Times are in 24-hour format and come from the supplied option IDs; no new class times are inferred. As elsewhere in the report, component pairing and teaching weeks remain planning assumptions.

'''
 evidence=[]
 days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
 def cell(text):return '{\\raggedright '+text+'\\par}'
 def times(o):
  def hh(t):return f'{t//60:02d}:{t%60:02d}'
  return '; '.join(days[m['day']-1]+' '+hh(m['start_minute'])+'--'+hh(m['end_minute']) for m in o['meetings'])
 for i,(ident,title,description) in enumerate(descriptions,1):
  c=next(c for c in cases if c['id']==ident);index={o['option_id']:o for o in c['problem']['options']};mapped={}
  for m in ['qwen','gpt']:
   mapped[m]={}
   for option_id in selections[m][ident]['selected_option_ids']:
    code=index[option_id]['course_code'] if option_id in index else option_id.split(':')[0]
    mapped[m].setdefault(code,[]).append(option_id)
  changed=[code for code in sorted(set(mapped['qwen'])|set(mapped['gpt'])) if sorted(mapped['qwen'].get(code,[]))!=sorted(mapped['gpt'].get(code,[]))]
  assert changed
  block+='\\textbf{'+title+'} '+description.replace(r'\textquotesingle ',"'")+r'''

\begin{table}[H]
\centering\small
\caption{'''+title+r''' --- differing timetable entries only.}
\begin{tabular}{p{.6in}p{2.2in}p{2.2in}}
\toprule
Course & Fine-tuned Qwen & GPT-6.1 Sol\\
\midrule
'''
  entries=[]
  for code in changed:
   values=[code]
   for m in ['qwen','gpt']:
    ids=mapped[m].get(code,[])
    text=' / '.join(times(index[x]) if x in index else 'ID not in supplied options; time unavailable' for x in ids) if ids else '---'
    values.append(text)
   block+=' & '.join(cell(v) for v in values)+r'\\'+'\n';entries.append(values)
  block+=r'''\bottomrule
\end{tabular}
\label{tab:comparison04-'''+str(i)+r'''}
\end{table}

'''
  evidence.append({'case_id':ident,'changed_courses':changed,'table_entries':entries,
                   'qwen':selections['qwen'][ident],'gpt':selections['gpt'][ident]})
 revised=old[:start]+block+old[end:]
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
 destination.write_text(revised,encoding='utf-8');(OUT/'Phase2_Report04.tex').write_text(revised,encoding='utf-8')
 for f in ['ge2340_project.sty','figures/workflow_training03.pdf','figures/stream_interaction.pdf']:
  shutil.copy2(ROOT/'output/pdf/phase2-report03'/f,OUT/f)
 assert revised[:start]==old[:start] and revised.endswith(old[end:])
 manifest={'old_tex_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
  'old_pdf_sha256':hashlib.sha256((ROOT/'GE_SEMA/Phase2_Report03.pdf').read_bytes()).hexdigest(),
  'only_replaced_model_comparison_subsection':True,'total_tested_profiles':14,'new_profiles':8,
  'report_selection':'four cases with differing outputs; not an overall benchmark score',
  'selected_examples':evidence}
 (OUT/'revision_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 (DATA/'displayed_examples.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
 print('Created',destination,'with',len(evidence),'differing examples.')
if __name__=='__main__':main()
