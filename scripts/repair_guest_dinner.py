#!/usr/bin/env python3
"""Validate the guest-dinner scene, plan and sufficient example goal; --write adopts them."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from ahat_benchmark.domains import domain_registry
from repair_cooking import CookingPlan
from repair_group_meal_references import require, sha, verify, write

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'guest-dinner-v1'
CASE_ID = 'dec162ab-e453-419f-971a-2e32987350f2'
FOODS = [('salmon_fillet_107', 'seafood'), ('potatoes_108', 'potato'), ('vegetables_109', 'vegetables')]
FRIDGE, OVEN = 'refrigerator_33', 'stove_oven_27'
PLATE, TABLE = 'plate_79', 'dining_table_14'


class DinnerPlan(CookingPlan):
    def into(self, obj, target):
        self.access(target)
        relation, source = self.positions[obj]
        if relation == 'in':
            self.access(source)
        self.navigate(obj)
        self.act('pick_from_receptacle' if relation == 'in' else 'pick_from_surface', obj, source)
        self.navigate(target)
        self.act('place_in_receptacle', obj, target)
        self.positions[obj] = ('in', target)

    def shut(self, target):
        if target in self.opened:
            self.navigate(target)
            self.act('close', target)
            self.opened.remove(target)


def candidate(before):
    row = copy.deepcopy(before)
    graph = row['scene_graph']
    added = []
    for name, kind in FOODS:
        node = {'name': name, 'type': kind, 'states': {
            'is_food': True, 'can_be_heated': True, 'heated': False,
            'is_clean': True, 'can_be_moved': True, 'serves_group': True,
        }}
        edge = {'relation': 'in', 'from': name, 'to': FRIDGE}
        existing = [n for n in graph['objects'] if n['name'] == name]
        if existing:
            require(existing == [node] and edge in graph['links'], f'Conflicting food: {name}')
        else:
            require(all(n.get('name') != name for key, nodes in graph.items() if key != 'links'
                        and isinstance(nodes, list) for n in nodes if isinstance(n, dict)), 'Name collision')
            graph['objects'].append(node)
            graph['links'].append(edge)
            added.append(node)
    b = DinnerPlan(graph)
    b.move(PLATE, TABLE)
    for food, _ in FOODS:
        b.into(food, OVEN)
    b.shut(OVEN)
    b.act('power_on', OVEN)
    for food, _ in FOODS:
        b.act('heat_with_oven', food, OVEN)
    b.act('power_off', OVEN)
    before_serving = len(b.plan)
    for food, _ in FOODS:
        b.move(food, PLATE)
    b.shut(OVEN)
    b.shut(FRIDGE)
    b.shut('kitchen_cabinet_set_30')
    b.navigate('candle_70')
    b.act('light_on', 'candle_70')
    goals = []
    for food, _ in FOODS:
        goals += [f'(is_food {food})', f'(serves_group {food})', f'(heated {food})',
                  f'(item_on_surface {food} {PLATE})']
    goals += [f'(item_on_surface {PLATE} {TABLE})', f'(is_clean {PLATE})', f'(is_clean {TABLE})',
              f'(furniture_in_room {TABLE} dining_room_7)',
              f'(not (is_powered_on {OVEN}))', f'(not (is_open {OVEN}))',
              f'(not (is_open {FRIDGE}))', '(not (is_open kitchen_cabinet_set_30))', '(handempty agent_0)']
    for item in ['tablecloth_67', 'centerpiece_vase_32', 'napkin_34', 'napkin_36', 'napkin_69']:
        require(b.positions[item] == ('on', TABLE), 'Expected existing table setting')
        goals += [f'(item_on_surface {item} {TABLE})', f'(is_clean {item})']
    goals += ['(is_light_on candle_70)', f'(item_on_surface candle_70 {TABLE})']
    row.update(plan=b.plan, reference_goal=goals)
    record = {'id': CASE_ID, 'instruction': row['instruction'], 'added_nodes': added,
              'design': {'foods': FOODS, 'fridge': FRIDGE, 'oven': OVEN, 'plate': PLATE,
                         'table': TABLE, 'light': 'candle_70'},
              'plan': b.plan, 'final_goals': goals, 'stage_goals': [], 'reference_goal_written': True,
              'controls': {
                  'omit_heating': {'action': 'heat_with_oven', 'valid': True, 'final_goal_reached': False},
                  'omit_lighting': {'valid': True, 'final_goal_reached': False},
                  'stop_before_serving': {'after_step': before_serving, 'valid': True, 'final_goal_reached': False},
                  'missing_capacity': [{'food': f, 'predicate': 'serves_group'} for f, _ in FOODS],
              }}
    return row, record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    source = ROOT / 'benchmarks/ahat_eval_set.jsonl'
    raw = source.read_bytes()
    lines = raw.splitlines(keepends=True)
    rows = list(map(json.loads, lines))
    index = next(i for i, r in enumerate(rows) if r['id'] == CASE_ID)
    before = rows[index]
    after, record = candidate(before)
    domains = domain_registry()
    verify(before, after, record)
    require({k: v for k, v in before.items() if k not in {'scene_graph', 'plan', 'reference_goal'}} ==
            {k: v for k, v in after.items() if k not in {'scene_graph', 'plan', 'reference_goal'}}, 'Unrelated change')
    print(json.dumps({'changed_cases': int(before != after), 'added_foods': len(record['added_nodes']),
                      'steps': len(after['plan']), 'goals': len(after['reference_goal']), 'verified': True}))
    if not args.write or before == after:
        return
    require(source.read_bytes() == raw and domain_registry() == domains, 'Baseline changed')
    snapshots = {str(p.relative_to(ROOT)): sha(p) for p in [
        ROOT / 'benchmarks/ahat-easy/cases.json', ROOT / 'benchmarks/ahat-medium/cases.json',
        *ROOT.glob('vendor/pddl/*.pddl')]}
    rows[index] = after
    lines[index] = (json.dumps(after, ensure_ascii=False) + '\n').encode()
    require(sum(a == b for a, b in zip(raw.splitlines(keepends=True), lines)) == len(rows) - 1,
            'Other task lines changed')
    source.write_bytes(b''.join(lines))
    cases = ROOT / 'benchmarks/ahat-open/cases.json'
    write(cases, [{k: r[k] for k in ('id', 'instruction', 'scene_graph', 'domain_id') if k in r}
                  for r in rows if r['type'] == 'open'])
    manifest_path = cases.with_name('manifest.json')
    manifest = json.loads(manifest_path.read_text())
    manifest.update(version='1.10.4', data_sha256=sha(cases), local_guest_dinner=REVISION)
    write(manifest_path, manifest)
    require(all(sha(ROOT / p) == h for p, h in snapshots.items()), 'Unrelated data/domain changed')
    record.update(status='accepted_reference_example', plan_before=before['plan'],
                  reference_goal_before=before.get('reference_goal'), source_index=index)
    report_path = ROOT / 'docs/validation/guest_dinner_v1_adoption.json'
    write(report_path, {'revision': REVISION, 'base_source_sha256': hashlib.sha256(raw).hexdigest(),
                       'source_sha256': sha(source), 'domains_unchanged': domains,
                       'other_source_lines_unchanged': len(rows) - 1, 'unchanged_files': snapshots,
                       'records': [record], 'failures': []})
    sync_path = ROOT / 'benchmarks/hf_sync.json'
    sync = json.loads(sync_path.read_text())
    sync['local_guest_dinner'] = {
        'revision': REVISION, 'ids': [CASE_ID], 'added_food_nodes': len(FOODS),
        'base_data_sha256': hashlib.sha256(raw).hexdigest(), 'result_data_sha256': sha(source),
        'report_path': str(report_path.relative_to(ROOT)), 'report_sha256': sha(report_path),
        'script_sha256': sha(Path(__file__)),
    }
    for artifact in sync['artifacts']:
        artifact['sha256'] = sha(ROOT / 'benchmarks' / artifact['path'])
    write(sync_path, sync)


if __name__ == '__main__':
    main()
