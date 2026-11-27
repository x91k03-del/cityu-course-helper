import copy,unittest
from four_year_markov import *
from profit_objective import settings,overload_penalty

class FourYearTests(unittest.TestCase):
    def test_historical_rollouts_are_rejected_by_current_document_rules(self):
        for r in read(REPORT/'rule_rollouts.json'):
            result=audit(r['transcript'])
            # These preserved snapshots predate the document allowlist.
            # Their credit totals alone must not certify graduation.
            self.assertFalse(result['all_encoded_requirements_met'],r['profile_id'])
            self.assertFalse(result['checks']['programme_document_membership'])
            self.assertGreaterEqual(result['earned_credits'],122);self.assertGreaterEqual(result['elective_math_credits'],20)
            self.assertEqual(result['core_credits'],45);self.assertEqual(result['capstone_credits'],6)
            self.assertFalse(result['official_graduation_verified'])
    def test_source_122_overrides_only_lower_user_floor(self):
        self.assertEqual(POLICY['user_minimum_credits'],121);self.assertEqual(POLICY['effective_minimum_credits'],122)
        self.assertEqual(read(REPORT/'sources.json')['source_minimum_credits'],122)
    def test_each_area_required_even_with_four_GE(self):
        r=copy.deepcopy(read(REPORT/'rule_rollouts.json')[0]['transcript'])
        row=next(x for x in r if x['id']=='GE1305');row['id']='GE1128';row['course_code']='GE1128';row['area']=1
        result=audit(r);self.assertTrue(result['checks']['four_distribution_GE']);self.assertFalse(result['checks']['each_GE_area_covered'])
    def test_failed_IP_never_cover_GE_or_earn_credits(self):
        for g in ['F','IP','W']:
            s=state_from([]);after,rows=transition(s,['GE1105'],{'GE1105':g})
            self.assertEqual(after['earned_credits'],0);self.assertEqual(after['distribution_GE_count'],0)
            self.assertEqual(after['GE_area_counts']['1'],0);self.assertEqual(after['attempted_credits'],3)
            self.assertEqual(reward(s,['GE1105'],parameters(s),after)['gross_course_profit'],0)
    def test_repeat_area_profit_is_much_lower(self):
        s=state_from([]);after,rows=transition(s,['GE1105'])
        first=reward(s,['GE1113'],parameters(s))
        repeat=reward(after,['GE1113'],parameters(after))
        self.assertLess(repeat['gross_course_profit'],.1*first['gross_course_profit'])
        self.assertGreater(first['net_profit'],repeat['net_profit'])
    def test_fourth_GE_required_after_all_areas_covered(self):
        s=state_from([])
        for code in ['GE1105','GE1202','GE1305']:
            s,rows=transition(s,[code]);s['term']+=1
        self.assertEqual(parameters(s)['GE_count_progress_bonus'],2)
        s,rows=transition(s,['GE1113']);self.assertEqual(parameters(s)['GE_count_progress_bonus'],0)
    def test_year_specific_credit_threshold(self):
        for year in [1,2,3]:
            c=settings({'student_year':year});self.assertEqual(overload_penalty(6,c,15),0);self.assertEqual(overload_penalty(6,c,18),2.25)
        c=settings({'student_year':4})
        self.assertEqual([overload_penalty(6,c,x) for x in [9,12,15,18]],[0,0,2.25,9])
        with self.assertRaises(ValueError):settings({})
    def test_year4_credit_MILP_matches_exhaustive_search(self):
        import itertools,random
        from scheduler import solve
        from test_scheduler import option
        rng=random.Random(202504)
        for trial in range(8):
            opts=[option('DEMO'+str(i),day=1+i//4,start=480+(i%4)*90,cost=.1) for i in range(7)]
            for o in opts:o.update(credits=rng.choice([3,4]),profit=rng.uniform(1,8))
            p={'student_year':4,'term':'DEMO','required_courses':[],'completed_courses':[],
               'credit_min':0,'credit_max':18,'options':opts}
            values=[]
            for n in range(7):
                for group in itertools.combinations(opts,n):
                    credit=sum(o['credits'] for o in group)
                    if credit<=18:values.append(sum(o['profit']-.3 for o in group)-.25*max(0,credit-12)**2)
            result=solve(p);self.assertEqual(result['status'],'optimal')
            self.assertAlmostEqual(result['objective'],max(values),places=6)
    def test_production_GE_profit_uses_completed_area_state(self):
        from scheduler import solve
        from test_scheduler import option
        p={'student_year':2,'term':'DEMO','required_courses':[],'completed_courses':['GE1105'],
           'course_min':1,'course_max':1,'credit_min':3,'credit_max':3,'completed_GE_area_counts':{'1':1},
           'options':[{**option('GE1113'),'ge_area':1},{**option('GE1202',day=2),'ge_area':2}]}
        result=solve(p);self.assertEqual(result['course_codes'],['GE1202'])
    def test_year4_does_not_keep_five_course_default(self):
        from scheduler import solve
        from test_scheduler import option
        opts=[option('DEMO'+str(i),day=1+i//4,start=480+(i%4)*90,cost=1/3) for i in range(6)]
        p={'student_year':4,'term':'DEMO','required_courses':[],'completed_courses':[],
           'credit_min':0,'credit_max':18,'options':opts}
        self.assertEqual(solve(p)['course_count'],4)
        p['student_year']=3;self.assertEqual(solve(p)['course_count'],5)
        p['overload_mode']='year4_credits';self.assertEqual(solve(p)['course_count'],6)
    def test_duplicate_passed_credit_is_rejected(self):
        rows=read(REPORT/'rule_rollouts.json')[0]['transcript'];duplicate=next(r for r in rows if r['grade'] in PASS)
        with self.assertRaises(ValueError):audit(rows+[duplicate])
    def test_math_core_and_capstone_not_math_electives(self):
        rows=read(REPORT/'rule_rollouts.json')[0]['transcript'];only=[r for r in rows if r['kind']!='math_elective']
        self.assertEqual(audit(only)['elective_math_credits'],0)
    def test_early_analysis_is_not_repeated_for_credit(self):
        early=next(r for r in read(REPORT/'rule_rollouts.json') if r['early_analysis'])
        analysis=[r for r in early['transcript'] if r['id']=='MA3526']
        self.assertEqual(len(analysis),1);self.assertEqual(analysis[0]['term'],2)
    def test_markov_state_independent_of_record_order(self):
        rows=read(REPORT/'rule_rollouts.json')[0]['transcript'][:10]
        a,b=state_from(rows,3),state_from(list(reversed(rows)),3)
        self.assertEqual(a,b);self.assertEqual(parameters(a),parameters(b))
    def test_model_parameter_guard(self):
        s=state_from([],5);good=parameters(s);self.assertTrue(parameter_grade(s,good))
        for k,v in [('covered_GE_area_multiplier',1),('year4_overload_weight',.25),('overload_threshold_credits',15)]:
            bad={**good,k:v};self.assertFalse(parameter_grade(s,bad))
    def test_language_GE_is_not_distribution_GE(self):
        rows=[{'id':c,'grade':'B'} for c in ['GE1401','GE2401','GE1501','GE1601']]
        s=state_from(rows);self.assertEqual(s['earned_credits'],10);self.assertEqual(s['distribution_GE_count'],0)
    def test_training_and_holdout_parameter_vectors_are_disjoint(self):
        from markov_training import TRAIN_DATA,state_key
        groups={}
        for split in ['train','validation','test']:
            groups[split]=set()
            for line in (TRAIN_DATA/(split+'.jsonl')).read_text(encoding='utf-8').splitlines():
                r=json.loads(line)
                if r['task']!='Markov_profit_parameters':continue
                content=json.JSONDecoder().raw_decode(r['messages'][1]['content'])[0]
                s=content['Markov_state'];groups[split].add(state_key(s))
                # Historical v4 dataset keeps its original nine-field schema.
                actual=json.loads(r['messages'][-1]['content']);expected=parameters(s)
                self.assertEqual(actual,{k:expected[k] for k in actual})
        self.assertFalse(groups['train']&groups['test']);self.assertFalse(groups['train']&groups['validation'])
        self.assertFalse(groups['test']&groups['validation'])
    def test_legacy_seed_not_silently_relabelled(self):
        old=read(REPORT/'legacy_seed_compatibility.json');self.assertFalse(old['compatible']);self.assertFalse(old['silently_rewritten'])
    def test_failed_analysis_is_replanned_and_graduated(self):
        r=next(r for r in read(REPORT/'rule_rollouts.json') if r['profile_id']=='CM2025_ANALYSIS_RESIT')
        self.assertEqual([x['grade'] for x in r['transcript'] if x['id']=='MA3526'][0],'F')
        self.assertTrue(r['audit']['all_encoded_requirements_met'])
        self.assertTrue(any(s['profit']['overload_penalty']>0 for s in r['steps'] if s['state_before']['year']==4))
    def test_final_term_failure_is_not_labelled_graduated(self):
        r=simulate('NEGATIVE_FINAL_PROJECT_FAILURE',fail_once=['MA4530:B'])
        self.assertEqual(r['status'],'graduation_incomplete')
        self.assertFalse(r['audit']['all_encoded_requirements_met'])

if __name__=='__main__':unittest.main(verbosity=2)
