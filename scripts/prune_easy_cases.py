#!/usr/bin/env python3
"""Apply the approved 13-task easy-pruning-v1 proposal; dry-run by default.

Stable IDs and review hashes guard the migration. Removed source lines are
archived before writing; surviving lines retain their bytes and order.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = 'docs/validation/easy_pruning_v1_inventory.json'
ARCHIVE = 'benchmarks/easy-pruning-v1/removed.jsonl'
REVISION = 'easy-pruning-v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def select_rows(rows, inventory):
    removed = set(inventory['remove_ids'])
    reviewed = {r['id']: r for g in inventory['groups'] for r in g['records']}
    ids = [r['id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate task IDs')
    protected = (set(reviewed) - removed) | set(inventory['extended_only_retained_ids'])
    if not protected <= set(ids):
        raise ValueError('Approved retained representative is missing')
    present = removed & set(ids)
    if present and present != removed:
        raise ValueError('Partially pruned snapshot')
    for row in rows:
        if row['id'] in reviewed:
            if row['type'] != 'easy' or sha(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()) != reviewed[row['id']]['record_sha256']:
                raise ValueError('Reviewed record changed since review')
    return [r for r in rows if r['id'] not in removed]


def migrate(root=ROOT, write=False):
    inventory = json.loads((root / INVENTORY).read_bytes())
    source = root / 'benchmarks/ahat_eval_set.jsonl'
    data = source.read_bytes()
    lines = data.splitlines(keepends=True)
    rows = [json.loads(line) for line in lines]
    after = select_rows(rows, inventory)
    removed = set(inventory['remove_ids'])
    counts = dict(Counter(r['type'] for r in after))
    if len(removed) != 13 or counts != {'easy': 117, 'medium': 65, 'open': 92}:
        raise ValueError('Unexpected approved IDs or post-pruning counts')
    for path, digest in inventory['unchanged_artifacts'].items():
        if sha((root / path).read_bytes()) != digest:
            raise ValueError(f'Unchanged artifact drift: {path}')
    sync_path = root / 'benchmarks/hf_sync.json'
    sync = json.loads(sync_path.read_bytes())
    archive = root / ARCHIVE
    report = {'removed_cases': len(rows) - len(after), 'case_count': len(after), 'split_counts': counts}
    if not report['removed_cases']:
        provenance = sync.get('local_easy_pruning', {})
        if sha(data) != provenance.get('result_data_sha256') or not archive.exists() or sha(archive.read_bytes()) != provenance.get('archive_sha256'):
            raise ValueError('Already-pruned snapshot lacks matching provenance/archive')
        for artifact in sync['artifacts']:
            if sha((root / 'benchmarks' / artifact['path']).read_bytes()) != artifact['sha256']:
                raise ValueError('Already-pruned artifact drift')
        if json.loads((root / 'benchmark_manifest.json').read_bytes())['active_case_count'] != 274:
            raise ValueError('Active count drift')
        return report
    easy = root / 'benchmarks/ahat-easy/cases.json'
    if sha(data) != inventory['source_sha256'] or sha(easy.read_bytes()) != inventory['easy_sha256']:
        raise ValueError('Source baseline differs from approved review')
    if 'local_easy_pruning' in sync:
        raise ValueError('Pruning provenance already exists for unpruned source')
    removed_bytes = b''.join(line for line, row in zip(lines, rows) if row['id'] in removed)
    after_bytes = b''.join(line for line, row in zip(lines, rows) if row['id'] not in removed)
    if archive.exists() and archive.read_bytes() != removed_bytes:
        raise ValueError('Archive conflict')
    projected = [{k: r[k] for k in ('instruction', 'scene_graph', 'id', 'domain_id') if k in r}
                 for r in after if r['type'] == 'easy']
    easy_bytes = dump(projected)
    manifest_path = root / 'benchmarks/ahat-easy/manifest.json'
    manifest = json.loads(manifest_path.read_bytes())
    manifest.update(version='1.11.0', case_count=117, data_sha256=sha(easy_bytes), local_easy_pruning=REVISION)
    additions = manifest['local_additions']
    additions['original_ids'] = additions['ids']
    additions['archived_ids'] = [i for i in additions['ids'] if i in removed]
    additions['ids'] = [i for i in additions['ids'] if i not in removed]
    main_path = root / 'benchmark_manifest.json'
    main = json.loads(main_path.read_bytes())
    main['active_case_count'] = 274
    sync.update(case_count=274, split_counts=counts)
    sync['local_easy_pruning'] = {
        'version': REVISION, 'date': inventory['date'],
        'base_data_sha256': sha(data), 'result_data_sha256': sha(after_bytes),
        'before_counts': inventory['current_counts'], 'after_counts': inventory['after_counts'],
        'removed_ids': inventory['remove_ids'], 'removed_case_count': 13,
        'retained_representative_ids': [r['id'] for g in inventory['groups'] for r in g['records'] if r['id'] not in removed],
        'inventory_path': INVENTORY, 'inventory_sha256': sha((root / INVENTORY).read_bytes()),
        'archive_path': ARCHIVE, 'archive_sha256': sha(removed_bytes),
        'script_sha256': sha(Path(__file__).read_bytes()),
        'policy': inventory['policy'], 'model_scores_used_for_selection': False,
        'survivor_policy': 'Preserve source lines byte-for-byte and in order.',
    }
    sync['transformation'] += ' Archive 13 approved easy semantic variants, preserving all survivors (easy-pruning-v1).'
    if write:
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(removed_bytes)
        source.write_bytes(after_bytes)
        easy.write_bytes(easy_bytes)
        manifest_path.write_bytes(dump(manifest))
        main_path.write_bytes(dump(main))
        sync['artifacts'].append({'path': 'easy-pruning-v1/removed.jsonl', 'sha256': sha(removed_bytes)})
        for artifact in sync['artifacts']:
            artifact['sha256'] = sha((root / 'benchmarks' / artifact['path']).read_bytes())
        sync_path.write_bytes(dump(sync))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    print(json.dumps(migrate(write=parser.parse_args().write)))
