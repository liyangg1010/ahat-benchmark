"""Explicit cooking annotations and audited reference repairs (idempotent).

Run with PYTHONPATH=src. Without --write this prints the proposed change counts.
Semantic allowlists deliberately exclude packaging, toys, plants and generic
serving dishes. Custom scenes must supply their own capability attributes.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from ahat_benchmark.scene import normalize_links


ROOT = Path(__file__).resolve().parents[1]
REVISION = 'heated-v2'
DOMAIN_NAME = 'ahat-v8-group-portions'
PORTION_REVISION = 'serves-two-v1'
GROUP_PORTION_REVISION = 'group-portions-v1'
COOKWARE = frozenset({
    'pot', 'pan', 'cooking_pot', 'cooking_pan', 'cookware_pot', 'frying_pan',
    'saucepan', 'hot_pot_saucepan', 'cast_iron_pan', 'clay_pot',
    'stainless_steel_pot', 'baking_tray', 'cake_pan', 'bundt_pan',
    'microwave_dish', 'microwave_safe_bowl', 'microwave_safe_dish',
})
# Direct food objects only: egg_carton, milk_carton, toy_food, fruit_bowl,
# food packaging and ordinary containers are not edible objects.
FOOD = frozenset({
    'apple', 'apples', 'banana', 'bread', 'bread_loaf', 'loaf_of_bread',
    'butter', 'butter_block', 'carrots', 'cucumber', 'egg', 'eggs', 'fruit',
    'fresh_vegetables', 'grapes', 'lemon', 'meat', 'milk', 'orange', 'potato',
    'raw_vegetables', 'seafood', 'spinach', 'strawberry', 'tomato', 'tomatoes',
    'vegetables', 'yak_butter', 'spicy_sausage', 'sandwich', 'microwaveable_meal',
})
DEVICE_FLAGS = {
    'microwave': 'is_microwave',
    'oven': 'is_oven', 'stove_oven': 'is_oven',
    'stove': 'is_cooking_surface', 'grill': 'is_cooking_surface',
    'bbq_grill': 'is_cooking_surface', 'portable_induction_stove': 'is_cooking_surface',
}
BREAKFAST = 'fd22ff41-4720-497c-bad3-7411b468b6cc'
HOT_BREAKFAST = '4bddb476-f1ae-44e1-9558-add1571dd936'
WARM_BRUNCH = '9027ed1b-fcf9-4f17-8b39-c397d4db7563'
REHEAT = '02a5f844-c663-4336-b6c9-fad5540b7cd5'
REPAIRED_IDS = (BREAKFAST, HOT_BREAKFAST, WARM_BRUNCH, REHEAT)
CONFIRMED_GOAL_IDS = (BREAKFAST, REHEAT)
TWO_SERVING_FOODS = {HOT_BREAKFAST: 'eggs_116', WARM_BRUNCH: 'breakfast_eggs_1'}
ADDITIONAL_TWO_SERVING_FOODS = {
    'f3ee3e87-d782-4870-8ed3-2bc92f344010': 'eggs_116',
    '0cf41a97-9f6a-4e13-8542-1def6889483d': 'eggs_66',
}
GROUP_SERVING_FOODS = {
    'dec162ab-e453-419f-971a-2e32987350f2': 'cheese_block_106',
    '198fd035-6f65-4740-8b01-0643a215ccb4': 'eggs_90',
}
ALL_TWO_SERVING_FOODS = {**TWO_SERVING_FOODS, **ADDITIONAL_TWO_SERVING_FOODS}


def confirmed_reference(row):
    """Only the two references certified in docs/heated.md.

    These are sufficient witnesses within the current symbolic model, not
    necessary goals or scoring rules. Do not extend this set on VAL validity
    alone: quantity, meal contents and requested processes need semantic review.
    """
    row = copy.deepcopy(row)
    if row['id'] == BREAKFAST:
        row['reference_goal'] = [
            '(heated breakfast_eggs_1)',
            '(item_on_surface breakfast_eggs_1 plate_48)',
            '(item_on_surface plate_48 dining_table_3)',
            '(furniture_in_room dining_table_3 dining_room_2)',
            '(is_clean plate_48)', '(is_clean dining_table_3)',
            '(not (is_powered_on stove_2))', '(handempty agent_0)',
        ]
    elif row['id'] == REHEAT:
        row['reference_goal'] = [
            '(heated casserole_21)',
            '(item_on_surface casserole_21 table_29)',
            '(furniture_in_room table_29 dining_room_1)',
            '(furniture_in_room oven_30 kitchen_1)',
            '(not (is_powered_on oven_30))', '(handempty robot1)',
        ]
        row['plan'] = [
            '(open robot1 counter_40)',
            '(navigate robot1 counter_40 oven_30)',
            '(open robot1 oven_30)',
            '(navigate robot1 oven_30 casserole_21)',
            '(pick_from_receptacle robot1 casserole_21 counter_40)',
            '(navigate robot1 casserole_21 oven_30)',
            '(place_in_receptacle robot1 casserole_21 oven_30)',
            '(close robot1 oven_30)',
            '(power_on robot1 oven_30)',
            '(heat_with_oven robot1 casserole_21 oven_30)',
            '(power_off robot1 oven_30)',
            '(open robot1 oven_30)',
            '(navigate robot1 oven_30 casserole_21)',
            '(pick_from_receptacle robot1 casserole_21 oven_30)',
            '(navigate robot1 casserole_21 table_29)',
            '(place_on_surface robot1 casserole_21 table_29)',
        ]
    return row


def semantic_type(node):
    return node.get('type') or re.sub(r'_\d+$', '', node['name'])


class CookingPlan:
    """Build access, processing and serving steps for the three named scenes."""

    def __init__(self, graph):
        self.nodes = {node['name']: node for group, nodes in graph.items()
                      if group != 'links' and isinstance(nodes, list)
                      for node in nodes if isinstance(node, dict) and 'name' in node}
        self.positions = {link['from']: (link['relation'], link['to'])
                          for link in normalize_links(graph) if link['relation'] in ('on', 'in')}
        self.agent = graph['agent'][0]['name']
        self.position = graph['agent'][0]['location']
        self.opened = {name for name, node in self.nodes.items() if node.get('states', {}).get('is_open')}
        self.plan = []

    def act(self, action, *args):
        self.plan.append(f'({action} {self.agent} ' + ' '.join(args) + ')')

    def navigate(self, target):
        if self.position != target:
            self.act('navigate', self.position, target)
            self.position = target

    def access(self, target):
        relation, parent = self.positions.get(target, (None, None))
        if relation == 'in' and parent in self.nodes:
            self.access(parent)
        if self.nodes[target].get('states', {}).get('can_be_opened') and target not in self.opened:
            self.navigate(target)
            self.act('open', target)
            self.opened.add(target)

    def move(self, obj, target):
        relation, source = self.positions[obj]
        if relation == 'in':
            self.access(source)
        self.navigate(obj)
        self.act('pick_from_receptacle' if relation == 'in' else 'pick_from_surface', obj, source)
        self.navigate(target)
        self.act('place_on_surface', obj, target)
        self.positions[obj] = ('on', target)

    def heat_and_serve(self, food, pot, stove, serving):
        self.move(food, pot)
        self.navigate(stove)
        self.act('power_on', stove)
        self.act('heat_on_heating_device', food, pot, stove)
        self.act('power_off', stove)
        self.move(food, serving)


def repair_cases(rows):
    result = copy.deepcopy(rows)
    for row in result:
        graph = row['scene_graph']
        for group, nodes in graph.items():
            if group == 'links' or not isinstance(nodes, list):
                continue
            for node in nodes:
                if not isinstance(node, dict) or 'name' not in node:
                    continue
                states = node.get('states') or {}
                # Do not infer heating from an obsolete initial doneness flag.
                states.pop('cooked', None)
                if 'is_heated' in states:
                    states.setdefault('heated', states.pop('is_heated'))
                kind = semantic_type(node)
                if kind in COOKWARE and group == 'objects':
                    node.setdefault('states', {})['is_heating_container'] = True
                if kind in FOOD and group == 'objects':
                    node.setdefault('states', {}).update(is_food=True, can_be_heated=True)
                if kind in DEVICE_FLAGS:
                    states = node.setdefault('states', {})
                    states.update({DEVICE_FLAGS[kind]: True, 'is_heating_device': True, 'is_powerable': True})
                    if kind in ('microwave', 'oven', 'stove_oven'):
                        states['can_be_opened'] = True

        if row['id'] in (BREAKFAST, WARM_BRUNCH):
            carton = 'egg_carton_46' if row['id'] == BREAKFAST else 'egg_carton_139'
            if not any(n['name'] == 'breakfast_eggs_1' for n in graph['objects']):
                graph['objects'].append({
                    'name': 'breakfast_eggs_1', 'type': 'eggs',
                    'states': {'is_food': True, 'can_be_heated': True, 'heated': False},
                })
                graph['links'].append({'relation': 'in', 'from': 'breakfast_eggs_1', 'to': carton})

        if row['id'] == BREAKFAST:
            plan = CookingPlan(graph)
            plan.heat_and_serve('breakfast_eggs_1', 'pot_2', 'stove_2', 'plate_48')
            row['plan'] = plan.plan
            row['reference_goal'] = [
                '(heated breakfast_eggs_1)',
                '(item_on_surface breakfast_eggs_1 plate_48)', '(item_on_surface plate_48 dining_table_3)',
                '(not (is_powered_on stove_2))',
            ]
        elif row['id'] == HOT_BREAKFAST:
            plan = CookingPlan(graph)
            plan.heat_and_serve('eggs_116', 'pot_37', 'stove_26', 'dining_table_19')
            plan.move('yogurt_cup_33', 'dining_table_19')
            plan.move('milk_114', 'dining_table_19')
            row['plan'] = plan.plan
            row['reference_goal'] = [
                '(heated eggs_116)', '(item_on_surface eggs_116 dining_table_19)',
                '(item_on_surface yogurt_cup_33 dining_table_19)', '(item_on_surface milk_114 dining_table_19)',
                '(not (is_powered_on stove_26))',
            ]
        elif row['id'] == WARM_BRUNCH:
            plan = CookingPlan(graph)
            plan.heat_and_serve('breakfast_eggs_1', 'cooking_pot_52', 'stove_16', 'dining_table_21')
            plan.move('butter_54', 'dining_table_21')
            plan.move('fruit_bowl_48', 'dining_table_21')
            row['plan'] = plan.plan
            # Unified heat processing; portion capacity is annotated below.
            row['reference_goal'] = [
                '(heated breakfast_eggs_1)',
                '(item_on_surface breakfast_eggs_1 dining_table_21)',
                '(item_on_surface butter_54 dining_table_21)', '(item_on_surface fruit_bowl_48 dining_table_21)',
                '(not (is_powered_on stove_16))',
            ]
        elif row['id'] == REHEAT:
            dish = next(n for n in graph['objects'] if n['name'] == 'casserole_21')
            # In this instruction casserole denotes the food dish, not an
            # empty pot. Keep its stable name while making that meaning explicit.
            dish['type'] = 'casserole_dish'
            dish['states'].pop('is_heated', None)
            dish['states'].update(is_food=True, can_be_heated=True, heated=False)
            action = '(heat_with_oven robot1 casserole_21 oven_30)'
            if action not in row['plan']:
                row['plan'].insert(row['plan'].index('(power_on robot1 oven_30)') + 1, action)
            row['reference_goal'] = [
                '(heated casserole_21)', '(item_on_surface casserole_21 table_29)',
                '(not (is_powered_on oven_30))',
            ]
    result = [confirmed_reference(row) if row['id'] in CONFIRMED_GOAL_IDS else row for row in result]
    # Migrate reference-only fields as well as scene states. Repeated conversion
    # cannot add duplicate goals or revive the removed action family.
    for row in result:
        row['plan'] = [re.sub(r'^\(cook_', '(heat_', action) for action in row['plan']]
        if 'reference_goal' in row:
            goals = [re.sub(r'\bcooked\b', 'heated', goal) for goal in row['reference_goal']]
            row['reference_goal'] = list(dict.fromkeys(goals))
        if row['id'] in TWO_SERVING_FOODS:
            # Explicit local scenario design, not a guess from names or packaging.
            food_name = TWO_SERVING_FOODS[row['id']]
            food = next(node for node in row['scene_graph']['objects'] if node['name'] == food_name)
            if not food.get('states', {}).get('is_food'):
                raise ValueError(f'Two-serving annotation requires actual food: {food_name}')
            food['states']['serves_two'] = True
            goal = f'(serves_two {food_name})'
            if goal not in row['reference_goal']:
                row['reference_goal'].append(goal)
        if row['id'] in ADDITIONAL_TWO_SERVING_FOODS or row['id'] in GROUP_SERVING_FOODS:
            two = row['id'] in ADDITIONAL_TWO_SERVING_FOODS
            food_name = (ADDITIONAL_TWO_SERVING_FOODS if two else GROUP_SERVING_FOODS)[row['id']]
            food = next(node for node in row['scene_graph']['objects'] if node['name'] == food_name)
            # Explicit local food-portion design. A cheese block is actual food,
            # not a wrapper; no capability is inferred for other cheese nodes.
            food['states'].update(is_food=True, can_be_heated=True)
            food['states'].setdefault('heated', False)
            food['states']['serves_two' if two else 'serves_group'] = True
    return result


def change_records(before, after):
    records = []
    for old, new in zip(before, after):
        if old == new:
            continue
        old_nodes = {n['name']: n for group, nodes in old['scene_graph'].items()
                     if group != 'links' and isinstance(nodes, list)
                     for n in nodes if isinstance(n, dict) and 'name' in n}
        changed_nodes = [n for group, nodes in new['scene_graph'].items()
                         if group != 'links' and isinstance(nodes, list)
                         for n in nodes if isinstance(n, dict) and old_nodes.get(n.get('name')) != n]
        records.append({'id': new['id'], 'type': new['type'],
                        'changed_nodes': [n['name'] for n in changed_nodes],
                        'reference_changed': old['plan'] != new['plan'] or old.get('reference_goal') != new.get('reference_goal')})
    return records


def write_snapshot(before, rows):
    domain_path = ROOT / 'vendor/pddl/domain_0102_test.pddl'
    domain_hash = hashlib.sha256(domain_path.read_bytes()).hexdigest()
    source = ROOT / 'benchmarks/ahat_eval_set.jsonl'
    source.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
    versions = {'easy': '1.6.0', 'medium': '1.5.0', 'open': '1.7.0'}
    for split, version in versions.items():
        folder = ROOT / f'benchmarks/ahat-{split}'
        projected = [{key: row[key] for key in ('instruction', 'scene_graph', 'id')}
                     for row in rows if row['type'] == split]
        (folder / 'cases.json').write_text(json.dumps(projected, ensure_ascii=False, indent=2) + '\n')
        manifest = json.loads((folder / 'manifest.json').read_text())
        version = max((version, manifest['version']), key=lambda v: tuple(map(int, v.split('.'))))
        manifest.update(version=version, domain=DOMAIN_NAME, domain_sha256=domain_hash,
                        data_sha256=hashlib.sha256((folder / 'cases.json').read_bytes()).hexdigest(),
                        local_heated=REVISION)
        manifest['local_serves_two'] = PORTION_REVISION
        manifest['local_group_portions'] = GROUP_PORTION_REVISION
        (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    path = ROOT / 'benchmarks/hf_sync.json'
    sync = json.loads(path.read_text())
    # Earlier revision entries describe their historical snapshots. Keep them
    # intact, including the superseded cooked-goal repair.
    if 'local_heated' not in sync:
        sync['local_heated'] = {
            'version': REVISION, 'date': '2026-11-11',
            'base_data_sha256': hashlib.sha256(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in before).encode()).hexdigest(),
            'cases': change_records(before, rows),
            'reference_repaired_ids': list(REPAIRED_IDS),
            'confirmed_reference_goal_ids': list(CONFIRMED_GOAL_IDS),
            'supersedes': ['cooking-v1', 'cooking-goals-v1', 'warm-brunch-cooked-goal-v1'],
            'semantics': 'One heated result for food and nonfood; no cooked state or initial doneness distinction. Explicit heatability is required.',
        }
    if 'local_serves_two' not in sync:
        sync['local_serves_two'] = {
            'version': PORTION_REVISION, 'date': '2026-11-11',
            'base_data_sha256': hashlib.sha256(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in before).encode()).hexdigest(),
            'food_nodes': TWO_SERVING_FOODS,
            'semantics': 'Explicit local declaration: each whole named food object is enough for two diners. Static capacity, not completed processing or serving.',
            'judge_input_scope': 'D1 final PDDL state; D2/D3/D4 inputs unchanged',
        }
    if 'local_group_portions' not in sync:
        sync['local_group_portions'] = {
            'version': GROUP_PORTION_REVISION, 'date': '2026-11-11',
            'base_data_sha256': hashlib.sha256(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in before).encode()).hexdigest(),
            'two_serving_food_nodes': ADDITIONAL_TWO_SERVING_FOODS,
            'group_serving_food_nodes': GROUP_SERVING_FOODS,
            'semantics': 'Static local capacity for two diners or the scenario intended family/guest group. No numeric group size, doneness, preparation or serving completion is inferred.',
            'changed_cases': change_records(before, rows),
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'judge_input_scope': 'Capacity facts reach D1; D2/D3/D4 input formats unchanged. D3 checks required stages, D4 checks required temporal order.',
        }
    sync['local_domain'].update(name=DOMAIN_NAME, sha256=domain_hash,
        changes='Preserve heated-only processing, serves_two and adjacency guards; add static serves_group capacity for the scenario intended dining group.')
    if 'heated-v2' not in sync['transformation']:
        sync['transformation'] += ' Unify thermal processing to heated only, remove initial cooked flags, normalize legacy is_heated flags and migrate references (heated-v2).'
    if PORTION_REVISION not in sync['transformation']:
        sync['transformation'] += ' Declare two-serving egg portions in two scenes, add reference capacity goals and expose the static predicate to D1 (serves-two-v1).'
    if GROUP_PORTION_REVISION not in sync['transformation']:
        sync['transformation'] += ' Annotate food capacity in the remaining two-person and family/guest meals without inventing numeric group size; clarify required plan stages and temporal order (group-portions-v1).'
    for artifact in sync['artifacts']:
        artifact['sha256'] = hashlib.sha256((ROOT / 'benchmarks' / artifact['path']).read_bytes()).hexdigest()
    path.write_text(json.dumps(sync, ensure_ascii=False, indent=2) + '\n')
    manifest_path = ROOT / 'benchmark_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['domain'].update(name=DOMAIN_NAME, sha256=domain_hash)
    from ahat_benchmark.judge.prompts import NAMES, PROMPT_DIR, PROMPT_VERSION
    manifest['judge']['version'] = PROMPT_VERSION
    manifest['judge']['prompt_hashes'] = {
        key: hashlib.sha256((PROMPT_DIR / (name + '.txt')).read_bytes()).hexdigest()
        for key, name in NAMES.items()
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    rows = [json.loads(line) for line in (ROOT / 'benchmarks/ahat_eval_set.jsonl').read_text().splitlines()]
    updated = repair_cases(rows)
    changed = change_records(rows, updated)
    print(json.dumps({'changed_cases': len(changed), 'split_counts': dict(Counter(c['type'] for c in changed)),
                      'changed_references': sum(c['reference_changed'] for c in changed)}))
    if args.write:
        write_snapshot(rows, updated)


if __name__ == '__main__':
    main()
