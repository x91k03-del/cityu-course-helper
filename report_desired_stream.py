"""Export all 20 inputs, validated paths, raw model results and limitations."""
import json,csv,html
from collections import Counter
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,PageBreak,Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from create_examples_pdf import p,table,CodeBox
ROOT=Path(__file__).resolve().parent;R=ROOT/'reports/desired-stream';OUT=ROOT/'output/pdf/Desired_Stream_20_Examples.pdf'
def footer(c,d):
    c.setFont('Arial',7.5);c.setFillColor(colors.HexColor('#526476'))
    c.drawString(42,26,'FICTIONAL POST-CORE PROFILES | Desired-stream planning | 21 November 2026')
    c.drawRightString(A4[0]-42,26,str(d.page))
def main():
    cases=json.loads((R/'plans.json').read_text(encoding='utf-8'));models=json.loads((R/'model_outputs.json').read_text(encoding='utf-8'))
    lookup={x['profile_id']:x for x in models}
    for row in cases:lookup[row['profile']['profile_id']]['complete_path']=row['stream_plan']
    (R/'model_outputs.json').write_text(json.dumps(models,ensure_ascii=False,indent=2),encoding='utf-8')
    counts=Counter(x['stream_plan']['path']['status'] for x in cases)
    summary={'CM_profiles':10,'CS_profiles':10,'paths':dict(counts),'raw_model_accepted':sum(x['accepted'] for x in models),
       'raw_model_total':20,'raw_model_acceptance_by_programme':{m:sum(x['accepted'] for x in models if x['profile_id'].startswith(m)) for m in ['CM','CS']},
       'policy_fallbacks':sum(not x['accepted'] for x in models),'weights_retrained':False,
       'path_notes':'Dependency layers are not semester assignments. Source-based paths are not official eligibility, registration, stream declaration or future availability.'}
    (R/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    with (R/'20_examples.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['FICTIONAL TEST PROFILES - NOT OFFICIAL UNIVERSITY RECORDS'])
        w.writerow(['profile','programme','desired_stream','GE_passed','stream_weight','path_status','dependency_layers','pending_rules','blocking_courses','model_accepted'])
        for row in cases:
            q=row['profile'];s=row['stream_plan'];b=s['path'];w.writerow([q['profile_id'],q['programme'],q['desired_stream'],', '.join(x['course_code'] for x in q['GE_history']),q['stream_reward_multiplier'],b['status'],
              ' -> '.join('+'.join(x) for x in b['dependency_layers']),'; '.join(x['course'] for x in b['unknown_rules']),
              '; '.join(x.get('course',','.join(x.get('courses',[]))) for x in b['blocked']),lookup[q['profile_id']]['accepted']])
    story=[p('Choose a desired stream<br/>20 CM and CS examples','HeadA'),
      p('10 Computing Mathematics profiles and 10 Computer Science profiles. Taught core is completed; GE history, grades and preference weights are generated with a fixed random seed.'),
      p('User control','SectionA'),
      CodeBox('programme_v6.cmd stream-path --profile data/desired-stream/CS_01.json\n  --desired-stream "Artificial Intelligence" --stream-weight 4',size=8.6,leading=11),
      p('Use one command line in PowerShell. The profile field desired_stream or the command option overrides GE-based suggestions. '
        'Default explicit preference weight is 3; an override between 0 and 10 is allowed. The same options work with plan and model-stream.'),
      p('Reward and path logic','SectionA'),
      p('Base reward is 2 per newly filled distinct stream slot plus 6 once when complete. The selected-stream multiplier scales those rewards. '
        'Completed core and GE never count as stream slots merely because they are related. The path search chooses a permitted course combination and expands known prerequisites before ordering the remaining courses.'),
      table(['Outcome','Profiles'],[['Source-based academic dependency path',counts['academic_dependency_path']],['Provisional: rule confirmation needed',counts['provisional_missing_rules']],['Blocked by current programme policy',counts['blocked']],['Raw model answers accepted',str(summary['raw_model_accepted'])+'/20']],[380,131]),
      p('Raw model acceptance was 0/10 for CM and 10/10 for CS. Rejected model answers use the exact rule policy; the report never treats them as model successes. '
        'The existing v6 weights were used without new fine-tuning. These are policy-conditioned illustrations, not a new independent accuracy benchmark.'),
      p('The five finance routes are blocked by missing EF prerequisites outside the CM allowlist. Two Cybersecurity routes use historical CS4286 evidence; two Software Engineering routes need current CS4348 confirmation. '
        'CS3346 is not offered in the current academic year, so its future availability is also unresolved. No page below is a verified weekly timetable.','SmallA'),PageBreak()]
    for start in range(0,20,2):
        for row in cases[start:start+2]:
            q=row['profile'];s=row['stream_plan'];b=s['path'];m=lookup[q['profile_id']]
            story += [p(q['profile_id']+' | '+html.escape(q['desired_stream']),'SectionA'),
              p('<b>Input:</b> '+q['programme']+'; taught core completed; user-selected weight '+str(q['stream_reward_multiplier'])+'. '
                'Passed GE: '+', '.join(x['course_code']+' ('+x['grade']+', Y'+str(x['year'])+x['semester']+')' for x in q['GE_history'])+'.','SmallA'),
              p('<b>Current earned stream slots:</b> '+str(s['current_progress']['completed_slots'])+'/'+str(s['current_progress']['required_slots'])+
                '. <b>Status:</b> '+b['status'].replace('_',' ')+'.','SmallA')]
            layers=b['dependency_layers'];rows=[[str(i+1),', '.join(x)] for i,x in enumerate(layers)] or [['-','Already completed']]
            story.append(table(['Dependency layer','Courses'],rows,[125,386]))
            if b['blocked']:story.append(p('<b>Blocked:</b> '+html.escape('; '.join(x.get('course',','.join(x.get('courses',[])))+': '+x['reason'].replace('_',' ') for x in b['blocked'])),'SmallA'))
            if b['unknown_rules']:story.append(p('<b>Needs confirmation:</b> '+html.escape('; '.join(x['course']+': '+x['reason'].replace('_',' ') for x in b['unknown_rules'])),'SmallA'))
            if b['offering_warnings']:story.append(p('<b>Offering warning:</b> '+html.escape('; '.join(c+': '+v for c,v in b['offering_warnings'].items())),'SmallA'))
            story.append(p('<b>Conditional remaining stream utility:</b> '+str(s['scaled_chain_reward'])+
               (' (no completion reward assigned to a blocked route).' if b['status']=='blocked' else ' if the listed eligible courses are subsequently passed; prerequisite courses do not earn extra stream slots.')+
               ' <b>Raw model accepted:</b> '+str(m['accepted'])+'.','SmallA'))
            story += [p('Actual model response','SmallA'),CodeBox(m['raw_model_response'],size=7.3,leading=8.8),Spacer(1,12)]
        story.append(PageBreak())
    story += [p('Common completed core and provenance','HeadA'),p('Computing Mathematics','SectionA'),
      p(', '.join(cases[0]['profile']['completed_taught_core'])),p('Computer Science','SectionA'),p(', '.join(cases[10]['profile']['completed_taught_core'])),
      p('These are completed taught-core sets, not complete degree transcripts. Final projects, internships, required supporting categories and total graduation credits are not assumed fulfilled. '
        'Support courses and each student\'s exact completed set are saved in their individual input JSON. No academic year or future class time is fabricated from the completion set.'),
      p('Reading dependency layers','SectionA'),p('Every course in a later layer has its known prerequisites satisfied by the original completed set or an earlier layer. '
        'Layers may contain several courses, are not semesters, and do not enforce an 18-credit load or a timetable. For an actual semester use plan, which retains the saved-source constraints and requires explicit acknowledgement of unverified component linkage.'),
      p('Random generation','SectionA'),p('Seed 20261121. GE courses, passing grades and weights vary randomly; desired streams are balanced for coverage. One fictional GE is assigned to each listed semester. '
        'The finance GE pair with conflicting exclusion evidence is not sampled together. Historical offering eligibility is not certified.'),
      p('Reproduce and inspect','SectionA'),CodeBox('programme_v6.cmd stream-path --profile data/desired-stream/CM_02.json\nprogramme_v6.cmd plan --profile YOUR_PROFILE.json --desired-stream "Data Science"\n  --stream-weight 3 --assume-component-linkage\npython generate_stream_profiles.py generate\npython generate_stream_profiles.py model',size=8.3,leading=11),
      p('Full profiles: data/desired-stream/profiles.json. Raw model inputs and outputs: reports/desired-stream/model_outputs.json. '
        'All 20 plans: reports/desired-stream/plans.json. Spreadsheet-friendly summary: reports/desired-stream/20_examples.csv. '
        'Stream definitions come from the user-supplied CM/CS programme PDFs; additional prerequisite sources are recorded per course and in data/stream_dependency_sources.json.'),
      p('Source versions are mixed and explicitly retained. A completed sequence is conditional on current requirements, permission, grades and future offerings; it is not an official stream declaration or graduation certification.','SmallA')]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=51,
        title='Desired Streams: 20 Random CM and CS Examples',author='CityU local course helper').build(story,onFirstPage=footer,onLaterPages=footer)
    print(OUT)
if __name__=='__main__':main()
