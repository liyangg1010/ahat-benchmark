#!/usr/bin/env python3
"""Apply the reviewed liquid-pruning-v1 inventory requested by the user, idempotently.

This reduces semantic coverage overlap, not just exact duplicate records.
Without --write, only report proposed deletions. Surviving source lines are kept
byte-for-byte; original task fields and the domain/rubric remain unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'docs/validation/liquid_pruning_inventory.json'
REVISION = 'liquid-pruning-v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def select_rows(rows, inventory):
    reviewed = {r['id']: r for r in inventory['records']}
    removed = {key for key, item in reviewed.items() if item['decision'] == 'remove'}
    retained = set(reviewed) - removed
    ids = [r['id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate task IDs')
    if not retained <= set(ids):
        raise ValueError('Approved retained representative is missing')
    present = removed & set(ids)
    if present and present != removed:
        raise ValueError('Partially pruned snapshot; refusing ambiguous migration')
    for row in rows:
        if row['id'] not in reviewed:
            continue
        item = reviewed[row['id']]
        if (row['instruction'], row['type']) != (item['instruction'], item['split']):
            raise ValueError('Reviewed task intent or split changed')
        if row['id'] in present and sha(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()) != item['record_sha256']:
            raise ValueError('Removal candidate changed since review')
    return [r for r in rows if r['id'] not in removed]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    inventory = json.loads(INVENTORY.read_text())
    source = ROOT / 'benchmarks/ahat_eval_set.jsonl'
    before_bytes = source.read_bytes()
    lines = before_bytes.splitlines(keepends=True)
    before = [json.loads(line) for line in lines]
    after = select_rows(before, inventory)
    kept_ids = {r['id'] for r in after}
    counts = dict(Counter(r['type'] for r in after))
    changed = len(before) - len(after)
    print(json.dumps({'removed_cases': changed, 'case_count': len(after), 'split_counts': counts}))
    if not args.write or not changed:
        return
    if sha(before_bytes) != inventory['source_sha256']:
        raise ValueError('Source baseline differs from the approved review')
    if len(after) != 296 or counts != {'easy': 130, 'medium': 74, 'open': 92}:
        raise ValueError('Unexpected post-pruning counts')
    sync_path = ROOT / 'benchmarks/hf_sync.json'
    sync = json.loads(sync_path.read_text())
    if 'local_liquid_pruning' in sync:
        raise ValueError('Pruning provenance already exists for an unpruned source')
    if not set(inventory['protected_reference_goal_ids']) <= kept_ids:
        raise ValueError('Pruning would remove an annotated reference goal')
    source.write_bytes(b''.join(line for line, row in zip(lines, before) if row['id'] in kept_ids))
    for split, version in [('easy', '1.7.0'), ('medium', '1.6.0')]:
        split_dir = ROOT / f'benchmarks/ahat-{split}'
        data_path = split_dir / 'cases.json'
        projected = [{k: r[k] for k in ('instruction', 'scene_graph', 'id')}
                     for r in after if r['type'] == split]
        data_path.write_text(json.dumps(projected, ensure_ascii=False, indent=2) + '\n')
        manifest_path = split_dir / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest.update(version=version, case_count=counts[split],
                        data_sha256=sha(data_path.read_bytes()), local_liquid_pruning=REVISION)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    sync.update(case_count=len(after), split_counts=counts)
    sync['local_liquid_pruning'] = {
        'version': REVISION, 'date': '2026-11-11', 'base_data_sha256': sha(before_bytes),
        'result_data_sha256': sha(source.read_bytes()),
        'policy': inventory['policy'], 'removed_case_count': changed,
        'reviewed_case_count': len(inventory['records']),
        'retained_representatives': [r for r in inventory['records'] if r['decision'] == 'retain'],
        'removed_cases': [r for r in inventory['records'] if r['decision'] == 'remove'],
        'inventory_path': 'docs/validation/liquid_pruning_inventory.json',
        'inventory_sha256': sha(INVENTORY.read_bytes()),
        'script_sha256': sha(Path(__file__).read_bytes()),
        'survivor_policy': 'Keep original source lines and order, with no field changes.',
        'previous_local_revision_entries_preserved': True,
    }
    sync['transformation'] += ' Remove 43 liquid-task variants from four overrepresented categories, retaining six representatives per category and preserving all surviving records (liquid-pruning-v1).'
    for artifact in sync['artifacts']:
        artifact['sha256'] = sha((ROOT / 'benchmarks' / artifact['path']).read_bytes())
    sync_path.write_text(json.dumps(sync, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
