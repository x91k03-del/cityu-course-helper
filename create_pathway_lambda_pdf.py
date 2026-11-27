"""Readable profile and sensitivity report; distinguish model, policy and synthetic controls."""
import json,html
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Spacer,PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from create_examples_pdf import p,table,CodeBox,styles
ROOT=Path(__file__).resolve().parent;R=ROOT/'reports/ge-pathway-lambda';OUT=ROOT/'output/pdf/GE_Pathways_and_Lambda_Comparison.pdf'
def read(name):return json.loads((R/name).read_text(encoding='utf-8'))
def footer(c,doc):
    w,h=A4;c.setStrokeColor(colors.HexColor('#CDD8E0'));c.line(42,39,w-42,39)
    c.setFont('Arial',7.5);c.setFillColor(colors.HexColor('#526476'))
    c.drawString(42,26,'FICTIONAL PROFILE EXPERIMENT | GE pathways and lambda sensitivity | 21 Nov 2026')
    c.drawRightString(w-42,26,str(doc.page))
def main():
    actual=read('saved_timetable_results.json');sweep=read('controlled_sensitivity.json');ablation=read('GE_ablation.json');models=read('model_outputs.json')
    story=[p('GE experience, study pathways<br/>and the three lambda penalties','HeadA'),
      p('Three fictional Year 2 profiles, two live model queries, twelve controlled optimizations and twelve saved-timetable runs.','BodyA'),
      p('1. CM student: finance GE completed in Year 1','SectionA')]
    cm=actual[0];profile=cm['profile'];route=cm['pathway']
    story+=[p('<b>Input:</b> Computing Mathematics, Year 2 Semester B, cohort 2025. Passed GE2260 Introduction to Finance in Year 1 Semester A, grade B. '
      'MA1300, MA1301, MA2503, MA2508, MA2509, CS1302 and CS2360 are also recorded as passed. Full machine-readable profiles are saved with this report.'),
      p('<b>Pathway result:</b> Financial Mathematics receives a <b>3x stream-reward multiplier</b>. A new stream slot gives 6 utility units rather than 2; the completion bonus is 18 rather than 6. '
        'GE2260 earns no stream credit. This is the user-requested interest policy, not evidence of mathematical ability or a university rule.'),
      p('Priority chain: MA2510 -> MA3521 -> MA4529','SectionA'),
      p('MA3521 formally requires MA2506 or MA2510; MA4529 requires MA3521. The planner adds a smaller 3-unit prerequisite-bridge bonus to MA2510 while that prerequisite is missing. '
        'The later course still cannot be selected before its prerequisite is passed. Future offering times are not assumed from the current snapshot.'),
      table(['GE-informed Semester B plan','Neutral GE comparison'],[[', '.join(ablation[0]['GE_course_plan']['course_codes']),', '.join(ablation[0]['neutral_course_plan']['course_codes'])]],[255,256]),
      p('Only the finance GE was replaced by a neutral GE in that comparison; all other passed courses are unchanged. '
        'The finance preference adds MA2510 to the current plan and avoids prioritizing the unrelated Abstract Algebra stream course MA3523.','SmallA'),
      p('A prerequisite limitation worth preserving','SectionA'),
      p('The saved EF3320 record requires CB3410 or FB3410 and has no explicitly CM-matching section. GE2260 is not listed as a substitute. '
        'EF3320 is therefore not inserted merely because its title is financial.','BodyA'),PageBreak()]
    story += [p('2. AI GE: stream and minor checks','HeadA'),
      p('<b>CS profile:</b> Year 2 Semester B, GE2340 Artificial Intelligence - Past, Present, and Future passed in Year 1. '
        'Programming, Computer Organization, Introduction to Computational Thinking, Discrete Mathematics and Data Structures appear in the fictional completion list.'),
      p('<b>Result:</b> Artificial Intelligence is the preferred major stream, with a 3x multiplier. A missing CS3342 is also given a 3-unit bridge bonus because it is the saved prerequisite of AI-stream option CS3383.'),
      p('CS students cannot declare the AI minor','SectionA'),
      p('The official AI minor page excludes Computer Science. The appropriate option for this CS profile is the AI major stream. '
        'GE2340 itself does not satisfy a minor or stream course slot.'),
      p('CM profile interested in the AI minor','SectionA'),
      p('The third profile is a CM student with GE2340, CS2360 and a fictional CGPA of 3.3. The minor page requires CGPA at least 3.0, a listed programming pass and approval. '
        'However, the AI-minor course codes are outside the CMcourses.pdf list imposed by the user. The planner therefore records interest and blocks that course pathway; it does not expand CM registration permissions. '
        'No minor award or declaration is verified. CS2360 can supply the listed programming condition; the minor curriculum then has CS4486 plus four approved electives. Those later CS courses remain blocked under the current CM allowlist.'),
      p('What happens in the current saved CS timetable?','SectionA'),
      p('The GE-informed and neutral-GE runs choose the same Semester B course set: '+', '.join(ablation[1]['GE_course_plan']['course_codes'])+'. '
        'No direct AI-stream course is available in the imported CS Semester B subset. A higher preference cannot invent an offering; the preference affects later eligible AI choices.'),
      p('Advisory preference versus earned qualification','SectionA'),
      table(['Signal','Planning treatment'],[
        ['Passed related GE','Choose a relevant stream preference, 3x reward'],
        ['Passed prerequisite bridge','Small enabling reward; no stream slot'],
        ['Passed actual stream course','Count its distinct requirement slot once'],
        ['Explicit user stream choice','Overrides the automatic GE suggestion'],
        ['Minor/course restriction','Remains a hard gate regardless of interest']],[180,331]),PageBreak()]
    story += [p('3. Do all three lambdas work?','HeadA'),
      p('The original proposal penalizes background mismatch b, difficulty d and workload w. The current profit objective retains the same weighted cost:'),
      CodeBox('net profit = course + graduation + preparation + stream + bridge rewards\n             - lambda_b * sum(b) - lambda_d * sum(d) - lambda_w * sum(w)\n             - Year4_overload',size=9,leading=12),
      p('Controlled test: four required courses are fixed, and exactly one of three alternatives must be chosen. Candidate scores, prerequisites, credits and synthetic conflict times are frozen across settings. '
        'These tests isolate the lambda mechanics; the scores and times are test fixtures, not measured CityU workloads or actual timetables.'),
      table(['Lambda b / d / w','CM fifth course','CS fifth course','CM net utility'],[
        ['1 / 1 / 1','MA3521 (Finance)','CS4486 (AI)','17.25'],
        ['20 / 1 / 1','MA3521 (Finance)','CS4486 (AI)','1.10'],
        ['1 / 20 / 1','MA3523 (Algebra)','CS3483 (Interface design)','-5.90'],
        ['1 / 1 / 20','MA3525 (Numerical methods)','CS3402 (Databases)','-5.75'],
        ['0 / 12 / 1','MA3523','CS3483','2.85'],
        ['12 / 12 / 1','MA3521','CS4486','-8.05']],[119,136,161,95]),
      p('The last two rows change only lambda_b. That is the isolated background-penalty test. A large background penalty favours the related course; large difficulty or workload penalties favour the corresponding lower-score alternative.'),
      p('Fixed optional-course scores','SectionA'),
      table(['CM / CS alternative','b','d','w'],[
        ['Finance / AI','.05','.65','.65'],['Algebra / Interface design','.75','.10','.55'],['Numerical methods / Databases','.60','.55','.10']],[271,80,80,80]),
      p('All four required courses have .20 for each score. The displayed net values include them. Negative net utility under extreme penalties is possible because the hard five-course minimum is retained. '
        'Net values calculated under different lambdas are not comparable measures of educational quality. Every controlled MILP optimum was checked by enumerating all three possible fifth-course choices.','SmallA'),PageBreak()]
    story += [p('4. Saved-timetable results','HeadA'),
      p('These runs use the imported 2026/27 Semester B course meeting records, document membership, prerequisite expressions and section restrictions. '
        'Lecture/tutorial pairing and teaching weeks remain explicitly hypothetical. Difficulty and workload ratings are an editable synthetic rubric; they are not observed student effort.'),
      p('CM with finance GE','SectionA')]
    for index in [0,1]:
        if index:story.append(p('CS with AI GE','SectionA'))
        rows=[]
        for run in actual[index]['runs']:
            result=run['result'];rows.append([' / '.join(str(x) for x in run['lambdas']),', '.join(result.get('course_codes',[])),result.get('credits','-')])
        story.append(table(['Lambda b / d / w','Selected courses','Credits'],rows,[107,348,56]))
    story += [p('A larger penalty may remove an optional sixth course, change the set, or leave it unchanged when hard constraints dominate. '
      'One distributional GE per semester and all programme membership gates remain in force.'),
      p('How to adjust the weights yourself','SectionA'),CodeBox('programme_v6.cmd plan --profile data/ge-pathway-lambda/CM_Y2_FINANCE_GE.json\n  --assume-component-linkage --lambda-b 1 --lambda-d 20 --lambda-w 1',size=8.6,leading=11),
      p('Enter this as one PowerShell command. You can also edit the profile weights object: background_mismatch, difficulty and workload. '
        'All weights must be finite and non-negative. Editable per-course score overrides use the profile course_scores object.','SmallA'),PageBreak()]
    story += [p('5. Actual model outputs and safeguards','HeadA'),
      p('The existing v6 checkpoint was queried with the two new GE-informed profiles and the advisory pathway context. '
        '<b>Both raw model outputs failed the exact policy check (0/2).</b> Each incorrectly claimed three completed stream slots, although neither profile had passed a stream course. '
        'The exact policy returns zero completed slots; only that validated result is used. The new planning preference and lambda wiring are policy changes; model weights were not retrained in this experiment.'),
      p('CM finance: raw model output','SectionA'),CodeBox(models[0]['raw_model_output'],size=8,leading=10),
      p('CS AI: raw model output','SectionA'),CodeBox(models[1]['raw_model_output'],size=8,leading=10),
      p('Verified output in both cases','SectionA'),
      p('Completed stream slots = 0. Financial Mathematics requires 4 slots; AI requires 3. GE study supplies interest evidence only. '
        'The objective scales the base stream rewards by 3 and adds the documented prerequisite bridge reward. '
        'This result demonstrates why the validated planner, rather than raw model memory, controls course eligibility and rewards.'),
      p('Evidence and reproducibility','SectionA'),
      p('Original proposal: PP3.pdf, section 3.3. Saved course and section sources retain their terms and restrictions. Full profiles, raw input messages, raw model outputs, score totals and all sweep runs are in reports/ge-pathway-lambda/ and data/ge-pathway-lambda/.'),
      p('Profiles are fictional. Course permission, component pairing, future offerings and degree/minor approval are not certified. The finance and AI preference links are user-directed heuristics, not causal evidence of ability.','SmallA')]
    for title,url in [('Finance GE','https://www.cityu.edu.hk/catalogue/ug/202425/course/GE2260.htm'),('AI GE','https://www.cityu.edu.hk/catalogue/ug/current/course/ge2340.htm'),
      ('AI minor restrictions','https://www.cityu.edu.hk/catalogue/ug/current/Minor/MNR-AINT.htm'),('MA3521 prerequisite','https://www.cityu.edu.hk/catalogue/ug/current/course/MA3521.htm'),('MA4529 prerequisite','https://www.cityu.edu.hk/catalogue/ug/current/course/MA4529.htm')]:
        story.append(p(f'<link href="{url}" color="#007E80">{title}: official CityU source</link>','SmallA'))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=51,title='GE Pathways and Lambda Sensitivity',author='CityU course-helper experiment')
    doc.build(story,onFirstPage=footer,onLaterPages=footer);print(OUT)
if __name__=='__main__':main()
