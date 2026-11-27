"""Source-grounded degree entrypoint; no MILP.

The default requires exact saved timetable evidence. The optional curriculum-only
beam search remains a historical reference, not a verified offering timetable.
"""
import argparse,copy,itertools,json,math,time
from functools import lru_cache
from pathlib import Path
import project_runtime
from four_year_markov import catalog,audit
from programme_policy import allowed,policy,progress
from cm_background_policy import waives_prerequisites
ROOT=Path(__file__).resolve().parent

def audit_sequence(profile,steps,transcript):
    """Recompute curriculum feasibility independently of the search's bitmasks."""
    source={c['id']:c for c in catalog()};done=set();errors=[]
    if [s['term'] for s in steps]!=list(range(1,9)):errors.append('not_eight_ordered_semesters')
    for s in steps:
        chosen=s['selected_courses'];term=s['term']
        if len(set(chosen))!=len(chosen) or done&set(chosen):errors.append('duplicate_credit')
        if any(c not in source or not allowed('CM',c) for c in chosen):errors.append('unknown_or_disallowed_course');continue
        credited=[source[c] for c in chosen if source[c]['credits']>0]
        if not 0<=len(credited)<=6:errors.append('course_count')
        if sum(c['credits'] for c in credited)>18:errors.append('credit_cap')
        if sum(c['kind']=='distribution_GE' for c in credited)>1:errors.append('GE_cap')
        for code in chosen:
            c=source[code]
            if not c['earliest']<=term<=c['latest']:errors.append('curriculum_window:'+code)
            if not waives_prerequisites(profile,code) and not set(c['prerequisites'])<=done:errors.append('prior_semester_prerequisite:'+code)
        load=sum(c['credits'] for c in credited);expected=.25*max(0,load-(12 if term>=7 else 15))**2
        if not math.isclose(s['reward']['overload'],expected):errors.append('overload_accounting')
        parts=s['reward'];net=sum(parts[k] for k in ('gross','area_progress','graduation_progress','stream_chain','on_path','preparation'))-parts['cost']-parts['overload']
        if not math.isclose(net,parts['net_profit']):errors.append('reward_accounting')
        done.update(chosen)
    if done!={r['id'] for r in transcript}:errors.append('transcript_disagrees_with_actions')
    result=audit(transcript);rule=policy()['streams']['CM'][profile.get('desired_stream','Enriched Mathematics')]
    result['checks'].update(selected_stream_complete=progress(rule,done)>=rule['slots'],
        semester_course_maximum_respected=all(sum(source[c]['credits']>0 for c in s['selected_courses'])<=6 for s in steps),
        sequence_and_reward_audit=not errors)
    result['sequence_violations']=sorted(set(errors))
    result['all_encoded_requirements_met']=all(result['checks'].values())
    return result

def simulate(profile,beam_width=24,branch_width=24,require_timetable_evidence=True):
    if require_timetable_evidence:
        from grounded_degree import simulate as grounded_simulate
        return grounded_simulate(profile)
    if profile['programme']!='CM' or profile.get('year',1)!=1:
        raise ValueError('This full-degree simulation currently supports an entering Year-1 CM profile.')
    source=[copy.deepcopy(c) for c in catalog() if allowed('CM',c['id'])]
    codes=[c['id'] for c in source];index={c:i for i,c in enumerate(codes)}
    stream=profile.get('desired_stream','Enriched Mathematics');rule=policy()['streams']['CM'][stream]
    credits=[c['credits'] for c in source];required=sum(1<<i for i,c in enumerate(source) if c['required'])
    prereq=[]
    for c in source:
        if waives_prerequisites(profile,c['id']):prereq.append(0)
        elif any(x not in index for x in c['prerequisites']):prereq.append(None)
        else:prereq.append(sum(1<<index[x] for x in c['prerequisites']))
    initial=profile.get('completed_courses',[])
    if initial:raise ValueError('Use an entering profile with an empty completed transcript for this simulation.')
    @lru_cache(maxsize=200000)
    def info(mask):
        selected=[i for i in range(len(source)) if mask>>i&1]
        done={codes[i] for i in selected};areas=tuple(sum(source[i]['kind']=='distribution_GE' and source[i].get('area')==a for i in selected) for a in [1,2,3])
        maths=sum(credits[i] for i in selected if source[i]['kind']=='math_elective')
        free=sum(credits[i] for i in selected if source[i]['kind']=='free_elective')+max(0,maths-12)
        return {'credits':sum(credits[i] for i in selected),'math':maths,'free':free,'areas':areas,
                'GE':sum(areas),'mandatory_missing':(required&~mask).bit_count(),
                'slots':progress(rule,done),'stream_complete':progress(rule,done)>=rule['slots']}
    def terminal(mask):
        x=info(mask)
        return (x['mandatory_missing']==0 and 122<=x['credits']<=144 and x['math']>=20 and x['free']>=20
                and x['GE']>=4 and all(x['areas']) and x['stream_complete'])
    def value(mask):
        x=info(mask)
        return (-4*x['mandatory_missing']-.3*max(0,122-x['credits'])-1.3*max(0,20-x['free'])
                -.4*max(0,20-x['math'])-5*sum(n==0 for n in x['areas'])-2*max(0,4-x['GE'])
                -2*(rule['slots']-x['slots'])-6*(not x['stream_complete']))
    @lru_cache(maxsize=128)
    def preparation_for(mask):
        from preparation import benefits
        return benefits([codes[i] for i in range(len(source)) if mask>>i&1])
    def advance(mask,action,term):
        new=mask|sum(1<<i for i in action);a=info(mask);b=info(new)
        gross=sum(0 if not credits[i] else .3 if source[i]['kind']=='distribution_GE' and a['areas'][source[i]['area']-1] else 3 for i in action)
        area_bonus=5*sum(x==0 and y>0 for x,y in zip(a['areas'],b['areas']))
        progress_reward=2*(min(4,b['GE'])-min(4,a['GE']))+1.5*(min(20,b['math'])-min(20,a['math']))+.05*(min(122,b['credits'])-min(122,a['credits']))
        chain=2*(b['slots']-a['slots'])+6*(b['stream_complete'] and not a['stream_complete'])
        on_path=sum(source[i]['required'] and source[i]['earliest']==term for i in action)
        prep=preparation_for(mask)
        preparation=sum(prep.get(codes[i],0) for i in action)
        load=sum(credits[i] for i in action);penalty=.25*max(0,load-(12 if term>=7 else 15))**2
        risk=sum(credits[i]>0 for i in action)
        reward=gross+area_bonus+progress_reward+chain+on_path+preparation-risk-penalty
        return new,reward,{'gross':gross,'area_progress':area_bonus,'graduation_progress':progress_reward,
            'stream_chain':chain,'on_path':on_path,'preparation':preparation,'cost':risk,'overload':penalty,'net_profit':reward}
    def actions(mask,term):
        if any(c['required'] and c['latest']<term and not(mask>>i&1) for i,c in enumerate(source)):return
        eligible=[i for i,c in enumerate(source) if not(mask>>i&1) and c['earliest']<=term<=c['latest']
                  and prereq[i] is not None and prereq[i]&mask==prereq[i]]
        automatic=tuple(i for i in eligible if credits[i]==0 and source[i]['required'])
        positive=[i for i in eligible if credits[i]>0]
        urgent={i for i in positive if source[i]['required'] and source[i]['latest']==term}
        min_count=0
        for count in range(min_count,min(6,len(positive))+1):
            for group in itertools.combinations(positive,count):
                if not urgent<=set(group) or sum(credits[i] for i in group)>18:continue
                if sum(source[i]['kind']=='distribution_GE' for i in group)>1:continue
                new=mask|sum(1<<i for i in group+automatic);x=info(new);remaining=8-term
                if x['credits']>144 or x['credits']+18*remaining<122:continue
                if x['mandatory_missing']>6*remaining+2:continue
                if max(4-x['GE'],sum(v==0 for v in x['areas']))>remaining:continue
                yield tuple(group)+automatic
    start=time.perf_counter();beam=[{'mask':0,'return':0.,'steps':[]}];expanded=[]
    for term in range(1,9):
        states={};explored=0
        for node in beam:
            ranked=[]
            for action in actions(node['mask'],term):
                new,r,parts=advance(node['mask'],action,term);explored+=1
                if term==8 and not terminal(new):continue
                ret=node['return']+.98**(term-1)*r
                ranked.append((ret+value(new),new,ret,action,parts))
            ranked.sort(reverse=True,key=lambda x:(x[0],x[2],x[1]))
            for rank,new,ret,action,parts in ranked[:branch_width]:
                if new in states and states[new]['return']>=ret:continue
                step={'term':term,'year':(term+1)//2,'semester':'A' if term%2 else 'B','selected_courses':[codes[i] for i in action],
                      'credit_bearing_course_count':sum(credits[i]>0 for i in action),'zero_credit_requirements':[codes[i] for i in action if not credits[i]],
                      'credits':sum(credits[i] for i in action),'reward':parts,'earned_credits_after':info(new)['credits']}
                states[new]={'mask':new,'return':ret,'rank':rank,'steps':node['steps']+[step]}
        expanded.append({'term':term,'semester_actions_evaluated':explored,'distinct_states':len(states)})
        if not states:
            return {'status':'search_exhausted','reason':'No graduation-compatible state retained; this is not a proof of infeasibility.',
                    'term':term,'search':expanded,'seconds':time.perf_counter()-start,'method':'Markov finite-horizon beam search; no MILP'}
        beam=sorted(states.values(),key=lambda n:(n['rank'],n['return']),reverse=True)[:beam_width]
        print('TERM',term,'actions',explored,'retained',len(beam),'top credits',info(beam[0]['mask'])['credits'],flush=True)
    best=max(beam,key=lambda n:n['return']);transcript=[]
    for step in best['steps']:
        for code in step['selected_courses']:
            c=source[index[code]]
            transcript.append({'id':code,'course_code':c.get('course_code_display',code),'title':c['title'],'credits':c['credits'],
              'kind':c['kind'],'area':c.get('area'),'grade':'B','year':step['year'],'semester':step['semester'],'term':step['term'],'synthetic':True})
    result=audit_sequence(profile,best['steps'],transcript)
    return {'status':'complete' if result['all_encoded_requirements_met'] else 'graduation_incomplete','input_profile':profile,
      'method':'Markov finite-horizon beam search; no MILP','policy':'maximise discounted reward with flexible semester loads and hard terminal graduation requirements',
      'beam_width':beam_width,'branch_width':branch_width,'discount':.98,'discounted_return':best['return'],
      'steps':best['steps'],'transcript':transcript,'audit':result,'search':expanded,'seconds':time.perf_counter()-start,
      'assumptions':['All selected courses passed with B; no failures or exemptions.',
       'Saved normative curriculum windows/precedence and user CM waiver assumptions; future offerings and actual full-degree timetable are unverified.',
       'Search is approximate and does not prove global optimality; success is independently audited.',
       'This is planner-policy simulation, not evidence that neural weights learned Bellman updates.']}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--profile',required=True);a.add_argument('--output',required=True);a.add_argument('--beam-width',type=int,default=24);v=a.parse_args()
    p=json.loads(Path(v.profile).read_text(encoding='utf-8'));r=simulate(p,v.beam_width)
    out=Path(v.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(r['status'],r.get('audit',{}).get('earned_credits'),r.get('audit',{}).get('all_encoded_requirements_met'),flush=True)
