#!/usr/bin/env python3
"""Offline reference validity, adjacency/cooking goals and scene replay controls."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import SceneGraphManager


ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / 'vendor/pddl/domain_0102_test.pddl'
VAL = ROOT / 'vendor/val/Validate'


def native_goal(problem, plan, goals):
    problem = problem.replace('(:goal (and))', '(:goal (and ' + ' '.join(goals) + '))')
    with tempfile.TemporaryDirectory(prefix='ahat-goals-') as directory:
        folder = Path(directory)
        (folder / 'problem.pddl').write_text(problem)
        (folder / 'plan.txt').write_text('\n'.join(plan))
        env = {**os.environ, 'LD_LIBRARY_PATH': str(VAL.parent) + ':' + os.environ.get('LD_LIBRARY_PATH', '')}
        result = subprocess.run([str(VAL), '-v', str(DOMAIN), str(folder / 'problem.pddl'), str(folder / 'plan.txt')],
                                capture_output=True, text=True, timeout=10, env=env)
    output = result.stdout + result.stderr
    if result.returncode == 0 and 'Successful plans:' in output:
        return True
    if 'Failed plans:' in output or 'Plan failed' in output:
        return False
    raise RuntimeError('VAL did not return a goal verdict')


def ordinary_placement(plan):
    output = []
    for text in plan:
        action = sexpr(text)
        if action[0] in {'place_next_to_surface', 'place_next_to_inside'}:
            name = 'place_on_surface' if action[0].endswith('surface') else 'place_in_receptacle'
            text = f'({name} {action[1]} {action[2]} {action[4]})'
        output.append(text)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/reference_plan_checks.json')
    args = parser.parse_args()
    source_path = ROOT / 'benchmarks/ahat_eval_set.jsonl'
    source = source_path.read_bytes()
    rows = [json.loads(line) for line in source.decode().splitlines()]
    sync = json.loads((ROOT / 'benchmarks/hf_sync.json').read_text())
    cooking_ids = set(sync.get('local_heated', sync.get('local_cooking', {})).get('reference_repaired_ids', []))
    failures, counts, cases = [], Counter(), []
    for split in ('easy', 'medium', 'open'):
        projected = [{k: r[k] for k in ('id', 'instruction', 'scene_graph')} for r in rows if r['type'] == split]
        actual = json.loads((ROOT / f'benchmarks/ahat-{split}/cases.json').read_text())
        if projected != actual:
            failures.append({'split': split, 'error': 'source/split mismatch'})
    for row in rows:
        checked = validate_plan(scene_graph=row['scene_graph'], plan=row['plan'], domain_path=DOMAIN,
                                val_executable=VAL, timeout_seconds=10)
        counts[checked['status']] += 1
        if checked['status'] != 'valid':
            failures.append({'id': row['id'], 'error': checked.get('fail_reason')})
            continue
        state = {tuple(f) for f in final_state(checked['problem_pddl'], row['plan'], DOMAIN)}
        for f in state:
            if f[0] == 'next_to' and ((f[0], f[2], f[1], f[3]) not in state or not any(
                (rel, f[1], f[3]) in state and (rel, f[2], f[3]) in state
                for rel in ('item_on_surface', 'item_in_receptacle')
            )):
                failures.append({'id': row['id'], 'error': 'unsupported/asymmetric adjacency', 'fact': f})
        if 'reference_goal' in row:
            passed = native_goal(checked['problem_pddl'], row['plan'], row['reference_goal'])
            counts['annotated_goals_passed'] += passed
            record = {'id': row['id'], 'reference_goal_passed': passed}
            if not passed:
                failures.append({'id': row['id'], 'error': 'reference goal failed'})
            if any(sexpr(goal)[0] == 'next_to' for goal in row['reference_goal']):
                control = ordinary_placement(row['plan'])
                result = validate_plan(scene_graph=row['scene_graph'], plan=control, domain_path=DOMAIN,
                                       val_executable=VAL, timeout_seconds=10)
                missed = not native_goal(checked['problem_pddl'], control, row['reference_goal'])
                record['ordinary_placement_valid'] = result['status'] == 'valid'
                record['ordinary_placement_misses_goal'] = missed
                if result['status'] != 'valid' or not missed:
                    failures.append({'id': row['id'], 'error': 'invalid adjacency control'})
                counts['adjacency_controls_passed'] += result['status'] == 'valid' and missed
            if row['id'] in cooking_ids:
                control = [text for text in row['plan'] if not sexpr(text)[0].startswith('heat_')]
                result = validate_plan(scene_graph=row['scene_graph'], plan=control, domain_path=DOMAIN,
                                       val_executable=VAL, timeout_seconds=10)
                missed = not native_goal(checked['problem_pddl'], control, row['reference_goal'])
                record['processing_omitted_valid'] = result['status'] == 'valid'
                record['processing_omitted_misses_goal'] = missed
                if result['status'] != 'valid' or not missed:
                    failures.append({'id': row['id'], 'error': 'invalid cooking/heating control'})
                counts['cooking_controls_passed'] += result['status'] == 'valid' and missed
            if row.get('source', {}).get('revision') == 'next-to-v1' or row['id'] in cooking_ids:
                manager = SceneGraphManager(row['scene_graph'], str(DOMAIN))
                prefix = []
                for text in row['plan']:
                    action = sexpr(text)
                    prefix.append(text)
                    manager.apply_action(action[0], action[1:])
                    actual = final_state(full_problem(manager.scene_graph, DOMAIN), [], DOMAIN)
                    expected = final_state(checked['problem_pddl'], prefix, DOMAIN)
                    if actual != expected:
                        failures.append({'id': row['id'], 'error': 'scene/PDDL replay mismatch', 'action': text})
                key = 'cooking_scene_roundtrip_steps' if row['id'] in cooking_ids else 'scene_roundtrip_steps'
                counts[key] += len(prefix)
            cases.append(record)
    manifest = json.loads((ROOT / 'benchmark_manifest.json').read_text())
    output = {'kind': 'offline_reference_and_goal_validation_not_llm_scores',
              'protocol': {key: manifest[key] for key in ('version', 'domain', 'validator', 'judge')},
              'source_sha256': hashlib.sha256(source).hexdigest(),
              'domain_sha256': hashlib.sha256(DOMAIN.read_bytes()).hexdigest(),
              'implementation_sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in [Path(__file__), ROOT / 'scripts/next_to_cases.py',
                                                 ROOT / 'scripts/repair_cooking.py',
                                                 *sorted((ROOT / 'src/ahat_benchmark').rglob('*.py'))]},
              'counts': dict(counts), 'annotated_cases': cases, 'failures': failures}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'counts': dict(counts), 'failures': len(failures)}))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
