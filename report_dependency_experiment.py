"""Publish the experiment design, implementation outcomes and raw neural probes."""
import json,html
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,PageBreak,Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from create_examples_pdf import p,table,CodeBox
ROOT=Path(__file__).resolve().parent;R=ROOT/'reports/dependency-experiment';OUT=ROOT/'output/pdf/Course_Dependency_Experiment.pdf'
def read(n):return json.loads((R/n).read_text(encoding='utf-8'))
def footer(c,d):
    c.setFont('Arial',7.5);c.setFillColor(colors.HexColor('#526476'))
    c.drawString(42,26,'COURSE DEPENDENCY EXPERIMENT | Synthetic computational interventions | 21 Nov 2026')
    c.drawRightString(A4[0]-42,26,str(d.page))
def main():
    pairs=read('paired_results.json');factor=read('factorial.json');grades=read('grade_controls.json');model=read('model_results.json')
    story=[p('Which completed courses change<br/>another course\'s reward?','HeadA'),
      p('Experiment design and executed checks for the current course-helper implementation. All student states are synthetic; numerical effects are policy utility, not proven learning gains.'),
      p('Research question','SectionA'),p('If a student passes course A, which component of course B\'s marginal reward changes, by how much, and does B become eligible? '
        'A second question tests whether two prior courses together trigger an effect that neither produces alone.'),
      p('Primary estimand','SectionA'),CodeBox('Delta R(A -> B) = R_B(after A is passed) - R_B(before A is passed)\nR_B = GE-adjusted course profit + preparation + stream reward\n      + prerequisite-bridge reward - fixed weighted cost',size=9,leading=12),
      p('Every comparison uses the same target, year 2, base profit 3, lambda values (1,1,1), and scores (.2,.2,.2), giving cost .6. '
        'All other passed courses and stream choices stay fixed unless that choice or multiplier is the named mechanism. '
        'The same-area GE experiment substitutes equal-credit GE courses.'),
      p('Keep four mechanisms separate','SectionA'),table(['Mechanism','What changes'],[
        ['Preparation','A bounded content-familiarity bonus; no formal eligibility substitution'],
        ['Stream / interest','Preference multiplier or progress toward a selected stream'],
        ['GE diminishing reward','Base profit falls for an already-covered area'],
        ['Prerequisite gate','A course becomes usable; its numeric reward need not change']],[140,371]),
      p('Quota progress, earned-credit bonuses, year-focused priority, semester competition and overload are excluded from the primary estimand. '
        'This isolates the implemented dependency rather than mixing it with graduation-credit changes. Eligibility is reported separately: an ineligible target has no usable reward, not an artificial reward of zero.'),
      p('Predeclared tests','SectionA'),p('12 paired comparisons; 4 grade controls; a 2x2 stream-reward interaction; a 2x2 prerequisite-OR check; and 4 frozen neural-model prompts. '
        'Expected values and prompts were saved before running the model. The neural weights are unchanged.'),PageBreak()]
    rows=[]
    concise={
      'D01':'Pass MA2508','D02':'Pass MA2509','D03':'Area-2 GE -> Area-1 GE',
      'D04':'Pass GE2260; finance stream fixed','D05':'GE2260; explicit Enriched choice',
      'D06':'Pass CS3481','D07':'Pass CS4480; CS3481 already passed','D08':'Pass unrelated GE1305',
      'D09':'Duplicate MA2509 ID','D10':'GE2260 strengthens bridge weight','D11':'GE2260; explicit finance weight=3',
      'D12':'MA2503; proposed EF content link'}
    for r in pairs:rows.append([r['id'],concise[r['id']],r['target'],f"{r['observed_delta']:+.2f}"])
    story += [p('1. Paired dependency results','HeadA'),table(['Case','Only changed condition','Target','Delta utility'],rows,[35,290,80,106]),
      p('How to interpret the effects','SectionA'),
      p('<b>D01-D02:</b> active preparation bonuses are +.20 and +.15. These are configured hypotheses. '
        '<b>D03:</b> base GE profit falls from 3 to .3, hence -2.70. '
        '<b>D04:</b> finance stream weight rises from 1 to 3; the next slot changes from 2 to 6, hence +4. '
        '<b>D07:</b> CS4487 becomes the final Data Science slot, so its stream component rises from 2 to 2+6=8.'),
      p('<b>D06:</b> CS4487\'s prerequisite changes from unsatisfied to satisfied, while its advertised reward is unchanged. '
        '<b>D08:</b> an unrelated GE has zero effect. '
        '<b>D09:</b> duplicating a passed ID gives no second benefit; this is an input-normalization stress test, not a valid second passing-credit record.'),
      p('<b>D05 and D11:</b> explicit choices protect user intent, and an existing weight of 3 does not multiply again to 9. '
        '<b>D10:</b> the existing bridge reward rises from 1 to 3. '
        '<b>D12:</b> a conceptual relation in the graph does not imply an active numeric preparation bonus. MA2503 does not unlock EF3320.'),
      p('Advertised target utility is not a recommendation or permission to enrol. Programme allowlists, prerequisites, exclusions and actual timetable constraints remain separate gates.','SmallA'),PageBreak()]
    story += [p('2. Test interactions, not just pairs','HeadA'),
      p('Stream threshold: A = CS3346, B = CS3356, target = CS4348. The selected stream is Software Engineering and Project Management (three of four listed courses). '
        'CS3342 and the relevant programming preparation are already passed. Stream weight is fixed at 1.'),
      table(['A passed','B passed','Target stream bonus','Target total utility'],[[c['A_CS3346'],c['B_CS3356'],c['result']['components']['stream_chain_bonus'],c['result']['advertised_marginal_utility']] for c in factor['cases']],[90,90,160,171]),
      CodeBox('Interaction = R(1,1) - R(1,0) - R(0,1) + R(0,0)\n            = 10.4 - 4.4 - 4.4 + 4.4 = +6.0',size=9,leading=12),
      p('Neither prior pass alone makes the target the final requirement. Together they do, so the additional effect is exactly the completion bonus. '
        'This exposes double-counting errors that a single-source test could miss.'),
      p('Prerequisite OR: a different interaction','SectionA'),
      p('Target CS4487 accepts CS3481 or CS4486 (another published alternative is SDSC3002). With programming and CS2402 already passed:'),
      table(['CS3481 passed','CS4486 passed','Known prerequisite satisfied'],[[c['A_CS3481'],c['B_CS4486'],str(c['result']['known_prerequisite_satisfied'])] for c in factor['gate_cases']],[130,130,251]),
      p('One qualifying alternative is enough. Passing both does not earn two prerequisite permissions or duplicate course credit. '
        'A gate effect must not be mistaken for an increase in academic utility.'),
      p('Grade boundary controls','SectionA'),
      table(['MA2509 status','Preparation bonus on GE2134'],[[g['grade'],g['result']['components']['preparation_bonus']] for g in grades],[180,331]),
      p('Source dates and restrictions remain relevant. CS4348 prerequisite evidence includes a historical source, and CS3346 is not currently offered in the inspected catalogue. '
        'This factorial is a computational rule test, not a claim that these courses can be registered now.','SmallA'),PageBreak()]
    story += [p('3. Neural-model dependency probe','HeadA'),
      p('Four greedy queries use the same selected stream and the four factorial histories above. Background preparation is provided separately from actual stream-member passes. '
        'The model must return the original unscaled policy JSON. A raw answer only passes if its complete JSON matches the expected policy; no repairs or fallback count as model success.'),
      p(f"<b>Raw model acceptance: {model['passed']}/{model['total']}.</b> Expected target-bonus interaction: +6. "
        f"Raw model interaction: {model['raw_model_reward_interaction']}. These four familiar policy-conditioned probes are diagnostic, not an independent generalization benchmark."),
      table(['Case','Exact policy match','Raw target stream bonus'],[[r['id'],str(r['accepted']),str(r['raw_target_stream_bonus'])] for r in model['results']],[70,180,261])]
    for r in model['results']:
        story += [p(r['id']+' | actual model response','SectionA'),CodeBox(r['raw_model_response'],size=7.5,leading=9)]
    story += [PageBreak(),p('4. Full experiment protocol','HeadA'),
      p('Phase A: mechanism correctness','SectionA'),
      p('Freeze the target, lambdas, score vector, year, source versions and relevant stream. Change one pass at a time, plus the matched GE substitution. '
        'Record each component delta, prerequisite state, programme permission, duplicate-credit flags and usable reward. Require the predicted sign, magnitude and component attribution to match.'),
      p('Phase B: end-to-end schedule relevance','SectionA'),
      p('Keep one complete set of course options, meetings, required courses and credit limits fixed across a paired run. '
        'Use matched-credit transcript controls, so earning another source course does not itself change graduation-credit deficits. '
        'Compare target rank, whether it enters the selected plan, plan overlap and each objective component. '
        'A reward can change without changing the optimal schedule when conflicts or mandatory courses dominate. Existing GE/lambda experiments provide a starting fixture.'),
      p('Phase C: model versus policy','SectionA'),
      p('Use frozen prompts and deterministic decoding for reproducibility. Report exact JSON accuracy, sign/magnitude error of target deltas, interaction error, and prerequisite-gate accuracy. '
        'Count policy fallback separately. For robustness, repeat with predeclared paraphrases and unrelated-history permutations, holding the actual passed set fixed.'),
      p('Phase D: educational validation','SectionA'),
      p('The numbers above test software behavior, not actual workload savings. To validate a preparation hypothesis, collect authorized target-course assessment results and study-time measures, '
        'compare students with similar prior attainment and backgrounds, account for self-selection and instructor differences, and evaluate on a later cohort with uncertainty intervals. '
        'Do not interpret agreement with synthetic policy labels as evidence of a causal learning benefit.'),
      p('Files and reruns','SectionA'),CodeBox('./.venv/Scripts/python.exe dependency_experiment.py build\n./.venv/Scripts/python.exe dependency_experiment.py model\n./.venv/Scripts/python.exe report_dependency_experiment.py',size=8.3,leading=12),
      p('reports/dependency-experiment/protocol.json: frozen design. paired_results.json: all before/after profiles and decompositions. '
        'factorial.json and grade_controls.json: interaction and boundary tests. model_protocol.json: exact prompts saved before inference. '
        'model_results.json: raw model answers. dependency_effects.csv: compact results.'),
      p('Source and policy files','SectionA'),
      p('data/preparation-v5.json; data/deep_course_relations.json; data/stream_dependency_sources.json; data/programme-v6/policy.json; saved course/GE PDFs. '
        'Unconfirmed content hypotheses remain labelled. The experiment does not change neural weights or university rules.','SmallA')]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=51,
      title='Course Dependency Experiment',author='CityU local course helper').build(story,onFirstPage=footer,onLaterPages=footer)
    print(OUT)
if __name__=='__main__':main()
