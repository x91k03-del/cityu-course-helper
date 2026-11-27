import copy,json,unittest
from four_year_markov import *
from preparation import benefits,from_transcript
class PreparationTests(unittest.TestCase):
    def test_pass_only_and_bounded(self):
        for grade in ['F','IP','W']:
            self.assertEqual(from_transcript([{'id':'MA2508','grade':grade}]),benefits([]))
        self.assertEqual(benefits(['MA2508'])['MA3512'],.25)
        self.assertEqual(benefits(['MA2509'])['GE2134'],.15)
        self.assertTrue(all(0<=v<=.35 for v in benefits(['MA2508','MA2509']).values()))
    def test_no_recursive_or_duplicate_benefit(self):
        self.assertEqual(benefits(['MA1301']),benefits([]))
        self.assertEqual(benefits(['MA2508','MA2508']),benefits(['MA2508']))
        self.assertEqual(benefits(['GE2134']),benefits([]))
    def test_prior_background_profit_difference(self):
        a=state_from([],5);b=state_from([{'id':'MA2509','grade':'B'}],5)
        ra=reward(a,['GE2134'],parameters(a));rb=reward(b,['GE2134'],parameters(b))
        self.assertAlmostEqual(rb['net_profit']-ra['net_profit'],.15)
        self.assertEqual(ra['course_cost_penalty'],rb['course_cost_penalty'])
    def test_same_semester_source_no_transfer(self):
        s=state_from([],3);r=reward(s,['MA2509','GE2134'],parameters(s))
        self.assertEqual(r['preparation_benefit'],0)
    def test_guard_rejects_hallucinated_benefit_or_cap(self):
        s=state_from([]);p=parameters(s);self.assertTrue(parameter_grade(s,p))
        bad=copy.deepcopy(p);bad['preparation_bonus_by_course']['GE2134']=.15
        self.assertFalse(parameter_grade(s,bad));self.assertFalse(parameter_grade(s,{**p,'maximum_distribution_GE_per_semester':2}))
    def test_audit_detects_GE_cap_even_failed_attempt(self):
        r=copy.deepcopy(read(REPORT/'rule_rollouts.json')[0]['transcript'])
        ge=[x for x in r if x['kind']=='distribution_GE'];ge[1]['term']=ge[0]['term'];ge[1]['grade']='F'
        self.assertFalse(audit(r)['checks']['at_most_one_distribution_GE_per_semester'])
    def test_all_plans_respect_GE_cap(self):
        for r in read(REPORT/'rule_rollouts.json'):
            self.assertEqual(r['status'],'complete',r.get('failure'))
            for t in range(1,9):self.assertLessEqual(sum(x['kind']=='distribution_GE' and x['term']==t for x in r['transcript']),1)
    def test_semester_solver_enforces_cap(self):
        from scheduler import solve
        from test_scheduler import option
        opts=[option('GE1105'),option('GE1202',day=2)]
        p={'student_year':2,'term':'DEMO','required_courses':['GE1105','GE1202'],'completed_courses':[],
           'course_min':2,'course_max':2,'credit_min':6,'credit_max':6,'options':opts}
        self.assertEqual(solve(p)['status'],'infeasible')
        with self.assertRaises(ValueError):transition(state_from([]),['GE1105','GE1202'])
    def test_production_preparation_increases_profit_without_reducing_workload(self):
        from scheduler import solve
        from test_scheduler import option
        o=option('GE2134');original=copy.deepcopy(o)
        p={'student_year':2,'term':'DEMO','required_courses':['GE2134'],'completed_courses':[],
           'course_min':1,'course_max':1,'credit_min':3,'credit_max':3,'options':[o]}
        a=solve(p);b=solve({**p,'completed_courses':['MA2509']})
        self.assertAlmostEqual(b['objective']-a['objective'],.15)
        self.assertEqual(o,original)
    def test_contacts_not_discounted(self):
        g=graph();self.assertEqual(g['courses']['MA2508']['lecture_hours_total'],39)
        self.assertEqual(g['courses']['GE2134']['workshop_hours_weekly'],1)
        for c in g['courses'].values():self.assertIsNone(c['published_self_study_hours'])
    def test_formal_prerequisite_not_waived_by_preparation(self):
        cat={c['id']:c for c in catalog()}
        self.assertEqual(cat['MA3511']['prerequisites'],['MA2508','MA2503'])
        self.assertEqual(cat['MA3515']['prerequisites'],['MA2503'])
        s=state_from([{'id':'MA2508','grade':'B'}],5)
        self.assertEqual(parameters(s)['preparation_bonus_by_course']['MA3515'],.2)
        with self.assertRaises(ValueError):transition(s,['MA3515'])
    def test_resit_profiles_contain_the_intended_failure(self):
        runs={r['profile_id']:r for r in read(REPORT/'rule_rollouts.json')}
        for pid,course in [('CM2025_ANALYSIS_RESIT','MA3526'),('CM2025_GE_RESIT','GE1305'),('CM2025_CALCULUS_RESIT','MA2508')]:
            self.assertIn('F',[r['grade'] for r in runs[pid]['transcript'] if r['id']==course])
    def test_current_training_and_holdout_states_are_disjoint(self):
        from preparation_training import TRAIN_DATA,state_key
        groups={}
        for split in ['train','validation','test']:
            groups[split]=set()
            for line in (TRAIN_DATA/(split+'.jsonl')).read_text(encoding='utf-8').splitlines():
                row=json.loads(line)
                if row['task']!='Markov_profit_parameters':continue
                state=json.JSONDecoder().raw_decode(row['messages'][1]['content'])[0]['Markov_state']
                groups[split].add(state_key(state))
                self.assertTrue(parameter_grade(state,json.loads(row['messages'][-1]['content'])))
        for a,b in [('train','test'),('train','validation'),('validation','test')]:self.assertFalse(groups[a]&groups[b])
if __name__=='__main__':unittest.main()
