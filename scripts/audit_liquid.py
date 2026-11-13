#!/usr/bin/env python3
"""Validate liquid witnesses, omission controls, scene replay and base isolation."""
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter
from ahat_benchmark.domains import resolve_domain, LIQUID_DOMAIN
from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from ahat_benchmark.val.validator import validate_plan
from check_reference_plans import native_goal

ROOT=Path(__file__).resolve().parents[1]
VAL=ROOT/'vendor/val/Validate'
BASE=ROOT/'vendor/pddl/domain_0102_test.pddl'
CRITICAL={'heat_liquid_in_kettle','heat_liquid_on_stove','load_tea','load_coffee','brew_tea','dispense_from_device','fill_from_faucet','fill_device_with_water','pour_into','water_plant','prepare_instant_noodles','inspect_water_container'}

def audit(rows,baseline=None,inventory=None):
    counts=Counter();failures=[];records=[]
    for r in rows:
        if 'liquid_reference' not in r:continue
        domain=resolve_domain(r.get('domain_id'));spec=r['liquid_reference']
        checked=validate_plan(scene_graph=r['scene_graph'],plan=r['plan'],domain_path=domain,val_executable=VAL,timeout_seconds=10)
        record={'id':r['id'],'domain_id':r.get('domain_id'),'valid':checked['status']=='valid'}
        if checked['status']!='valid':failures.append([r['id'],'invalid',checked.get('fail_reason')]);continue
        problem=checked['problem_pddl']
        reached=native_goal(problem,r['plan'],spec['goals'],domain)
        if not reached:failures.append([r['id'],'reference outcomes not reached'])
        counts['reference_outcomes_reached']+=reached
        cursor=0
        for required in spec['required_actions']:
            try:cursor=r['plan'].index(required,cursor)+1
            except ValueError:failures.append([r['id'],'missing/out-of-order reference action',required])
        manager=SceneGraphManager(r['scene_graph'],str(domain))
        for i,step in enumerate(r['plan']):
            a=sexpr(step);manager.apply_action(a[0],a[1:])
            if final_state(full_problem(manager.scene_graph,domain),[],domain)!=final_state(problem,r['plan'][:i+1],domain):
                failures.append([r['id'],'scene replay mismatch',i])
            counts['scene_replay_steps']+=1
        controls=[]
        for i,step in enumerate(r['plan']):
            if sexpr(step)[0] not in CRITICAL:continue
            plan=r['plan'][:i]+r['plan'][i+1:]
            result=validate_plan(scene_graph=r['scene_graph'],plan=plan,domain_path=domain,val_executable=VAL,timeout_seconds=10)
            outcome_missed=result['status']=='invalid' or (result['status']=='valid' and not native_goal(problem,plan,spec['goals'],domain))
            # Some earlier methods are instructions even if a later step yields the same state.
            # The ordered action witness catches those; final goals alone are not called sufficient.
            stage_missed=step in spec['required_actions'] and plan.count(step)<r['plan'].count(step)
            if not outcome_missed and not stage_missed:failures.append([r['id'],'undetected omitted processing',step])
            if result['status'] not in ('valid','invalid'):failures.append([r['id'],'control infrastructure error',result['status']])
            controls.append({'omitted':step,'invalid_or_outcome_missed':outcome_missed,'required_stage_missed':stage_missed})
            counts['omission_controls']+=1
        record.update(outcomes_reached=reached,controls=controls);records.append(record)
    if baseline is not None:
        old={r['id']:r for r in baseline};current={r['id']:r for r in rows}
        inventory_path=inventory or ROOT/'docs/validation/liquid_v1_inventory.json'
        inv=json.loads(inventory_path.read_text()) if inventory_path.exists() else json.loads((ROOT/'outputs/liquid-v1/candidate_review.json').read_text())
        decisions={r['id']:r['decision'] for r in inv['records']}
        allowed={k for k,v in decisions.items() if v in ('migrate','repair_equipment','quarantine')}
        if set(old)-set(current)!={k for k,v in decisions.items() if v=='quarantine'}:failures.append(['unexpected removal'])
        if set(current)-set(old):failures.append(['unexpected addition'])
        if [r['id'] for r in rows] != [r['id'] for r in baseline if r['id'] in current]:failures.append(['task order changed'])
        for r in rows:
            prev=old[r['id']]
            if (r['instruction'],r['type'])!=(prev['instruction'],prev['type']):failures.append([r['id'],'intent/split changed'])
            if r['id'] not in allowed:
                if r!=prev:failures.append([r['id'],'ordinary record changed'])
                # Verify old and current ordinary references produce identical facts.
                old_state=final_state(full_problem(prev['scene_graph'],BASE),prev['plan'],BASE)
                new_state=final_state(full_problem(r['scene_graph'],resolve_domain(r.get('domain_id'))),r['plan'],resolve_domain(r.get('domain_id')))
                if old_state!=new_state:failures.append([r['id'],'ordinary final state changed'])
                counts['unchanged_records_and_states']+=1
    return {'kind':'offline_liquid_witness_validation_not_llm_scores','counts':dict(counts),'cases':records,'failures':failures}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=ROOT/'benchmarks/ahat_eval_set.jsonl');p.add_argument('--baseline',type=Path);p.add_argument('--inventory',type=Path);p.add_argument('--output',type=Path,default=ROOT/'docs/validation/liquid_v1_checks.json');a=p.parse_args()
    read=lambda path:[json.loads(l) for l in path.read_text().splitlines()]
    result=audit(read(a.source),read(a.baseline) if a.baseline else None,a.inventory)
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    result['source_sha256']=digest(a.source)
    result['baseline_sha256']=digest(a.baseline) if a.baseline else None
    result['domains']={name:digest(resolve_domain(name)) for name in ('ahat-v8-group-portions',LIQUID_DOMAIN)}
    result['implementation_sha256']={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'scripts/repair_liquid.py',ROOT/'scripts/build_liquid_domain.py',*sorted((ROOT/'src/ahat_benchmark').rglob('*.py'))]}
    if a.baseline:
        old_lines={json.loads(line)['id']:line for line in a.baseline.read_bytes().splitlines(keepends=True)}
        unchanged=0
        for line in a.source.read_bytes().splitlines(keepends=True):
            row=json.loads(line)
            if 'liquid_reference' not in row:
                if line!=old_lines[row['id']]:result['failures'].append([row['id'],'unchanged source line rewritten'])
                unchanged+=1
        result['counts']['unchanged_raw_lines']=unchanged
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'counts':result['counts'],'failures':result['failures']}));raise SystemExit(bool(result['failures']))
