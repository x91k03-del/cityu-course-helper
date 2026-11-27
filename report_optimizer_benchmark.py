"""Matched, blind direct-GPT completion task; no optimizer answers in its packet."""
import copy,hashlib,json
from pathlib import Path
import project_runtime
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'reports/report-optimizer-comparison'
ELECTIVES=['MA4528','MA4529','MA4537','MA4546','MA4550','MA4551']

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'gpt_input.json').exists():raise RuntimeError('Comparison packet already frozen')
    pending=json.loads((ROOT/'data/curriculum-pending-evidence.json').read_text())['courses']
    teacher=json.loads((ROOT/'data/reward-only/active_packet.json').read_text())
    priorities=json.loads((ROOT/'data/cm_year_priority_policy.json').read_text())
    cases=[]
    for n in ['F','N','M']:
        r=json.loads((ROOT/f'reports/llm-reward-external-search/{n}_exact.json').read_text())
        fixed=[]
        for s in r['semesters']:
            rows=[o for o in s['course_evidence'] if o['course_code'] not in ELECTIVES]
            fixed.append({'term':s['term'],'year':s['year'],'semester':s['semester'],
                'fixed_courses':[{'course_code':o['course_code'],'credits':o['credits']} for o in rows],
                'fixed_credits':sum(o['credits'] for o in rows),
                'positive_course_count':sum(o['credits']>0 for o in rows)})
        p=r['input_profile']
        cases.append({'case_id':n,'programme':'CM','desired_stream':p['desired_stream'],
            'completed_year1':p['historical_transcript'],'fixed_remaining_context':fixed})
    packet={'task':'Direct GPT planning with no solver or code; allocate all six remaining electives to permitted terms 5-8. Return a complete assignments object for each case.',
        'blind_protocol':'No optimizer output, candidate ranking, objective value or feasibility result is provided. Use only this packet. No browsing, coding, numerical tool, search program or other model call. Reason directly from the facts. Writing the final JSON file is allowed.',
        'teacher_reward_packet':teacher,'math_core_priority_policy':priorities,
        'cost_weights':{'background_mismatch':1,'difficulty':1,'workload':1},
        'discount':.98,'semester_credit_maximum':18,'positive_course_maximum':6,'minimum_course_count':0,
        'fixed_part_must_not_change':True,'minimum_final_credits':122,'maximum_final_credits':144,
        'GE_rule':'Four distributional GE spanning Areas 1,2,3, at most one per semester; compulsory language/development GE is separate. Fixed courses already encode those requirements.',
        'history_is_assumed_fictional':True,'pending_timetable_mode_authorised':True,
        'future_offerings':'A/B recurrence is an explicit simulation assumption; missing class times remain pending.',
        'electives':[{ 'course_code':c,'credits':3,'eligible_terms':[5,7] if pending[c]['semesters']==['A'] else [6,8],
            'completion_alternatives':pending[c]['completion_alternatives']} for c in ELECTIVES],
        'utility_rule':'J = sum over terms 3..8 of 0.98^(term-3) * (course base profit + preparation + core priority + bridge + stream progress + GE progress + EF3320 Year4 bonus - weighted course costs - EF no-finance surcharge - overload). No reward for historical passes again.',
        'pending_elective_scores':{'difficulty':.62,'workload':.65,
            'background_mismatch':'MA4529 and MA4537: .45 no finance, .15 introductory finance, .05 advanced finance. Other new electives: .18 because MA1301 is passed.'},
        'finance_background':'Passed GE1202/GE2260 gives introductory preparation; a passed EF course or MA3521/MA4529/MA4537 gives advanced preparation. Prior terms only; same-term courses do not count.',
        'preparation_rule':'Strongest direct prior-pass edge, maximum .35 per target; no sum, recursion, same-term or repeat benefit.',
        'stream_rule':{'multiplier':3,'per_new_distinct_slot':2,'completion_once':6,
            'Financial Mathematics':{'required':['MA3521','MA4529'],'choose_two':['MA4537','EF3320','EF4821']},
            'Enriched Mathematics':{'required':['MA3523','MA4542','MA4545'],'choose_one':['MA4528','MA4546','MA4551']}},
        'priority_rule':'Only unfinished common core receives the supplied year-focus reward, multiplied by graduation_priority_weight. Fixed base courses keep their existing placements. The six new electives receive no common-core priority.',
        'GE_areas':{'GE2260':2,'GE1105':1,'GE1113':1,'GE1305':3,'GE2134':1},
        'GE_progress':'New area +5 and GE count progress +2 while below four. Covered area multiplies base by .1.',
        'overload_rule':'.25 * max(0,semester credits - 15)^2 for Years1-3; .25 * max(0,semester credits - 12)^2 in Year4.',
        'bridge_rule':'For the financial stream, MA2510 receives +3 if neither MA2506 nor MA2510 was passed before that term. These fixed placements are unchanged.',
        'fixed_course_scores':'Only the new elective placements change. For fixed EF3320 the background score follows the prior-pass finance level above, its extra surcharge is 1.5 if there is no finance preparation, and its preparation benefit follows the supplied graph. Other fixed course base scores and year bonuses are unchanged across allowed assignments.',
        'output_schema':{'answers':[{'case_id':'F or N or M','assignments':{'MA4528':'integer term','MA4529':'integer term','MA4537':'integer term','MA4546':'integer term','MA4550':'integer term','MA4551':'integer term'},'explanation':'brief explanation'}]},
        'cases':cases}
    (OUT/'gpt_input.json').write_text(json.dumps(packet,indent=2),encoding='utf-8')
    (OUT/'protocol.json').write_text(json.dumps({'comparator':'Direct GPT agent; previously requested GPT-6.1 Sol label; actual endpoint identity is not independently exposed',
        'paired_cases':3,'input_sha256':hashlib.sha256((OUT/'gpt_input.json').read_bytes()).hexdigest(),
        'model_blind_to_optimizer_results':True,'LLM_solver_tools_forbidden':True,'one_response_per_case':True,
        'scope':'Six-elective completion with a fixed source-backed curriculum context, not global full-degree rescheduling or empirical student evaluation'},indent=2))
    print(OUT/'gpt_input.json')

def assess():
    from curriculum_chain import plan
    raw=json.loads((OUT/'gpt_direct_corrected_raw.json').read_text())
    answers={x['case_id']:x for x in raw['answers']}
    if set(answers)!={'F','N','M'} or len(raw['answers'])!=3:raise ValueError('Expected three fresh direct GPT answers')
    packet=json.loads((OUT/'gpt_input_corrected.json').read_text())
    rows=[]
    for q in packet['cases']:
        n=q['case_id'];p=json.loads((ROOT/f'reports/llm-reward-external-search/{n}_profile.json').read_text())
        p['evaluate_completion_proposal']=answers[n]['assignments']
        baseline=json.loads((ROOT/f'reports/ef-late-ge-examples/{n}_rollout.json').read_text())
        result=plan(p,baseline)
        if result['optimizer_called']:raise AssertionError('Direct GPT evaluator must not optimize')
        optimized=json.loads((ROOT/f'reports/llm-reward-external-search/{n}_exact.json').read_text())
        row={'case_id':n,'input':q,'gpt_raw':answers[n],'gpt_evaluation':result,
            'optimizer_output':optimized,'gpt_repaired':False,
            'reward_gap':None if not result['proposal_valid'] else optimized['discounted_academic_reward']-result['discounted_academic_reward'],
            'different_assignments':{c:{'optimizer':next(s['term'] for s in optimized['semesters'] if c in s['selected_courses']),
                'gpt':answers[n]['assignments'].get(c)} for c in ELECTIVES
                if answers[n]['assignments'].get(c)!=next(s['term'] for s in optimized['semesters'] if c in s['selected_courses'])}}
        rows.append(row)
    (OUT/'comparison.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    summary={'cases':3,'direct_GPT_valid':sum(r['gpt_evaluation']['proposal_valid'] for r in rows),
        'direct_GPT_matches_optimum':sum(r['reward_gap'] is not None and abs(r['reward_gap'])<1e-7 for r in rows),
        'input_corrected_before_final_response':True,'pilot_results_excluded':True,
        'scores_are_configured_utility_not_educational_outcomes':True,
        'results':[{'case_id':r['case_id'],'optimizer_reward':r['optimizer_output']['discounted_academic_reward'],
            'GPT_reward':r['gpt_evaluation'].get('discounted_academic_reward'),'reward_gap':r['reward_gap'],
            'different_assignments':r['different_assignments']} for r in rows]}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':
    import sys
    assess() if len(sys.argv)>1 and sys.argv[1]=='assess' else build()
