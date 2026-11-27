"""Natural language only: no custom system message, examples or teacher edges."""
import hashlib,json,time,sys
from pathlib import Path
import project_runtime

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reports/qwen-natural-language-20261127'

def save(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    OUT.mkdir(parents=True,exist_ok=True)
    old=json.loads((ROOT/'reports/additional-qwen-examples-20261127/results.json').read_text())
    old={x['id']:x for x in old}
    profile_texts={
      'FIN_PASS':[
        "I am a Year 2 Computing Mathematics student at City University of Hong Kong. My transcript is CS1302: B, MA1300: B+, and GE2260 Introduction to Finance: A-. How well does my completed study prepare me for EF3320?",
        "I'm in my second year of Computing Mathematics at CityUHK. I passed GE2260 Introduction to Finance with A-, CS1302 with B and MA1300 with B+. Based on these results, what preparation do I have for EF3320?"],
      'FIN_FAIL':[
        "I am a Year 2 Computing Mathematics student at City University of Hong Kong. My transcript is CS1302: B, MA1300: B+, and GE2260 Introduction to Finance: F. How well does my completed study prepare me for EF3320?",
        "I'm in my second year of Computing Mathematics at CityUHK. I failed GE2260 Introduction to Finance, but passed CS1302 with B and MA1300 with B+. Based on these results, what preparation do I have for EF3320?"],
      'AI_GE':[
        "I am a Year 2 Computer Science student at City University of Hong Kong. My transcript is CS1302A: A, CS2310: B+, and GE2340 Artificial Intelligence - Past, Present, and Future: B. How well does my completed study prepare me for CS4487?",
        "I'm studying Computer Science in Year 2 at CityUHK. I have passed the AI GE GE2340 with B, CS2310 with B+ and CS1302A with A. What preparation from these courses would help me take CS4487?"],
      'AI_MAX':[
        "I am a Year 3 Computing Mathematics student at City University of Hong Kong. My transcript is MA2503: B+, MA2510: P, MA3515: A-, and GE2340: B. How well does my completed study prepare me for CS4487?",
        "I'm a third-year Computing Mathematics student at CityUHK. My passed courses are GE2340 (B), MA3515 (A-), MA2510 (P) and MA2503 (B+). What preparation from these courses would help me take CS4487?"],
    }
    cases=[]
    for key,texts in profile_texts.items():
        for index,text in enumerate(texts,1):
            cases.append({'id':key+f'_NL{index}','group':key,'mode':'natural_language_question',
                          'input_text':text,'reference':old[key]['expected'],
                          'previous_structured_raw_output':old[key]['raw_model_output']})
    for key in ['FIN_PASS','AI_GE']:
        text=profile_texts[key][0].split(' How well')[0]
        cases.append({'id':key+'_TRANSCRIPT_ONLY','group':key,'mode':'transcript_only_no_question',
                      'input_text':text,'reference':None})
        cases.append({'id':key+'_PLAN','group':key,'mode':'ordinary_planning_question',
                      'input_text':text+' What courses should I consider next semester and why?',
                      'reference':None})
    for c in cases:c['messages']=[{'role':'user','content':c['input_text']}]
    if (OUT/'cases.json').exists():
        assert json.loads((OUT/'cases.json').read_text(encoding='utf-8'))==cases
    else:save('cases.json',cases)
    (OUT/'natural_language_inputs.txt').write_text('\n\n'.join(
        'CASE '+c['id']+'\nUSER MESSAGE (exact text)\n'+c['input_text'] for c in cases),encoding='utf-8')
    manifest=json.loads((ROOT/'data/active_relation_adapter.json').read_text())
    save('protocol.json',{'adapter':manifest['adapter'],'cases':len(cases),
         'custom_system_message':False,'teacher_edges_provided':False,'output_schema_instructed':False,
         'few_shot_examples_provided':False,'retrieval_used':False,'optimizer_used':False,
         'each_case_new_conversation':True,'decoding':'greedy, standard Qwen chat template, enable_thinking=False',
         'max_new_tokens':512,'neural_weights_updated':False,
         'scope':'Natural language and paraphrase robustness probes; references withheld from model. Transcript-only controls have no explicit task, so no answer-format accuracy is assigned.'})
    import torch
    from inference import load
    from programme_policy import exact
    torch.set_num_threads(8)
    tok,model=load(manifest['adapter'])
    rendered=[]
    results=json.loads((OUT/'results.json').read_text(encoding='utf-8')) if (OUT/'results.json').exists() else []
    for c in cases:
        prompt=tok.apply_chat_template(c['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=False)
        assert '<|im_start|>system' not in prompt
        rendered.append('CASE '+c['id']+'\n'+prompt)
    (OUT/'rendered_inputs.txt').write_text('\n\n'.join(rendered),encoding='utf-8')
    for c in cases:
        if any(r['id']==c['id'] for r in results):continue
        prompt=tok.apply_chat_template(c['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=False)
        batch=tok(prompt,return_tensors='pt').to('cuda');start=time.perf_counter()
        with torch.inference_mode():
            ids=model.generate(**batch,max_new_tokens=512,do_sample=False,pad_token_id=tok.eos_token_id,use_cache=True)
        tail=ids[0,batch.input_ids.shape[1]:]
        raw=tok.decode(tail,skip_special_tokens=True).strip()
        try:parsed=json.loads(raw)
        except (ValueError,TypeError):parsed=None
        reference=c['reference']
        result={**c,'raw_output':raw,'parsed_json':parsed,'generated_tokens':len(tail),
                'hit_token_limit':len(tail)>=512,'seconds':round(time.perf_counter()-start,2),
                'exact_reference_match':exact(reference,parsed) if reference is not None else None,
                'repair_used':False,'fallback_used':False}
        results.append(result);save('results.json',results)
        (OUT/'natural_language_outputs.txt').write_text('\n\n'.join(
            'CASE '+r['id']+'\nINPUT\n'+r['input_text']+'\nRAW OUTPUT\n'+r['raw_output']+
            '\nHIT TOKEN LIMIT: '+str(r['hit_token_limit']) for r in results),encoding='utf-8')
        print(c['id'],'TOKENS',len(tail),'EXACT',result['exact_reference_match'],raw[:220],flush=True)
    pairs=[]
    for key in profile_texts:
        a,b=[r for r in results if r['group']==key and r['mode']=='natural_language_question']
        pairs.append({'profile':key,'identical_raw_answers':a['raw_output']==b['raw_output'],
                      'same_parsed_answer':a['parsed_json']==b['parsed_json'] if a['parsed_json'] is not None and b['parsed_json'] is not None else None,
                      'both_exact_reference':a['exact_reference_match'] and b['exact_reference_match']})
    summary={'cases':len(results),'natural_language_question_cases':8,
             'exact_reference_matches':sum(r['exact_reference_match'] is True for r in results),
             'paraphrase_pairs':pairs,'truncated_outputs':sum(r['hit_token_limit'] for r in results),
             'input_sha256':hashlib.sha256((OUT/'natural_language_inputs.txt').read_bytes()).hexdigest()}
    save('summary.json',summary)
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
