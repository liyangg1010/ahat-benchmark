#!/usr/bin/env python3
"""Add explicit dinner foods to three scenes; preserve instructions and references.

Dry-run by default. --write validates candidate scenes and independent food-use
witnesses before changing data. Witnesses are not task completion certificates.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from ahat_benchmark.domains import domain_registry, task_domain
from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.scene import normalize_links
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from check_reference_plans import native_goal
from repair_cooking import CookingPlan

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'dinner-food-v1'
DESIGNS = {
    'a55dd1af-59ee-4e0c-8139-208e2134ed49': {
        'fridge': 'refrigerator_19', 'stove': 'stove_49', 'pot': 'cooking_pot_72',
        'plate': 'plate_set_37', 'table': 'dining_table_16',
        'foods': [('chicken_breast_162', 'meat'), ('potatoes_163', 'potato'), ('broccoli_164', 'vegetables')],
    },
    '3cf1736a-3b96-4913-b9c5-df4688ee9053': {
        'fridge': 'refrigerator_32', 'stove': 'stove_33', 'pot': 'pot_63',
        'plate': 'plate_143', 'table': 'dining_table_18',
        'foods': [('salmon_fillet_220', 'seafood'), ('potatoes_221', 'potato')],
    },
    '4a3dc074-3cd6-4241-a4a5-2c37f31c99a1': {
        'fridge': 'refrigerator_14', 'stove': 'stove_15', 'pot': 'cooking_pot_13',
        'plate': 'plate_set_15', 'table': 'dining_table_19',
        'foods': [('beef_steak_99', 'meat'), ('potatoes_100', 'potato'), ('green_beans_101', 'vegetables')],
    },
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def repair(row):
    result = copy.deepcopy(row)
    if row['id'] not in DESIGNS:
        return result
    design = DESIGNS[row['id']]
    graph = result['scene_graph']
    nodes = {n['name']: n for k, values in graph.items() if k != 'links' and isinstance(values, list)
             for n in values if isinstance(n, dict) and 'name' in n}
    require(design['fridge'] in nodes, 'Missing designated refrigerator')
    for name, kind in design['foods']:
        node = {'name': name, 'type': kind, 'states': {
            'is_food': True, 'can_be_heated': True, 'heated': False,
            'is_clean': True, 'can_be_moved': True,
        }}
        if name in nodes:
            require(nodes[name] == node and node in graph['objects'], f'Conflicting existing food: {name}')
        else:
            graph['objects'].append(node)
        edge = {'relation': 'in', 'from': name, 'to': design['fridge']}
        locations = [link for link in normalize_links(graph)
                     if link.get('from') == name and link['relation'] in {'on', 'in'}]
        require(not locations or locations == [edge], f'Conflicting food location: {name}')
        if not locations:
            graph['links'].append(edge)
    return result


def check_candidate(before, after):
    design = DESIGNS[after['id']]
    domain = task_domain(after)
    dropped = []
    problem = full_problem(after['scene_graph'], domain, dropped)
    require(not dropped, 'Candidate initial facts were dropped')
    old_problem = full_problem(before['scene_graph'], domain)
    old_initial = {tuple(f) for f in final_state(old_problem, [], domain)}
    initial = {tuple(f) for f in final_state(problem, [], domain)}
    added_names = {name for name, _ in design['foods']}
    require(old_initial <= initial and all(f[1] in added_names for f in initial - old_initial),
            'Unexpected initial-state change')
    original_reference = validate_plan(scene_graph=after['scene_graph'], plan=after['plan'], domain_path=domain,
                                       val_executable=ROOT / 'vendor/val/Validate', timeout_seconds=10)
    require(original_reference['status'] == 'valid', 'Original reference no longer valid')
    end = {tuple(f) for f in final_state(problem, after['plan'], domain)}
    old_end = {tuple(f) for f in final_state(old_problem, before['plan'], domain)}
    require(end - old_end == initial - old_initial and old_end <= end, 'Existing reference outcome changed')

    builder = CookingPlan(after['scene_graph'])
    builder.move(design['plate'], design['table'])
    goals = [f"(item_on_surface {design['plate']} {design['table']})", f"(not (is_powered_on {design['stove']}))"]
    for name, _ in design['foods']:
        require(('is_food', name) in initial and ('can_be_heated', name) in initial and ('heated', name) not in initial,
                f'Incorrect initial food states: {name}')
        builder.heat_and_serve(name, design['pot'], design['stove'], design['plate'])
        goals += [f'(is_food {name})', f'(heated {name})', f"(item_on_surface {name} {design['plate']})"]
    checked = validate_plan(scene_graph=after['scene_graph'], plan=builder.plan, domain_path=domain,
                            val_executable=ROOT / 'vendor/val/Validate', timeout_seconds=10)
    require(checked['status'] == 'valid', f"Food witness invalid: {checked.get('fail_reason')}")
    require(native_goal(problem, builder.plan, goals, domain), 'Food-use witness goals not reached')
    replay_steps = 0
    for plan in (after['plan'], builder.plan):
        manager = SceneGraphManager(after['scene_graph'], str(domain))
        for i, text in enumerate(plan):
            action = sexpr(text)
            manager.apply_action(action[0], action[1:])
            require(final_state(full_problem(manager.scene_graph, domain), [], domain) ==
                    final_state(problem, plan[:i + 1], domain), 'Scene/PDDL replay mismatch')
            replay_steps += 1
    return {'id': after['id'], 'instruction': after['instruction'], 'design': design,
            'added_nodes': [n for n in after['scene_graph']['objects'] if n['name'] in added_names],
            'added_initial_facts': sorted(initial - old_initial),
            'original_reference_valid': True, 'old_reference_facts_preserved': True,
            'food_use_witness': {'plan': builder.plan, 'goals': goals, 'native_val_valid': True,
                                 'goals_reached': True, 'scope': 'Added foods can be heated and plated; not a full task reference.'},
            'scene_replay_steps': replay_steps}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    source = ROOT / 'benchmarks/ahat_eval_set.jsonl'
    lines = source.read_text().splitlines(keepends=True)
    rows = list(map(json.loads, lines))
    require(set(DESIGNS) <= {r['id'] for r in rows}, 'Missing dinner task')
    updated = [repair(row) for row in rows]
    changed = [i for i, pair in enumerate(zip(rows, updated)) if pair[0] != pair[1]]
    print(json.dumps({'revision': REVISION, 'changed_ids': [rows[i]['id'] for i in changed],
                      'added_food_nodes': sum(len(DESIGNS[rows[i]['id']]['foods']) for i in changed)}))
    if not args.write or not changed:
        return
    require(len(changed) == 3, 'Partial migration; inspect before writing')
    baseline_hash = sha(source)
    domains = domain_registry()
    records = []
    for index in changed:
        record = check_candidate(rows[index], updated[index])
        record.update(source_index=index, split='open',
                      split_index=sum(r['type'] == 'open' for r in rows[:index]))
        records.append(record)
        require({k: v for k, v in rows[index].items() if k != 'scene_graph'} ==
                {k: v for k, v in updated[index].items() if k != 'scene_graph'}, 'Changed non-scene fields')
    require(all(sha(ROOT / d['path']) == d['sha256'] for d in domains.values()), 'Domain changed')
    original_lines = list(lines)
    for index in changed:
        lines[index] = json.dumps(updated[index], ensure_ascii=False) + '\n'
    require(all(lines[i] == original_lines[i] for i in range(len(rows)) if i not in changed), 'Other source lines changed')
    source.write_text(''.join(lines))
    cases_path = ROOT / 'benchmarks/ahat-open/cases.json'
    cases = [{k: row[k] for k in ('id', 'instruction', 'scene_graph', 'domain_id') if k in row}
             for row in updated if row['type'] == 'open']
    write_json(cases_path, cases)
    manifest_path = cases_path.with_name('manifest.json')
    manifest = json.loads(manifest_path.read_text())
    manifest.update(version='1.10.1', data_sha256=sha(cases_path), local_dinner_food=REVISION)
    write_json(manifest_path, manifest)
    report_path = ROOT / 'docs/validation/dinner_food_v1_checks.json'
    report = {'revision': REVISION, 'base_source_sha256': baseline_hash, 'source_sha256': sha(source),
              'domains_unchanged': domains, 'task_count': len(rows), 'changed_cases': len(changed),
              'added_food_nodes': 8, 'other_source_lines_unchanged': len(rows) - len(changed),
              'instructions_plans_goals_unchanged': True, 'records': records, 'failures': []}
    write_json(report_path, report)
    sync_path = ROOT / 'benchmarks/hf_sync.json'
    sync = json.loads(sync_path.read_text())
    sync['local_dinner_food'] = {'revision': REVISION, 'ids': list(DESIGNS), 'added_food_nodes': 8,
        'base_data_sha256': baseline_hash, 'result_data_sha256': sha(source),
        'report_path': str(report_path.relative_to(ROOT)), 'report_sha256': sha(report_path),
        'script_sha256': sha(Path(__file__))}
    for artifact in sync['artifacts']:
        artifact['sha256'] = sha(ROOT / 'benchmarks' / artifact['path'])
    write_json(sync_path, sync)
    print(json.dumps({'validated_cases': len(records), 'scene_replay_steps': sum(r['scene_replay_steps'] for r in records),
                      'witnesses_reached': len(records), 'other_source_lines_unchanged': len(rows) - len(changed)}))


if __name__ == '__main__':
    main()
