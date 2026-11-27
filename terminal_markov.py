"""Finite-horizon Markov beam search with a hard terminal acceptance predicate."""
def search(initial,horizon,actions,transition,terminal,key,heuristic=lambda s:0,width=32,terminal_reward=lambda s:0.,stage_heuristic=None):
    beam=[{'state':initial,'return':0.,'actions':[]}];pruned=False;counts=[]
    for term in range(1,horizon+1):
        states={};expanded=0
        for node in beam:
            for action in actions(node['state'],term):
                state,reward=transition(node['state'],action,term);expanded+=1
                if term==horizon and not terminal(state):continue
                value=node['return']+.98**(term-1)*reward
                if term==horizon:value+=terminal_reward(state)
                k=key(state)
                if k not in states or value>states[k]['return']:
                    states[k]={'state':state,'return':value,'actions':node['actions']+[action]}
        counts.append(expanded)
        if not states:return {'status':'search_exhausted' if pruned else 'infeasible','expanded':counts,'pruned':pruned}
        ordered=sorted(states.values(),key=lambda n:n['return']+(stage_heuristic(n['state'],term) if stage_heuristic else heuristic(n['state'])),reverse=True)
        if len(ordered)>width:pruned=True
        beam=ordered[:width]
    best=max(beam,key=lambda n:n['return'])
    assert terminal(best['state'])
    return {'status':'complete','best':best,'expanded':counts,'pruned':pruned,'globally_optimal':not pruned}
