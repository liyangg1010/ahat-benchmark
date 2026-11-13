"""Installed-wheel regression: all references, liquid replay and mixed routing.

Run with the installed environment's Python -I, outside the source package.
Uses real VAL and a local mock judge; never calls a remote model.
"""
import hashlib,json,sys,tempfile,os,subprocess
from pathlib import Path
from types import SimpleNamespace
import ahat_benchmark
from ahat_benchmark.config import PROJECT_DIR
from ahat_benchmark.domains import resolve_domain,domain_binding,BASE_DOMAIN,LIQUID_DOMAIN
from ahat_benchmark.datasets import load_eval_set
from ahat_benchmark.inference_inputs import export_inputs
from ahat_benchmark.pddl import final_state,full_problem,sexpr
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.judge.evaluator import RubricEvaluator
from ahat_benchmark.judge.prompts import PROMPTS,LIQUID_PROMPTS
from ahat_benchmark.pipeline.val_stage import run_val_stage
from ahat_benchmark.pipeline.judge_stage import run_judge_stage
from ahat_benchmark.pipeline.summarize import summarize
assert Path(ahat_benchmark.__file__).is_relative_to(Path(sys.prefix)),ahat_benchmark.__file__
rows=[json.loads(l) for l in (PROJECT_DIR/'benchmarks/ahat_eval_set.jsonl').read_text().splitlines()]
assert len(rows)==json.loads((PROJECT_DIR/'benchmark_manifest.json').read_text())['active_case_count']
val=PROJECT_DIR/'vendor/val/Validate'
counts={'valid':0,'native_goals':0,'liquid_replay_steps':0}
for r in rows:
 domain=resolve_domain(r.get('domain_id'))
 result=validate_plan(scene_graph=r['scene_graph'],plan=r['plan'],domain_path=domain,val_executable=val,timeout_seconds=10)
 assert result['status']=='valid',(r['id'],result)
 counts['valid']+=1
 goals=r.get('reference_goal',[])+r.get('liquid_reference',{}).get('goals',[])
 if goals:
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);(p/'problem').write_text(result['problem_pddl'].replace('(:goal (and))','(:goal (and '+' '.join(goals)+'))'))
   (p/'plan').write_text('\n'.join(r['plan']))
   env={**os.environ,'LD_LIBRARY_PATH':str(val.parent)}
   checked=subprocess.run([str(val),'-v',str(domain),str(p/'problem'),str(p/'plan')],capture_output=True,text=True,env=env,timeout=10)
   assert checked.returncode==0 and 'Successful plans:' in checked.stdout,(r['id'],checked.stdout[-1000:])
  counts['native_goals']+=1
 if r.get('domain_id')==LIQUID_DOMAIN:
  manager=SceneGraphManager(r['scene_graph'],str(domain))
  for i,text in enumerate(r['plan']):
   a=sexpr(text);manager.apply_action(a[0],a[1:])
   assert final_state(full_problem(manager.scene_graph,domain),[],domain)==final_state(result['problem_pddl'],r['plan'][:i+1],domain)
   counts['liquid_replay_steps']+=1
class Fake:
 base_url='https://mock.invalid/v1'
 def __init__(self):self.calls=[];self.chat=SimpleNamespace(completions=SimpleNamespace(create=self.create))
 def create(self,**kw):
  self.calls.append(kw)
  return SimpleNamespace(id='mock',model='mock',usage=None,choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({'score':1,'rationale':'offline routing check','critical_failure':False})))])
with tempfile.TemporaryDirectory() as directory:
 folder=Path(directory);out=export_inputs('ahat-medium',folder/'export.json')
 assert set(out['domains'])=={BASE_DOMAIN,LIQUID_DOMAIN}
 assert all('plan' not in r and 'reference_goal' not in r and 'liquid_reference' not in r for r in out['cases'])
 chosen=[next(r for r in rows if not r.get('domain_id')),next(r for r in rows if r.get('domain_id')==LIQUID_DOMAIN)]
 data=[{k:r[k] for k in ('id','instruction','scene_graph','domain_id') if k in r} for r in chosen]
 raw=json.dumps(data).encode();(folder/'cases.json').write_bytes(raw)
 (folder/'manifest.json').write_text(json.dumps({'case_count':2,'data_sha256':hashlib.sha256(raw).hexdigest()}))
 (folder/'registry.yaml').write_text('datasets:\n  mixed: cases.json\n')
 inference=folder/'inference.json';inference.write_text(json.dumps({'results':[{'id':r['id'],'plan':r['plan'],**domain_binding(r.get('domain_id'))} for r in chosen]}))
 shared=dict(dataset='mixed',inference_path=inference,registry_path=folder/'registry.yaml')
 base=resolve_domain(BASE_DOMAIN);vp=folder/'val.json';jp=folder/'judge.json'
 run_val_stage(**shared,output_path=vp,domain_path=base,val_executable=val,timeout_seconds=10,workers=2)
 client=Fake();e=RubricEvaluator(client=client,model='mock',domain_path=base,max_attempts=1)
 run_judge_stage(**shared,val_results_path=vp,output_path=jp,evaluator=e,workers=2)
 result=summarize(**shared,val_results_path=vp,judge_results_path=jp,output_path=folder/'final.json',domain_path=base)
 assert result['statistics']['system_errors']==0,result
 assert set(result['statistics']['by_domain'])=={BASE_DOMAIN,LIQUID_DOMAIN}
 for prompt in [*PROMPTS.values(),*LIQUID_PROMPTS.values()]:assert any(c['messages'][0]['content']==prompt for c in client.calls)
counts['mixed_pipeline']='passed_mock_judge_real_VAL';counts['reference_free_export']='passed'
print(json.dumps(counts))
