import copy,hashlib,json,unittest
import profit_planning as profit
from cm_planning_update import DATA
from ma_timetable import read
from test_cm_profiles import make_profiles

class ProfitPlanningTests(unittest.TestCase):
    def test_source_reference_validates_for_all_new_profiles(self):
        for p in read(DATA/'test_profiles.json'):
            r=profit.reference(p)
            self.assertTrue(profit.grade(p,r['plan'])['passed'],p['profile_id'])
            if r['plan']['status']=='candidate':
                self.assertGreaterEqual(r['course_count'],5)
                self.assertAlmostEqual(r['profit_breakdown']['schedule_loss'],-r['profit_breakdown']['net_profit'])
    def test_new_profit_objective_is_graded_not_historical_cost(self):
        p=next(p for p in make_profiles() if p['profile_id']=='CM06')
        relaxed=profit.reference(p,{'overload_penalty_weight':0})
        self.assertEqual(relaxed['course_count'],6)
        self.assertTrue(profit.grade(p,relaxed['plan'],{'overload_penalty_weight':0})['passed'])
        strict=profit.reference(p,{'overload_penalty_weight':100})
        self.assertEqual(strict['course_count'],5)
        self.assertFalse(profit.grade(p,relaxed['plan'],{'overload_penalty_weight':100})['passed'])
    def test_source_times_not_changed_to_improve_profit(self):
        p=next(p for p in make_profiles() if p['profile_id']=='CM06');r=profit.reference(p)
        r['plan']['selected_options'][0]['meetings'][0]['start_time']='02:00'
        self.assertFalse(profit.grade(p,r['plan'])['passed'])
    def test_copy_weights_identical_and_not_retrained(self):
        manifest=read(profit.REPORT/'checkpoint_copy.json')
        self.assertFalse(manifest['training_performed']);self.assertTrue(manifest['source_and_copy_identical'])
        for f in manifest['files']:
            for folder in [profit.ROOT/'adapters/bscm-planning-v2',profit.ROOT/profit.ADAPTER]:
                self.assertEqual(hashlib.sha256((folder/f['file']).read_bytes()).hexdigest(),f['sha256'])

if __name__=='__main__':unittest.main(verbosity=2)
