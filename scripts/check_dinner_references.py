#!/usr/bin/env python3
"""Validate adopted dinner references and their offline stage/outcome witnesses.

These checks do not require other valid solutions to copy the reference plan,
menu or locations, and do not add runtime scoring gates.
"""
import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path

from ahat_benchmark.domains import domain_registry, task_domain
from ahat_benchmark.pddl import final_state, sexpr
from ahat_benchmark.val.validator import validate_plan
from check_reference_plans import native_goal

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def satisfies(goals, state):
    facts = {tuple(f) for f in state}
    return all(tuple(expr[1]) not in facts if expr[0] == 'not' else tuple(expr) in facts
               for expr in map(sexpr, goals))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/dinner_reference_checks.json')
    parser.add_argument('--adoption', type=Path, default=ROOT / 'docs/validation/dinner_reference_v1_adoption.json')
    args = parser.parse_args()
    source = ROOT / 'benchmarks/ahat_eval_set.jsonl'
    rows = {r['id']: r for r in map(json.loads, source.read_text().splitlines())}
    adoption = json.loads(args.adoption.read_text())
    counts, failures = Counter(), []
    for record in adoption['records']:
        try:
            row = rows[record['id']]
            domain = task_domain(row)
            require(row['plan'] == record['plan'], 'Reference differs from adopted example')
            if record.get('reference_goal_written'):
                require(row.get('reference_goal') == record['final_goals'], 'Stored reference goal differs')

            def validate(plan):
                result = validate_plan(scene_graph=row['scene_graph'], plan=plan, domain_path=domain,
                                       val_executable=ROOT / 'vendor/val/Validate', timeout_seconds=10)
                require(result['status'] == 'valid', result.get('fail_reason', 'Invalid reference'))
                return result['problem_pddl']

            problem = validate(row['plan'])
            require(native_goal(problem, row['plan'], record['final_goals'], domain), 'Final witness goal missed')
            counts['valid_references_and_final_goals'] += 1
            for stage in record['stage_goals']:
                require(0 < stage['after_step'] < len(row['plan']), 'Stage must precede the final phase')
                require(native_goal(problem, row['plan'][:stage['after_step']], stage['goals'], domain),
                        'Serving stage missed before cleanup')
                counts['serving_stages_before_cleanup'] += 1
            for key, action in [('omit_heating', 'heat_on_heating_device'), ('omit_lighting', 'light_on')]:
                if key not in record['controls']:
                    continue
                action = record['controls'][key].get('action', action)
                control = [step for step in row['plan'] if sexpr(step)[0] != action]
                validate(control)
                require(not native_goal(problem, control, record['final_goals'], domain), 'Omitted action still meets goals')
                counts['omission_controls'] += 1
            if 'stop_before_serving' in record['controls']:
                control = row['plan'][:record['controls']['stop_before_serving']['after_step']]
                validate(control)
                require(not native_goal(problem, control, record['final_goals'], domain),
                        'Unserved food still meets meal goals')
                counts['serving_controls'] += 1
            for capacity in record['controls'].get('missing_capacity', []):
                graph = copy.deepcopy(row['scene_graph'])
                node = next(n for n in graph['objects'] if n['name'] == capacity['food'])
                require(node['states'].pop(capacity['predicate'], False), 'Capacity annotation missing')
                result = validate_plan(scene_graph=graph, plan=row['plan'], domain_path=domain,
                                       val_executable=ROOT / 'vendor/val/Validate', timeout_seconds=10)
                require(result['status'] == 'valid', 'Capacity unexpectedly changes executability')
                require(not native_goal(result['problem_pddl'], row['plan'], record['final_goals'], domain),
                        'Missing capacity still meets meal goals')
                counts['capacity_controls'] += 1
            if 'skip_serving_counterexample' in record['controls']:
                control = record['controls']['skip_serving_counterexample']['plan']
                validate(control)
                require(native_goal(problem, control, record['final_goals'], domain), 'Final-only counterexample changed')
                stage_goals = record['stage_goals'][0]['goals']
                require(not any(satisfies(stage_goals, final_state(problem, control[:i], domain))
                                for i in range(len(control) + 1)), 'Counterexample unexpectedly served dinner')
                counts['final_only_goal_insufficiency_controls'] += 1
        except Exception as exc:
            failures.append({'id': record['id'], 'error': str(exc)})
    report = {'revision': adoption['revision'], 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'domains': domain_registry(), 'counts': dict(counts), 'failures': failures}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'counts': dict(counts), 'failures': failures}, ensure_ascii=False))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
