import unittest,json
from programme_policy import *
from ge_pathways import recommend
from stream_path import plan_stream
class StreamPathTests(unittest.TestCase):
    def test_explicit_user_choice_over_GE(self):
        p={'programme':'CM','completed_courses':['GE2260'],'desired_stream':'Enriched Mathematics'}
        self.assertEqual(recommend(p)['selected_stream'],'Enriched Mathematics')
        self.assertEqual(recommend(p)['stream_reward_multiplier'],3)
    def test_alias_and_invalid_major(self):
        self.assertEqual(recommend({'programme':'CS','completed_courses':[],'desired_stream':'AI'})['selected_stream'],'Artificial Intelligence')
        with self.assertRaises(ValueError):recommend({'programme':'CM','completed_courses':[],'desired_stream':'AI'})
    def test_finance_path_cannot_bypass_EF_prerequisites(self):
        r=plan_stream({'programme':'CM','completed_courses':['GE2260','MA2510'],'desired_stream':'finance','cm_ef_cs_prerequisite_waiver':False})
        self.assertEqual(r['path']['status'],'blocked')
        self.assertFalse(r['path']['stream_complete_if_all_passed'])
    def test_AI_course_order_and_no_reuse(self):
        r=plan_stream({'programme':'CS','completed_courses':['CS2310','CS3342'],'desired_stream':'AI'})
        self.assertEqual(r['path']['status'],'academic_dependency_path')
        self.assertTrue(r['path']['stream_complete_if_all_passed'])
        layers=r['path']['dependency_layers']
        self.assertLess(next(i for i,x in enumerate(layers) if 'CS4486' in x),next(i for i,x in enumerate(layers) if 'CS4487' in x))
        self.assertFalse(r['future_offerings_and_timetables_verified'])
    def test_already_complete_has_zero_remaining_reward(self):
        r=plan_stream({'programme':'CS','completed_courses':['CS4486','CS4487','CS3383'],'desired_stream':'AI'})
        self.assertEqual(r['path']['remaining_courses'],[]);self.assertEqual(r['scaled_chain_reward'],0)
    def test_twenty_profiles_generated_and_GE_not_qualification(self):
        p=json.loads((ROOT/'data/desired-stream/profiles.json').read_text(encoding='utf-8'))
        self.assertEqual(len(p),20)
        for major in ['CM','CS']:self.assertEqual(sum(x['programme']==major for x in p),10)
        for x in p:
            self.assertEqual(len(x['GE_history']),len({(r['year'],r['semester']) for r in x['GE_history']}))
            r=plan_stream(x);self.assertEqual(r['selected_stream'],x['desired_stream']);self.assertTrue(r['all_path_courses_programme_allowed'])
    def test_model_context_does_not_count_core_as_stream(self):
        from stream_path import model_messages
        p={'programme':'CS','completed_courses':['CS2310','CS3334','GE2340'],'desired_stream':'AI'}
        query=json.loads(model_messages(p,'system')[1]['content'])
        self.assertEqual(query['completed_courses'],[])
        self.assertEqual(set(query['background_courses_not_stream_slots']),set(p['completed_courses']))
    def test_AI_does_not_add_unnecessary_data_science_bridge(self):
        r=plan_stream({'programme':'CS','completed_courses':['CS2310','CS3342','CS2402'],'desired_stream':'AI'})
        self.assertEqual(set(r['path']['remaining_courses']),{'CS3383','CS4486','CS4487'})
if __name__=='__main__':unittest.main()
