"""Compact repeated transcript bases and remove redundant obsolete algebra."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    p=ROOT/'GE_SEMA/Phase2_Report07.tex';s=p.read_text(encoding='utf-8')
    s=re.sub(r'models\s+extquotesingle\\\s+later',"the models' later",s)
    a=s.index(r'\textbf{Reward and penalty function }');b=s.index(r'\textbf{Final formula for the Markov decision process}',a)
    s=s[:a]+r'\textbf{Reward and penalty function.} The three non-negative penalty weights express student priorities. We maximise net academic utility over feasible course sets using the following Markov-state objective.'+'\n'+s[b:]
    cases=json.loads((ROOT/'reports/timetable-retest07/cases.json').read_text())
    labels=['CM1','CM2','CM3','CS1','CS2','CS3','CM4','CM5']
    bases={'CM':set(cases[0]['profile']['completed_courses'])-{'GE2260'},'CS':set(cases[3]['profile']['completed_courses'])-{'GE2340'}}
    legend=r'''\textbf{Completed-course bases for Table~\ref{tab:retest-input07}.} Each row lists its full passed-course history by base plus additions and explicit removals; no pass is inferred from year. 

'''
    for major,base in bases.items():legend+=r'\textit{'+major+' base:} '+', '.join(sorted(base))+'.\n\n'
    for label,c in zip(labels,cases):
        q=c['profile'];done=set(q['completed_courses']);base=bases[q['programme']];missing=base-done;extra=done-base
        old=r'\textbf{'+label+'; '+q['programme']+r'.} Passed: '+', '.join(q['completed_courses'])+r'. \textit{Preference:} '+q['desired_stream']+'.'
        new=r'\textbf{'+label+'; '+q['programme']+r'.} Passed: '+q['programme']+' base'
        if missing:new+=' except '+', '.join(sorted(missing))
        if extra:new+='; plus '+', '.join(sorted(extra))
        new+=r'. \textit{Preference:} '+q['desired_stream']+'.'
        assert base-missing|extra==done
        assert old in s,label
        s=s.replace(old,new)
    pos=s.index('{\\small',s.index(r'\textbf{Updated Qwen--GPT comparison'))
    s=s[:pos]+legend+s[pos:]
    s=s.replace('\\begin{thebibliography}{9}\n\\small','\\begin{thebibliography}{9}\n\\footnotesize')
    s=s.replace('The repository demonstrates supervised training and corrective replay, now includes logged',
        'The repository demonstrates supervised training and corrective replay and now includes logged')
    p.write_text(s,encoding='utf-8');(ROOT/'output/pdf/phase2-report07/Phase2_Report07.tex').write_text(s,encoding='utf-8')
if __name__=='__main__':main()
