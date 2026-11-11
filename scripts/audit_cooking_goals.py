#!/usr/bin/env python3
"""Check the two semantically reviewed references and deferred-case evidence.

VAL checks reachability, not natural-language sufficiency. The manual coverage
arguments and model limits are in docs/heated.md. This script guards
their domain/scene premises and checks reference witnesses and counterexamples.
It never writes benchmark tasks. Run with PYTHONPATH=src.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path

from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.judge.evaluator import build_inputs
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import PDDLDomainParser, SceneGraphManager
from check_reference_plans import DOMAIN, ROOT, VAL, native_goal
from repair_cooking import (ADDITIONAL_TWO_SERVING_FOODS, BREAKFAST, CONFIRMED_GOAL_IDS,
                            GROUP_SERVING_FOODS, REHEAT, WARM_BRUNCH, TWO_SERVING_FOODS, repair_cases)


INVENTORY = ROOT / 'docs/validation/cooking_goal_inventory.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def literals(expr, negative=False):
    """Walk domain effects, retaining polarity (including quantified effects)."""
    if expr[0] == 'and':
        for child in expr[1:]:
            yield from literals(child, negative)
    elif expr[0] == 'not':
        yield from literals(expr[1], not negative)
    elif expr[0] == 'forall':
        yield from literals(expr[2], negative)
    elif expr[0] == 'when':
        yield from literals(expr[2], negative)
    else:
        yield negative, tuple(expr)


def domain_premises(domain_path=DOMAIN):
    parsed = PDDLDomainParser(domain_path.read_text())
    changes = [(name, neg, atom) for name, action in parsed.actions.items()
               for neg, atom in literals(action['effect'])]
    heats = {'heat_with_microwave', 'heat_with_oven', 'heat_on_heating_device'}
    require('cooked' not in parsed.predicates and not any(n.startswith('cook_') for n in parsed.actions),
            'Removed doneness model reintroduced')
    require({n for n, neg, a in changes if not neg and a[0] == 'heated'} == heats,
            'Heating producer set changed; repeat semantic review')
    require('serves_two' in parsed.predicates, 'Two-serving predicate is missing')
    require('serves_group' in parsed.predicates, 'Group-serving predicate is missing')
    immutable = {'is_food', 'serves_two', 'serves_group', 'can_be_heated', 'is_heating_device', 'is_oven',
                 'is_microwave', 'is_cooking_surface', 'can_be_moved'}
    require(not any(a[0] in immutable or (neg and a[0] == 'heated')
                    for _, neg, a in changes), 'Capability/result invariants changed')
    for name in heats:
        pre = parsed.actions[name]['precondition']
        require(['can_be_heated', '?o'] in pre and ['not', ['heated', '?o']] in pre
                and ['is_food', '?o'] not in pre, f'{name}: unified heating guard changed')
    oven = parsed.actions['heat_with_oven']['precondition']
    for fact in [['is_oven', '?d'], ['is_heating_device', '?d'], ['is_powered_on', '?d'],
                 ['not', ['is_open', '?d']], ['item_in_receptacle', '?o', '?d']]:
        require(fact in oven, 'Oven method premises changed')
    require({n for n, neg, a in changes if neg and a[0] == 'is_powered_on'} == {'power_off'},
            'Power-off producer changed')
    return {'heated_producers': sorted(heats), 'single_thermal_result': True,
            'capabilities_immutable': True, 'heated_never_deleted': True}


def validate(row, plan):
    result = validate_plan(scene_graph=row['scene_graph'], plan=plan, domain_path=DOMAIN,
                           val_executable=VAL, timeout_seconds=10)
    require(result['status'] == 'valid', f"{row['id']}: {result.get('fail_reason')}")
    return result['problem_pddl']


def audit(rows, baseline=None):
    cases = {r['id']: r for r in rows}
    inventory = json.loads(INVENTORY.read_text())
    pruning = json.loads((ROOT / 'docs/validation/meal_pruning_inventory.json').read_text())
    approved_removals = {r['id'] for r in pruning['records'] if r['proposal'] == 'remove'}
    liquid_pruning = json.loads((ROOT / 'docs/validation/liquid_pruning_inventory.json').read_text())
    approved_removals |= {r['id'] for r in liquid_pruning['records'] if r['decision'] == 'remove'}
    missing_ids = {r['id'] for r in inventory['records']} - set(cases)
    require(missing_ids <= approved_removals, 'Unapproved task missing from historical inventory')
    active_records = [r for r in inventory['records'] if r['id'] in cases]
    for item in active_records:
        row = cases[item['id']]
        require((row['instruction'], row['type']) == (item['instruction'], item['split']),
                'Inventory instruction or split changed; repeat manual review')
    confirmed = {r['id'] for r in active_records if r['decision'] == 'confirmed'}
    require(confirmed == set(CONFIRMED_GOAL_IDS), 'Confirmed inventory differs from repair scope')
    premises = domain_premises()
    for row in rows:
        require(not any(sexpr(a)[0].startswith('cook_') for a in row['plan']), 'Old cook action in reference')
        require(not any('cooked' in sexpr(g) for g in row.get('reference_goal', [])), 'Old cooked goal')
        for group, nodes in row['scene_graph'].items():
            if group == 'links' or not isinstance(nodes, list):
                continue
            for node in nodes:
                if isinstance(node, dict):
                    states = node.get('states') or {}
                    require('cooked' not in states and 'is_heated' not in states, 'Obsolete scene thermal state')
    if baseline is not None:
        removed_from_baseline = {r['id'] for r in baseline} - set(cases)
        require(removed_from_baseline <= approved_removals, 'Unapproved baseline task removed')
        expected_baseline = [r for r in baseline if r['id'] not in removed_from_baseline]
        require([r['id'] for r in expected_baseline] == [r['id'] for r in rows], 'Task IDs/order changed')
        require(all((a['instruction'], a['type']) == (b['instruction'], b['type'])
                    for a, b in zip(expected_baseline, rows)), 'Instruction/split changed')
        require(repair_cases(expected_baseline) == rows, 'Changes exceed approved pruning and scene/reference migration')

    records = []
    for case_id in CONFIRMED_GOAL_IDS:
        row = cases[case_id]
        problem = validate(row, row['plan'])
        initial = {tuple(f) for f in final_state(problem, [], DOMAIN)}
        require(native_goal(problem, row['plan'], row['reference_goal']), 'Reference misses goal')
        food = 'breakfast_eggs_1' if case_id == BREAKFAST else 'casserole_21'
        require(('heated', food) not in initial, 'Initially heated: witness would not prove processing')
        if case_id == REHEAT:
            devices = {f[1] for f in initial if f[0] in
                       {'is_oven', 'is_microwave', 'is_cooking_surface'}}
            require(devices == {'oven_30'}, 'No longer a unique possible processing device')
            require(not any(f[0] == 'can_be_moved' for f in initial), 'Room invariance needs review')
            for fact in [('furniture_in_room', 'counter_40', 'dining_room_1'),
                         ('item_in_receptacle', food, 'counter_40'),
                         ('furniture_in_room', 'oven_30', 'kitchen_1'),
                         ('furniture_in_room', 'table_29', 'dining_room_1')]:
                require(fact in initial, f'Missing initial premise: {fact}')
            positions = [row['plan'].index(a) for a in [
                '(heat_with_oven robot1 casserole_21 oven_30)',
                '(power_off robot1 oven_30)',
                '(place_on_surface robot1 casserole_21 table_29)']]
            require(positions == sorted(positions), 'Reference heating/off/return order changed')
        else:
            require(('is_food', food) in initial, 'Breakfast must use actual food')

        controls = {'omit_processing': [a for a in row['plan']
                    if not sexpr(a)[0].startswith('heat_')]}
        if case_id == BREAKFAST:
            controls['omit_power_off'] = [a for a in row['plan'] if not a.startswith('(power_off ')]
            controls['omit_serving'] = row['plan'][:-4]
        else:
            controls['omit_power_off'] = [a for a in row['plan'] if not a.startswith('(power_off ')]
            controls['return_to_wrong_room'] = [a.replace('table_29', 'counter_23') for a in row['plan']]
        for name, plan in controls.items():
            validate(row, plan)
            require(not native_goal(problem, plan, row['reference_goal']), f'{name} unexpectedly meets goal')

        manager = SceneGraphManager(row['scene_graph'], str(DOMAIN))
        for i, text in enumerate(row['plan'], 1):
            action = sexpr(text)
            manager.apply_action(action[0], action[1:])
            require(final_state(full_problem(manager.scene_graph, DOMAIN), [], DOMAIN) ==
                    final_state(problem, row['plan'][:i], DOMAIN), 'Scene/PDDL replay mismatch')
        records.append({'id': case_id, 'reference_goal': row['reference_goal'], 'plan': row['plan'],
                        'native_val_valid': True, 'goal_reached': True,
                        'legal_controls_missing_goal': list(controls), 'scene_replay_steps': len(row['plan']),
                        'semantic_status': 'manually_reviewed_sufficient_within_symbolic_model_not_necessary'})

    warm = cases[WARM_BRUNCH]
    require('(heated breakfast_eggs_1)' in warm['reference_goal'], 'Warm-brunch goal omits heated eggs')
    portion_checks = []
    for case_id, food in TWO_SERVING_FOODS.items():
        row = cases[case_id]
        problem = validate(row, row['plan'])
        state = final_state(problem, row['plan'], DOMAIN)
        goal = f'(serves_two {food})'
        require(goal in row['reference_goal'], 'Reference omits two-serving capacity')
        require(['serves_two', food] in state, 'Two-serving capacity lost during execution')
        d1 = build_inputs(row['instruction'], row['scene_graph'], row['plan'], state)['D1']
        require(goal in d1, 'D1 cannot see two-serving capacity')
        require(native_goal(problem, row['plan'], row['reference_goal']), 'Two-serving reference misses goal')
        # The same legal plan without the initial capacity declaration must fail
        # the strengthened target. No action is allowed to invent portion size.
        missing = copy.deepcopy(row)
        node = next(n for n in missing['scene_graph']['objects'] if n['name'] == food)
        node['states']['serves_two'] = False
        missing_problem = validate(missing, missing['plan'])
        require(not native_goal(missing_problem, missing['plan'], row['reference_goal']),
                'Missing quantity declaration passes reference goal')
        heat_index = next(i for i, a in enumerate(row['plan']) if sexpr(a)[0].startswith('heat_'))
        controls = {'omit_processing': [a for a in row['plan'] if not sexpr(a)[0].startswith('heat_')],
                    'omit_serving': row['plan'][:heat_index + 2]}
        for name, plan in controls.items():
            validate(row, plan)
            require(['serves_two', food] in final_state(problem, plan, DOMAIN),
                    f'{name}: control lost static capacity')
            require(not native_goal(problem, plan, row['reference_goal']),
                    f'{name}: capacity alone passes reference goal')
        portion_checks.append({'id': case_id, 'food': food, 'd1_contains': goal,
                               'reference_goal_passed': True, 'missing_capacity_control_valid': True,
                               'missing_capacity_control_misses_goal': True,
                               'legal_controls_with_capacity_missing_goal': list(controls)})

    group_checks = []
    for mapping, pred in [(ADDITIONAL_TWO_SERVING_FOODS, 'serves_two'),
                          (GROUP_SERVING_FOODS, 'serves_group')]:
        for case_id, food in mapping.items():
            row = cases[case_id]
            problem = validate(row, row['plan'])
            state = final_state(problem, row['plan'], DOMAIN)
            fact = f'({pred} {food})'
            require([pred, food] in state and ['is_food', food] in state,
                    'Named food capacity missing from final state')
            require(['heated', food] not in final_state(problem, [], DOMAIN),
                    'Portion declaration invented initial processing')
            require(fact in build_inputs(row['instruction'], row['scene_graph'], row['plan'], state)['D1'],
                    'D1 cannot see food capacity')
            require(native_goal(problem, row['plan'], [fact]), 'Static capacity witness failed')
            missing = copy.deepcopy(row)
            next(n for n in missing['scene_graph']['objects'] if n['name'] == food)['states'][pred] = False
            missing_problem = validate(missing, missing['plan'])
            require(not native_goal(missing_problem, missing['plan'], [fact]),
                    'False capacity was inferred')
            group_checks.append({'id': case_id, 'food': food, 'capacity_predicate': pred,
                                 'native_plan_valid': True, 'd1_contains': fact,
                                 'false_capacity_control_valid_and_missing_fact': True,
                                 'whole_instruction_sufficiency_certified': False})

    # One heat action completes the thermal subtask, including eggs; the explicit
    # serving-capacity annotation does not replace actual processing.
    reference_problem = validate(warm, warm['plan'])
    require(native_goal(reference_problem, warm['plan'], warm['reference_goal']), 'Warm-brunch reference misses goal')
    control = [a for a in warm['plan'] if not sexpr(a)[0].startswith('heat_')]
    validate(warm, control)
    require(not native_goal(reference_problem, control, warm['reference_goal']), 'Warm-brunch goal accepts no processing')
    return {'kind': 'manual_semantic_review_with_native_witnesses_not_llm_scores',
            'revision': 'liquid-pruning-v1', 'inventory_revision': inventory['revision'], 'task_count': len(rows),
            'historical_inventory_count': len(inventory['records']),
            'approved_pruned_inventory_count': len(missing_ids),
            'group_counts': dict(Counter(r['group'] for r in active_records)),
            'explicit_food_thermal_requirements': sum(r['explicit_food_thermal_requirement'] for r in active_records),
            'confirmed_count': len(confirmed),
            'deferred_meal_candidates': sum(r['decision'] == 'deferred' for r in active_records),
            'baseline_preservation_checked': baseline is not None, 'domain_premises': premises,
            'confirmed_references': records,
            'two_serving_checks': portion_checks,
            'additional_portion_checks': group_checks,
            'warm_brunch_check': {'id': WARM_BRUNCH, 'reference_goal': warm['reference_goal'],
                                  'reference_plan_reaches_goal': True, 'no_processing_control_misses_goal': True,
                                  'semantic_status': 'two_serving_capacity_explicit_reference_goal_reached'}}


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'benchmarks/ahat_eval_set.jsonl')
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/cooking-goal-audit/checks.json')
    args = parser.parse_args()
    result = audit(read_rows(args.source), read_rows(args.baseline) if args.baseline else None)
    result['source_sha256'] = hashlib.sha256(args.source.read_bytes()).hexdigest()
    result['baseline_sha256'] = hashlib.sha256(args.baseline.read_bytes()).hexdigest() if args.baseline else None
    result['implementation_sha256'] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in [DOMAIN, INVENTORY, ROOT / 'docs/validation/meal_pruning_inventory.json',
                                                ROOT / 'docs/validation/liquid_pruning_inventory.json', Path(__file__),
                                                ROOT / 'scripts/repair_cooking.py',
                                                ROOT / 'scripts/check_reference_plans.py',
                                                *sorted((ROOT / 'src/ahat_benchmark').rglob('*.py'))]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['task_count', 'group_counts', 'explicit_food_thermal_requirements',
                                          'confirmed_count', 'deferred_meal_candidates']}))


if __name__ == '__main__':
    main()
