"""Validate the completed experiment before activating its separate adapter."""
import hashlib,shutil,unittest
from four_year_markov import *
from preparation_training import TRAIN_REPORT
MODULES=['test_preparation_v5','test_four_year_markov','test_profit_objective','test_profit_planning','test_scheduler',
         'test_five_course_policy','test_cm_planning_update','test_assistant_loss','test_ma_timetable','test_ge_timetable',
         'test_banweb_collector','test_ma_offline_import','test_cm_profile_grading']
def main():
    suite=unittest.defaultTestLoader.loadTestsFromNames(MODULES)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise SystemExit('Checks failed: current adapter not activated')
    training=read(TRAIN_REPORT/'training.json');evaluation=read(TRAIN_REPORT/'evaluation.json')
    assert training['status']=='complete'
    assert evaluation['after']['passed']==evaluation['after']['total']==20
    runs=read(REPORT/'rule_rollouts.json')+read(TRAIN_REPORT/'model_rollouts.json')
    assert len(runs)==8
    audits=[{'profile_id':r['profile_id'],'audit':audit(r['transcript'])} for r in runs]
    assert all(r['status']=='complete' for r in runs)
    assert all(a['audit']['all_encoded_requirements_met'] for a in audits)
    # Recompute each realized profit from its observed transition, not stored totals.
    profits=[]
    for run in runs:
        for step in run['steps']:
            calculated=reward(step['state_before'],step['selection'],step['parameters'],step['state_after'])
            assert structured_grade(calculated,step['profit'])
            profits.append({'profile_id':run['profile_id'],'term':step['term'],'matches_recomputed_profit':True})
    calls=read(TRAIN_REPORT/'rollout_parameter_calls.json');paired=read(TRAIN_REPORT/'counterfactual_predictions.json')
    assert len(calls)==24 and all(c['accepted'] for c in calls)
    assert len(paired)==8 and all(c['passed'] for c in paired)
    assert not any(s['fallback_to_rule_parameters'] for r in runs for s in r['steps'])
    snapshot=read(ROOT/ADAPTER/'preparation_policy.json')
    prior=hashlib.sha256((ROOT/'adapters/bscm-markov-v4/adapter_model.safetensors').read_bytes()).hexdigest()
    assert prior==snapshot['source_adapter_sha256']
    current=hashlib.sha256((ROOT/ADAPTER/'adapter_model.safetensors').read_bytes()).hexdigest()
    assert current!=prior
    validation={'automated_tests':result.testsRun,'tests_passed':True,'complete_transcripts':len(runs),'semester_profit_recomputations':len(profits),
       'audits':audits,'profit_arithmetic':profits,'model_parameters_accepted':len(calls),'parameter_fallbacks':0,
       'paired_transcript_diagnostics_passed':len(paired),'source_adapter_unchanged':True,'official_graduation_verified':False}
    write(TRAIN_REPORT/'validation.json',validation)
    write(ROOT/'data/active_planning_adapter.json',{'adapter':ADAPTER,'adapter_sha256':current,
       'source_adapter':'adapters/bscm-markov-v4','source_adapter_sha256':prior,
       'model_role':'state_dependent_profit_parameters_GE_cap_and_direct_preparation_controller',
       'training_performed':True,'selected_epoch':training['selected_epoch'],'policy_file':'data/four_year_policy.json',
       'preparation_hypotheses':'data/preparation-v5.json','formal_prerequisite_branches':'data/preparation-v5-prerequisites.json',
       'training_report':'reports/preparation-v5/training.json','evaluation_report':'reports/preparation-v5/evaluation.json',
       'four_year_audit_report':'reports/preparation-v5/validation.json','final_selection_authority':'hard_constrained_curriculum_solver',
       'full_current_syllabi_downloaded':False,'official_graduation_verified':False})
    write(ROOT/ADAPTER/'verified_prerequisite_branches.json',read(ROOT/'data/preparation-v5-prerequisites.json'))
    storage=read(ROOT/'reports/storage-audit.json')
    storage['C_free_bytes_after_evaluation']=shutil.disk_usage('C:/').free
    storage['F_free_bytes_after_evaluation']=shutil.disk_usage('F:/').free
    storage['project_cache_bytes_after']=sum(p.stat().st_size for p in (ROOT/'.cache').rglob('*') if p.is_file())
    write(ROOT/'reports/storage-audit.json',storage)
    from preparation_report import main as report
    report()
    print('Activated',ADAPTER,'after',result.testsRun,'checks;',len(runs),'complete transcripts;',len(calls),'accepted model calls')
if __name__=='__main__':main()
