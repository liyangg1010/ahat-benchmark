#!/usr/bin/env python3
"""Validate three concrete group-meal examples before adoption with --write.

Outcome goals are offline witnesses, not a mandatory menu or runtime scoring gate.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from ahat_benchmark.domains import domain_registry, task_domain
from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from check_reference_plans import native_goal
from repair_cooking import CookingPlan

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'group-meal-reference-v1'
DESIGNS = {
    'f3ee3e87-d782-4870-8ed3-2bc92f344010': {
        'table': 'dining_table_19', 'dish': 'fruit_bowl_74', 'pot': 'pot_37', 'stove': 'stove_26',
        'fridge': 'refrigerator_32', 'capacity': 'serves_two',
        'heat': ['eggs_116', 'potatoes_122', 'vegetables_123'], 'serve': [],
        'added': [('potatoes_122', 'potato'), ('vegetables_123', 'vegetables')],
        'capacity_foods': ['eggs_116', 'potatoes_122', 'vegetables_123'],
        'decor': ['centerpiece_27'], 'light': 'candle_29',
    },
    '0cf41a97-9f6a-4e13-8542-1def6889483d': {
        'table': 'dining_table_52', 'dish': 'fruit_bowl_30', 'pot': 'pot_132', 'stove': 'stove_26',
        'fridge': 'refrigerator_46', 'capacity': 'serves_two',
        'heat': ['eggs_66'], 'serve': ['apple_180'], 'added': [],
        'capacity_foods': ['eggs_66'], 'decor': [], 'light': 'candle_set_28',
    },
    '198fd035-6f65-4740-8b01-0643a215ccb4': {
        'table': 'dining_table_19', 'dish': 'plate_86', 'pot': 'pot_30', 'stove': 'stove_22',
        'fridge': 'refrigerator_35', 'capacity': 'serves_group',
        'heat': ['eggs_90'], 'serve': ['bread_115', 'butter_92'],
        'added': [('bread_115', 'bread')], 'capacity_foods': ['eggs_90', 'bread_115'],
        'decor': ['napkin_87'], 'light': None,
    },
}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def candidate(row):
    row = copy.deepcopy(row)
    d = DESIGNS[row['id']]
    graph = row['scene_graph']
    added = []
    for name, kind in d['added']:
        node = {'name': name, 'type': kind, 'states': {
            'is_food': True, 'can_be_heated': True, 'heated': False,
            'is_clean': True, 'can_be_moved': True, d['capacity']: True,
        }}
        existing = [n for n in graph['objects'] if n['name'] == name]
        edge = {'relation': 'in', 'from': name, 'to': d['fridge']}
        if existing:
            require(existing == [node] and edge in graph['links'], f'Conflicting food: {name}')
        else:
            graph['objects'].append(node)
            graph['links'].append(edge)
            added.append(node)
    b = CookingPlan(graph)
    if b.positions[d['dish']] != ('on', d['table']):
        b.move(d['dish'], d['table'])
    first_serving = None
    for food in d['heat']:
        b.move(food, d['pot'])
        b.navigate(d['stove'])
        b.act('power_on', d['stove'])
        b.act('heat_on_heating_device', food, d['pot'], d['stove'])
        b.act('power_off', d['stove'])
        if first_serving is None:
            first_serving = len(b.plan)
        b.move(food, d['dish'])
    for food in d['serve']:
        b.move(food, d['dish'])
    for item in d['decor']:
        if b.positions[item] != ('on', d['table']):
            b.move(item, d['table'])
    if d['light']:
        require(b.positions[d['light']] == ('on', d['table']), 'Candle must be at the meal table')
        b.navigate(d['light'])
        b.act('light_on', d['light'])
    initially_open = {n['name'] for n in b.nodes.values() if n.get('states', {}).get('is_open')}
    closed = sorted(b.opened - initially_open)
    for name in closed:
        b.navigate(name)
        b.act('close', name)
    goals = [f'(heated {f})' for f in d['heat']]
    for food in d['heat'] + d['serve']:
        goals += [f'(is_food {food})', f"(item_on_surface {food} {d['dish']})"]
    goals += [f"({d['capacity']} {f})" for f in d['capacity_foods']]
    goals += [f"(item_on_surface {d['dish']} {d['table']})", f"(is_clean {d['dish']})",
              f"(is_clean {d['table']})", f"(not (is_powered_on {d['stove']}))", f'(handempty {b.agent})']
    goals += [f'(not (is_open {name}))' for name in closed]
    goals += [f"(item_on_surface {item} {d['table']})" for item in d['decor']]
    if d['light']:
        goals += [f"(is_light_on {d['light']})", f"(item_on_surface {d['light']} {d['table']})"]
    controls = {'omit_heating': {'valid': True, 'final_goal_reached': False},
                'stop_before_serving': {'after_step': first_serving, 'valid': True, 'final_goal_reached': False},
                'missing_capacity': [{'food': f, 'predicate': d['capacity']} for f in d['capacity_foods']]}
    if d['light']:
        controls['omit_lighting'] = {'valid': True, 'final_goal_reached': False}
    row['plan'] = b.plan
    return row, {'id': row['id'], 'instruction': row['instruction'], 'design': d, 'added_nodes': added,
                 'plan': b.plan, 'final_goals': goals, 'stage_goals': [], 'controls': controls}


def verify(before, after, record):
    graph, plan, domain = after['scene_graph'], after['plan'], task_domain(after)
    dropped = []
    problem = full_problem(graph, domain, dropped)
    require(not dropped, 'Dropped initial facts')
    initial = {tuple(f) for f in final_state(problem, [], domain)}
    previous = {tuple(f) for f in final_state(full_problem(before['scene_graph'], domain), [], domain)}
    added_names = {n['name'] for n in record['added_nodes']}
    require(previous <= initial and all(f[1] in added_names for f in initial - previous), 'Unexpected initial change')

    def valid(steps, scene=graph):
        result = validate_plan(scene_graph=scene, plan=steps, domain_path=domain,
                               val_executable=ROOT / 'vendor/val/Validate', timeout_seconds=10)
        require(result['status'] == 'valid', result.get('fail_reason', 'Invalid plan'))
        return result['problem_pddl']

    valid(plan)
    goals = record['final_goals']
    require(native_goal(problem, plan, goals, domain), 'Candidate goals missed')
    heat_action = record['controls']['omit_heating'].get('action', 'heat_on_heating_device')
    for action in [heat_action] + (['light_on'] if record['design']['light'] else []):
        control = [s for s in plan if sexpr(s)[0] != action]
        valid(control)
        require(not native_goal(problem, control, goals, domain), 'Omission control passed goals')
    control = plan[:record['controls']['stop_before_serving']['after_step']]
    valid(control)
    require(not native_goal(problem, control, goals, domain), 'Unserved meal passed goals')
    for capacity in record['controls']['missing_capacity']:
        scene = copy.deepcopy(graph)
        node = next(n for n in scene['objects'] if n['name'] == capacity['food'])
        require(node['states'].pop(capacity['predicate']), 'Missing declared capacity')
        control_problem = valid(plan, scene)
        require(not native_goal(control_problem, plan, goals, domain), 'Missing-capacity control passed goals')
    manager = SceneGraphManager(graph, str(domain))
    for i, step in enumerate(plan, 1):
        action = sexpr(step)
        manager.apply_action(action[0], action[1:])
        require(final_state(full_problem(manager.scene_graph, domain), [], domain) ==
                final_state(problem, plan[:i], domain), 'Scene/PDDL replay mismatch')
    record.update(native_val_valid=True, goals_reached=True, scene_replay_steps=len(plan))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    source = ROOT / 'benchmarks/ahat_eval_set.jsonl'
    raw = source.read_bytes()
    lines = raw.splitlines(keepends=True)
    rows = list(map(json.loads, lines))
    domains = domain_registry()
    records, changes = [], []
    for i, row in enumerate(rows):
        if row['id'] not in DESIGNS:
            continue
        after, record = candidate(row)
        verify(row, after, record)
        if after == row:
            continue
        require({k: v for k, v in row.items() if k not in {'plan', 'scene_graph'}} ==
                {k: v for k, v in after.items() if k not in {'plan', 'scene_graph'}}, 'Unrelated fields changed')
        record.update(plan_before=row['plan'], source_index=i, status='accepted_reference_example')
        records.append(record)
        changes.append(i)
        rows[i] = after
    print(json.dumps({'changed_cases': len(changes), 'steps': [len(r['plan']) for r in records],
                      'added_nodes': sum(len(r['added_nodes']) for r in records)}))
    if not args.write or not changes:
        return
    require(len(changes) == 3, 'Partial migration; inspect before writing')
    require(source.read_bytes() == raw and domains == domain_registry(), 'Baseline changed')
    for i in changes:
        lines[i] = (json.dumps(rows[i], ensure_ascii=False) + '\n').encode()
    require(sum(a == b for a, b in zip(raw.splitlines(keepends=True), lines)) == len(rows) - 3,
            'Other source lines changed')
    source.write_bytes(b''.join(lines))
    cases = ROOT / 'benchmarks/ahat-open/cases.json'
    write(cases, [{k: r[k] for k in ('id', 'instruction', 'scene_graph', 'domain_id') if k in r}
                  for r in rows if r['type'] == 'open'])
    manifest_path = cases.with_name('manifest.json')
    manifest = json.loads(manifest_path.read_text())
    manifest.update(version='1.10.3', data_sha256=sha(cases), local_group_meal_reference=REVISION)
    write(manifest_path, manifest)
    report_path = ROOT / 'docs/validation/group_meal_reference_v1_adoption.json'
    write(report_path, {'revision': REVISION, 'base_source_sha256': hashlib.sha256(raw).hexdigest(),
                       'source_sha256': sha(source), 'domains_unchanged': domains,
                       'other_source_lines_unchanged': len(rows) - 3, 'reference_goals_not_added': True,
                       'records': records, 'failures': []})
    sync_path = ROOT / 'benchmarks/hf_sync.json'
    sync = json.loads(sync_path.read_text())
    sync['local_group_meal_reference'] = {
        'revision': REVISION, 'ids': list(DESIGNS), 'added_food_nodes': 3,
        'base_data_sha256': hashlib.sha256(raw).hexdigest(), 'result_data_sha256': sha(source),
        'report_path': str(report_path.relative_to(ROOT)), 'report_sha256': sha(report_path),
        'script_sha256': sha(Path(__file__)),
    }
    for artifact in sync['artifacts']:
        artifact['sha256'] = sha(ROOT / 'benchmarks' / artifact['path'])
    write(sync_path, sync)


if __name__ == '__main__':
    main()
