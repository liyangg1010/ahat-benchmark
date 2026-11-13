#!/usr/bin/env python3
"""Audited, idempotent scene/lighting migration; dry-run unless --write.

This does not add spatial-cycle prevention or generic container accessibility.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from ahat_benchmark.scene import normalize_links, sync_agent_rooms
from ahat_benchmark.judge.prompts import PROMPTS, PROMPT_VERSION, LIQUID_PROMPTS, LIQUID_PROMPT_VERSION

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'scene-lighting-v1'
SOURCE = ROOT / 'benchmarks/ahat_eval_set.jsonl'
RENAMES = {"children's_toys_63": 'childrens_toys_63', 'stuffed toy_22': 'stuffed_toy_22',
           'under‑stair_storage_unit_22': 'under_stair_storage_unit_22', 't‑shirt_57': 't_shirt_57'}
COFFEE = {'f8e914bb-3f3a-43de-8b8f-c86cbaf6894f': ('coffee_machine_16', 'kitchen_island_6'),
          '2cd06e0a-88a9-45a6-a5e3-a378199d6414': ('coffee_machine_39', 'kitchen_island_84')}
# Reviewed identities with lighting capability, not an inference from all furniture.
LIGHTS = frozenset('pendant_lamp table_lamp scented_candle candles ceiling_lamp floor_lamp '
    'candle_holder candlestick candle wall_lamp chandelier track_lighting night_light bedside_lamp '
    'light_bulb smart_light flashlight pathway_light desk_lamp lamp study_lamp bedside_lamp_small '
    'lamp_invented reading_lamp lantern lamp_bedroom lamp_office candle_festive outdoor_lantern '
    'handrail_light nightstand_lamp candle_set mirror_light reading_light string_lights small_lantern '
    'toilet_night_light led_light_bar'.split())


def nodes(graph):
    return {n['name']: n for k, v in graph.items() if k != 'links' and isinstance(v, list)
            for n in v if isinstance(n, dict) and 'name' in n}


def map_strings(value, transform):
    if isinstance(value, str):
        return transform(value)
    if isinstance(value, list):
        return [map_strings(v, transform) for v in value]
    if isinstance(value, dict):
        return {transform(k): map_strings(v, transform) for k, v in value.items()}
    return value


def repair(row):
    result = copy.deepcopy(row)
    changes = {}
    old_names = nodes(result['scene_graph'])
    renames = {a: b for a, b in RENAMES.items() if a in old_names}
    for old, new in renames.items():
        if new in old_names:
            raise ValueError(f'Rename collision: {new}')
        pattern = re.compile(r'(?<![\w-])' + re.escape(old) + r'(?![\w-])')
        result = map_strings(result, lambda text: pattern.sub(new, text))
    if renames:
        changes['renames'] = renames
    g = result['scene_graph']
    ns = nodes(g)
    lamp_names = []
    migrated = []
    for name, node in ns.items():
        states = node.get('states') or {}
        if not states.get('can_be_lighted'):
            continue
        if re.sub(r'_\d+$', '', name) not in LIGHTS:
            raise ValueError(f'Unreviewed lighting object: {name}')
        lamp_names.append(name)
        power = {k: states[k] for k in ('is_powerable', 'is_powered_on') if k in states}
        if power:
            migrated.append({'name': name, 'removed': power})
            if states.get('is_powered_on'):
                states['is_light_on'] = True
            states.pop('is_powerable', None)
            states.pop('is_powered_on', None)
    if migrated:
        changes['lighting_nodes'] = migrated
    if lamp_names:
        names = '(?:' + '|'.join(map(re.escape, lamp_names)) + ')'
        action = re.compile(r'\(power_(on|off) (\S+) (' + names + r')\)')
        pred = re.compile(r'\(is_powered_on (' + names + r')\)')
        result = map_strings(result, lambda s: pred.sub(r'(is_light_on \1)',
            action.sub(r'(light_\1 \2 \3)', s)))
        g = result['scene_graph']
    if row['plan'] != result['plan']:
        changes['plan_before'] = row['plan']
        changes['plan_after'] = result['plan']
    if row['id'] in COFFEE:
        machine, counter = COFFEE[row['id']]
        links = normalize_links(g)
        old = {'relation': 'in', 'from': machine, 'to': counter}
        if old in links:
            links[links.index(old)] = {'relation': 'on', 'from': machine, 'to': counter}
            g['links'] = links
            changes['coffee_placement'] = {'object': machine, 'surface': counter, 'from': 'in', 'to': 'on'}
    agents = {a['name'] for a in g.get('agent') or []}
    links = normalize_links(g)
    bad = [l for l in links if l['relation'] == 'on' and l['to'] in agents]
    if bad:
        g['links'] = [l for l in links if l not in bad]
        room_names = {r['name'] if isinstance(r, dict) else r for r in g['rooms']}
        old_room_links = [l for l in links if l['relation'] == 'in' and l['from'] in agents and l['to'] in room_names]
        sync_agent_rooms(g)
        changes['removed_agent_on_links'] = bad
        changes['agent_room_links_before'] = old_room_links
        changes['agent_room_links_after'] = [l for l in g['links'] if l['relation'] == 'in' and l['from'] in agents and l['to'] in room_names]
    return result, changes


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    before = SOURCE.read_bytes()
    lines = before.decode().splitlines()
    rows = list(map(json.loads, lines))
    repaired = [repair(r) for r in rows]
    positions = {}
    changed = []
    for index, (old, (new, details)) in enumerate(zip(rows, repaired)):
        split = old['type']
        split_index = positions.get(split, 0)
        positions[split] = split_index + 1
        if old != new:
            changed.append({'id': old['id'], 'source_index': index, 'split': split,
                            'split_index': split_index, **details})
    report = {'revision': REVISION, 'base_data_sha256': sha(before), 'changed_task_count': len(changed), 'changes': changed}
    print(json.dumps({k: v for k, v in report.items() if k != 'changes'}))
    if not args.write:
        return
    # Preserve unchanged source lines and task ordering.
    text = '\n'.join(json.dumps(new, ensure_ascii=False) if old != new else line
                     for line, old, (new, _) in zip(lines, rows, repaired)) + '\n'
    SOURCE.write_text(text)
    rows = [r for r, _ in repaired]
    report['result_data_sha256'] = sha(SOURCE.read_bytes())
    inventory = ROOT / 'docs/validation/scene_lighting_v1_inventory.json'
    if changed or not inventory.exists():
        write_json(inventory, report)
    manifest_path = ROOT / 'benchmark_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for domain in manifest['domains'].values():
        domain.update(sha256=sha((ROOT / domain['path']).read_bytes()), revision=REVISION)
    manifest['domain'] = manifest['domains'][manifest['domain']['name']]
    for key, prompts, version in [('ahat-v8-group-portions', PROMPTS, PROMPT_VERSION),
                                  ('ahat-liquid-v1', LIQUID_PROMPTS, LIQUID_PROMPT_VERSION)]:
        profile = {'version': version, 'prompt_hashes': {k: sha(v.encode()) for k, v in prompts.items()}}
        manifest['judge_profiles'][key] = profile
        if key == manifest['domain']['name']:
            manifest['judge'].update(profile)
    write_json(manifest_path, manifest)
    for split, version in [('easy', '1.9.0'), ('medium', '1.8.0'), ('open', '1.9.0')]:
        folder = ROOT / f'benchmarks/ahat-{split}'
        records = [{k: r[k] for k in ('id', 'instruction', 'scene_graph', 'domain_id') if k in r}
                   for r in rows if r['type'] == split]
        write_json(folder / 'cases.json', records)
        m = json.loads((folder / 'manifest.json').read_text())
        m.update(version=version, case_count=len(records), data_sha256=sha((folder / 'cases.json').read_bytes()),
                 domains=manifest['domains'], domain_sha256=manifest['domain']['sha256'], local_scene_lighting=REVISION)
        write_json(folder / 'manifest.json', m)
    sync_path = ROOT / 'benchmarks/hf_sync.json'
    sync = json.loads(sync_path.read_text())
    recorded = json.loads(inventory.read_text())
    sync['local_scene_lighting'] = {'revision': REVISION, 'base_data_sha256': recorded['base_data_sha256'],
        'result_data_sha256': sha(SOURCE.read_bytes()), 'changed_task_count': recorded['changed_task_count'],
        'inventory_path': str(inventory.relative_to(ROOT)), 'inventory_sha256': sha(inventory.read_bytes()),
        'script_sha256': sha(Path(__file__).read_bytes())}
    for artifact in sync['artifacts']:
        artifact['sha256'] = sha((ROOT / 'benchmarks' / artifact['path']).read_bytes())
    write_json(sync_path, sync)


if __name__ == '__main__':
    main()
