#!/usr/bin/env python3
"""Offline full-reference round trips and scoped before/after scene checks."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from ahat_benchmark.domains import task_domain, domain_registry
from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.scene import normalize_links, sync_agent_rooms
from ahat_benchmark.vendor.scene_graph import SceneGraphManager, PDDLDomainParser
from repair_scene_lighting import repair, nodes, COFFEE

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True, help='Folder with pre-repair JSONL and both domains')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/validation/scene_lighting_v1_checks.json')
    args = parser.parse_args()
    source = ROOT / 'benchmarks/ahat_eval_set.jsonl'
    rows = list(map(json.loads, source.read_text().splitlines()))
    previous = list(map(json.loads, (args.baseline / source.name).read_text().splitlines()))
    old_by_id = {r['id']: r for r in previous}
    inventory = json.loads((ROOT / 'docs/validation/scene_lighting_v1_inventory.json').read_text())
    changes = {r['id']: r for r in inventory['changes']}
    counts, failures = Counter(), []
    if [r['id'] for r in rows] != [r['id'] for r in previous]:
        failures.append(['task IDs/order changed'])
    for row in rows:
        cid = row['id']; graph = row['scene_graph']; domain = task_domain(row)
        old = old_by_id[cid]; detail = changes.get(cid, {})
        if row['instruction'] != old['instruction'] or row['type'] != old['type']:
            failures.append([cid, 'instruction/split changed'])
        if repair(row) != (row, {}):
            failures.append([cid, 'migration not idempotent'])
        ns = nodes(graph)
        if any(not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]*', n) for n in ns):
            failures.append([cid, 'illegal object name'])
        agents = {a['name'] for a in graph.get('agent') or []}
        links = normalize_links(graph)
        if any(l['relation'] == 'on' and l['to'] in agents for l in links):
            failures.append([cid, 'illegal on-agent link remains'])
        if 'removed_agent_on_links' in detail:
            # Every retained non-agent physical edge is unchanged; room roots need no parent.
            old_links = normalize_links(old['scene_graph'])
            expected = [l for l in old_links if l not in detail['removed_agent_on_links']
                        and not (l['relation'] == 'in' and l['from'] in agents)]
            actual = [l for l in links if not (l['relation'] == 'in' and l['from'] in agents)]
            rename = detail.get('renames', {})
            expected = [{k: rename.get(v, v) for k, v in l.items()} for l in expected]
            if expected != actual:
                failures.append([cid, 'unexpected physical-edge change during agent repair'])
        if cid in COFFEE:
            machine, counter = COFFEE[cid]
            if {'relation': 'on', 'from': machine, 'to': counter} not in links:
                failures.append([cid, 'coffee machine not on accessible counter'])
        dropped = []
        problem = full_problem(graph, domain, dropped)
        if dropped:
            failures.append([cid, 'initial facts excluded', dropped])
        manager = SceneGraphManager(graph, str(domain))
        for i, step in enumerate(row['plan']):
            a = sexpr(step); manager.apply_action(a[0], a[1:])
            actual = final_state(full_problem(manager.scene_graph, domain), [], domain)
            expected = final_state(problem, row['plan'][:i + 1], domain)
            if actual != expected:
                failures.append([cid, 'scene/PDDL roundtrip mismatch', i + 1])
                break
            # Synchronization must be stable even after pick removes a navigation anchor's support.
            original_links = list(manager.scene_graph['links'])
            sync_agent_rooms(manager.scene_graph)
            if original_links != manager.scene_graph['links']:
                failures.append([cid, 'unstable agent room links', i + 1])
            counts['scene_roundtrip_steps'] += 1
        counts['scene_roundtrip_cases'] += 1
        current = {tuple(f) for f in final_state(problem, row['plan'], domain)}
        prior_domain = args.baseline / domain.name
        prior = {tuple(f) for f in final_state(full_problem(old['scene_graph'], prior_domain), old['plan'], prior_domain)}
        allowed_names = set(detail.get('renames', {})) | set(detail.get('renames', {}).values())
        light_names = {n['name'] for n in detail.get('lighting_nodes', [])}
        def allowed(fact):
            if any(x in allowed_names for x in fact[1:]):
                return True
            if fact[0] in {'is_powerable', 'is_powered_on', 'is_light_on'} and fact[1] in light_names:
                return True
            return (cid in COFFEE and fact[0] in {'item_on_surface', 'item_in_receptacle'}
                    and fact[1:] == COFFEE[cid])
        unexpected = [f for f in current ^ prior if not allowed(f)]
        if unexpected:
            failures.append([cid, 'unexpected PDDL final-state changes', unexpected])
        counts['baseline_state_scope_checks'] += 1
        counts['identical_baseline_final_states'] += current == prior
        counts['idempotent_migration_cases'] += repair(row) == (row, {})
    for name, entry in domain_registry().items():
        current = PDDLDomainParser((ROOT / entry['path']).read_text())
        prior = PDDLDomainParser((args.baseline / Path(entry['path']).name).read_text())
        if set(current.actions) - set(prior.actions) != {'light_off'}:
            failures.append([name, 'unexpected added actions'])
        for action, spec in prior.actions.items():
            if action != 'light_on' and current.actions.get(action) != spec:
                failures.append([name, 'non-lighting action changed', action])
    report = {'kind': 'offline_scene_lighting_validation_not_llm_scores',
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'domains': domain_registry(),
              'counts': dict(counts), 'failures': failures}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'counts': dict(counts), 'failures': failures}, ensure_ascii=False))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
