#!/usr/bin/env python3
"""Keep two refill representatives and add explicit opening before faucet filling.

Dry-run by default; --write archives removed tasks and updates dataset manifests.
Only the liquid domain's fill_from_faucet changes (generated separately).
"""
import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path

from ahat_benchmark.pddl import sexpr

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'bottle-refill-v1'
LIQUID = 'ahat-liquid-v1'
KEEP = {'6e590abe-0592-4a01-8de9-269cdd94fa89': 'reusable_water_bottle_24',
        '44a3890d-31fb-4a53-b9d2-1d7f2e22f686': 'reusable_water_bottle_47'}
REMOVE = {'baebc10b-0942-4ab8-a948-b5ce3630af75', 'ca93f23c-c8c5-426f-81f5-4f7e51811dfc'}
REPRESENTATIVE = '44a3890d-31fb-4a53-b9d2-1d7f2e22f686'
NOTE = 'Open the bottle before pickup and faucet filling; the instruction does not require a closed final bottle.'


def repair(row):
    result = copy.deepcopy(row)
    if row['id'] not in KEEP:
        return result
    bottle = KEEP[row['id']]
    result['domain_id'] = LIQUID
    pickup = next(i for i, step in enumerate(result['plan'])
                  if sexpr(step)[:3] == ['pick_from_surface', 'agent_0', bottle])
    opening = f'(open agent_0 {bottle})'
    if opening not in result['plan']:
        result['plan'].insert(pickup, opening)
    witness = result['liquid_reference']
    if opening not in witness['required_actions']:
        witness['required_actions'].insert(0, opening)
    if NOTE not in witness['notes']:
        witness['notes'].append(NOTE)
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    source = ROOT / 'benchmarks/ahat_eval_set.jsonl'
    lines = source.read_text().splitlines()
    rows = list(map(json.loads, lines))
    if not set(KEEP).issubset({r['id'] for r in rows}):
        raise ValueError('Missing retained bottle task')
    removed = [r for r in rows if r['id'] in REMOVE]
    after = [repair(r) for r in rows if r['id'] not in REMOVE]
    changed = [r['id'] for r in rows if r['id'] in KEEP and repair(r) != r]
    print(json.dumps({'revision': REVISION, 'removed': len(removed), 'repaired': changed, 'active_cases': len(after)}))
    if not args.write:
        return
    archive = ROOT / 'benchmarks/bottle-refill-v1/pruned.json'
    if removed:
        if archive.exists():
            raise ValueError('Archive already exists while removed tasks are still active; inspect before rewriting')
        write_json(archive, [{'representative_id': REPRESENTATIVE,
                             'reason': 'Redundant refill-and-place task; retain specified faucet and return-to-origin coverage.',
                             'original_record': r} for r in removed])
    if not archive.exists() or {x['original_record']['id'] for x in json.loads(archive.read_text())} != REMOVE:
        raise ValueError('Pruned-task archive is missing or incomplete')
    inventory_path = ROOT / 'docs/validation/bottle_refill_v1_inventory.json'
    before_hash = sha(source)
    if changed or removed or not inventory_path.exists():
        positions = Counter()
        records = []
        for index, row in enumerate(rows):
            split_index = positions[row['type']]; positions[row['type']] += 1
            if row['id'] in set(KEEP) | REMOVE:
                records.append({'id': row['id'], 'source_index_before': index, 'split': row['type'],
                                'split_index_before': split_index, 'instruction': row['instruction'],
                                'decision': 'keep_and_open' if row['id'] in KEEP else 'prune_duplicate',
                                'plan_before': row['plan'],
                                'plan_after': repair(row)['plan'] if row['id'] in KEEP else None})
        inventory = {'revision': REVISION, 'base_data_sha256': before_hash, 'records': records,
                     'ordinary_domain_sha256': sha(ROOT / 'vendor/pddl/domain_0102_test.pddl')}
    else:
        inventory = json.loads(inventory_path.read_text())
    source.write_text('\n'.join(json.dumps(repair(r), ensure_ascii=False) if r['id'] in changed else line
                                for line, r in zip(lines, rows) if r['id'] not in REMOVE) + '\n')
    inventory['result_data_sha256'] = sha(source)
    write_json(inventory_path, inventory)
    manifest_path = ROOT / 'benchmark_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['domains'][LIQUID].update(revision=REVISION,
                                      sha256=sha(ROOT / manifest['domains'][LIQUID]['path']))
    manifest['active_case_count'] = len(after)
    write_json(manifest_path, manifest)
    for split, version in [('easy', '1.9.1'), ('medium', '1.9.0'), ('open', '1.9.1')]:
        folder = ROOT / f'benchmarks/ahat-{split}'
        cases = [{k: r[k] for k in ('id', 'instruction', 'scene_graph', 'domain_id') if k in r}
                 for r in after if r['type'] == split]
        write_json(folder / 'cases.json', cases)
        m = json.loads((folder / 'manifest.json').read_text())
        m.update(version=version, case_count=len(cases), data_sha256=sha(folder / 'cases.json'),
                 domains=manifest['domains'], local_bottle_refill=REVISION)
        write_json(folder / 'manifest.json', m)
    sync_path = ROOT / 'benchmarks/hf_sync.json'
    sync = json.loads(sync_path.read_text())
    sync.update(case_count=len(after), split_counts=dict(Counter(r['type'] for r in after)))
    sync['local_bottle_refill'] = {'revision': REVISION, 'retained_ids': list(KEEP), 'pruned_ids': sorted(REMOVE),
        'domain_counts': dict(Counter(r.get('domain_id', manifest['domain']['name']) for r in after)),
        'base_data_sha256': inventory['base_data_sha256'], 'result_data_sha256': sha(source),
        'inventory_path': str(inventory_path.relative_to(ROOT)), 'inventory_sha256': sha(inventory_path),
        'archive_path': str(archive.relative_to(ROOT)), 'script_sha256': sha(Path(__file__))}
    if not any(a['path'] == 'bottle-refill-v1/pruned.json' for a in sync['artifacts']):
        sync['artifacts'].append({'path': 'bottle-refill-v1/pruned.json'})
    for artifact in sync['artifacts']:
        artifact['sha256'] = sha(ROOT / 'benchmarks' / artifact['path'])
    write_json(sync_path, sync)


if __name__ == '__main__':
    main()
