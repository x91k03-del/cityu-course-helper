"""Explain the reward-only LLM / external-search boundary and measured tests."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
import project_runtime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'reports/llm-reward-external-search';OUT=ROOT/'output/pdf/llm-reward-external-search'
def main():
    OUT.mkdir(parents=True,exist_ok=True);runs={n:json.loads((DATA/f'{n}_exact.json').read_text()) for n in ('F','N','M')}
    s=getSampleStyleSheet();s.add(ParagraphStyle(name='T2',fontName='Helvetica-Bold',fontSize=20,leading=24,spaceAfter=11,textColor=colors.HexColor('#173d50')))
    s.add(ParagraphStyle(name='B2',fontSize=9.2,leading=12.5,spaceAfter=8));s.add(ParagraphStyle(name='C2',fontSize=8.3,leading=11));s.add(ParagraphStyle(name='S2',fontSize=8,leading=10.5,spaceAfter=7))
    def p(t,k='B2'):return Paragraph(t,s[k])
    def table(rows,widths):
        t=Table([[p(escape(str(c)),'C2') for c in row] for row in rows],colWidths=widths,repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#deedf2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f8')]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));return t
    story=[p('LLM rewards; external path optimization','T2'),
        p('<b>The LLM supplies the reward model. External software chooses the path.</b> The implemented interface accepts only numeric reward parameters and direct source/target/benefit links. '
          'It rejects schedule fields, invalid numbers and attempts to change hard degree requirements.'),
        table([['Component','Output','Chooses the path?'],
          ['GPT teacher','Configured academic reward policy and course preparation relationships','No'],
          ['Local Qwen','Validated JSON: eight reward settings and 26 course links','No'],
          ['External dynamic programming','Best legal completion path, objective and optimality certificate','Yes']],[109,319,83]),Spacer(1,9),
        p('<b>Algorithm: exact dynamic programming on a finite assignment graph.</b> A state records the remaining course-to-semester assignments and prior passes. '
          'Each action places an eligible missing elective in a semester. Duplicate states are merged; infeasible states are rejected. '
          'The objective adds discounted semester rewards and subtracts weighted costs and overload. Course preparation uses the strongest direct prior-pass link, capped at 0.35; same-semester and repeated-course benefits do not count.'),
        p('The current demonstration keeps the saved course/section allocations and compulsory catch-up placements fixed. It optimizes the six missing electives over their permitted A/B terms. '
          'The exact search retains every state instead of a narrow beam. A second, independent Cartesian enumeration checks all 64 term combinations and confirms the same maximum. '
          'This follows the <link href="https://underactuated.mit.edu/dp.html" color="#245c79">finite-horizon dynamic-programming principle</link>.'),
        table([['Profile','Planned credits','Maximum reward','Feasible / checked'],
          *[[{'F':'Finance prepared','N':'No finance at entry','M':'Enriched mathematics'}[n],runs[n]['audit']['earned_credits'],f"{runs[n]['discounted_academic_reward']:.6f}",f"{runs[n]['completion_optimality_certificate']['feasible_assignments']} / 64"] for n in runs]],[139,91,123,158]),Spacer(1,8),
        p('<b>Parameter sensitivity: the tool changes its decision.</b> With the same finance-prepared input and course links, changing only the Year 4 overload weight produces:'),
        table([['Year 4 overload weight','Year 3B credits','Year 4B credits','Total'],['0.25 (configured policy)',18,15,122],['0 (counterfactual test)',15,18,122]],[190,112,112,97]),Spacer(1,8),
        p('The counterfactual allows the tool to move three credits to the final semester. This is a policy-sensitivity test, not evidence of improved educational outcomes. '
          'The configured overload weight remains 0.25. The user can still adjust the three cost weights in the profile; the LLM cannot weaken the 122-credit requirement.'),
        p('<b>Verification and limits.</b> All three paths pass the encoded GE, core, project, mathematics-elective, free-elective and desired-stream checks. '
          'The optimality gap is zero <b>within this declared completion space</b>; no global maximum over all possible saved course reallocations or future catalogues is claimed. '
          'Twenty-five credits still have pending timetable details under the approved curriculum mode. These are curriculum plans, not confirmed registration timetables.','S2'),
        p('One actual local Qwen inference exported the complete parameter/link packet. It was accepted without fallback; no candidate timetable was sent to or generated by the LLM. '
          'Configured numeric weights and relationships were copied correctly in this run; the links remain GPT-authored content hypotheses. This is not independent empirical reward validation. '
          'Neural weights were unchanged. Software verification: 108 checks passed. Earlier reports and checkpoints were preserved.','S2')]
    def footer(c,d):
        c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#60717a'));c.drawString(42,21,'Reward-only LLM architecture | 24 November 2026');c.drawRightString(553,21,str(d.page))
    path=OUT/'Reward_Only_LLM_External_Optimizer.pdf'
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=32,bottomMargin=34).build(story,onFirstPage=footer,onLaterPages=footer)
    print(path)
if __name__=='__main__':main()
