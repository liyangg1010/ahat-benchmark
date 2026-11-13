#!/usr/bin/env python3
"""Check both type trees, every active problem and every reference replay step.

Requires the dev extra for independent PDDL parsing. An optional pre-change
baseline records domains, data hashes, and each case's initial/final facts.
Native VAL reference and goal checks are run by check_reference_plans.py.
"""
import argparse
from collections import Counter
import hashlib
from importlib.metadata import version
import json
from pathlib import Path

from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser

from ahat_benchmark.domains import BASE_DOMAIN, LIQUID_DOMAIN, domain_registry, task_domain
from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.pddl_effects import compatible_type, typed_symbols
from ahat_benchmark.vendor.scene_graph import PDDLDomainParser, SceneGraphManager

ROOT = Path(__file__).resolve().parents[1]
LIQUID_ONLY = {'fill_from_faucet', 'fill_device_with_water', 'dispense_from_device', 'pour_into', 'pour'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def renamed_domain(old):
    def rename(node):
        if isinstance(node, list):
            return [rename(value) for value in node]
        return 'small_object' if node == 'object' else node
    expected = rename(old)
    types = next(s for s in expected if isinstance(s, list) and s[0] == ':types')
    require(types[1:3] == ['item', 'agent'], 'Unexpected baseline type tree')
    types[2:2] = ['-', 'object']
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, help='Pre-change folder with baseline.json and both domains')
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/domain_type_checks.json')
    args = parser.parse_args()
    baseline = json.loads((args.baseline / 'baseline.json').read_text()) if args.baseline else None
    counts, failures, records, domains = Counter(), [], [], {}
    source = ROOT / 'benchmarks/ahat_eval_set.jsonl'
    rows = list(map(json.loads, source.read_text().splitlines()))
    registry = domain_registry()
    for name, entry in registry.items():
        try:
            path = ROOT / entry['path']
            DomainParser()(path.read_text())
            parsed = PDDLDomainParser(path.read_text())
            require('object' not in parsed.types, 'Built-in root redeclared')
            require(parsed.types['item'] == 'object', 'item must inherit the built-in root')
            require(parsed.types['small_object'] == 'physobj', 'Wrong small-object parent')
            require(parsed.types['container'] == 'small_object', 'Wrong container parent')
            for kind in parsed.types:
                visited, current = set(), kind
                while current != 'object':
                    require(current not in visited and current in parsed.types, 'Cyclic/unknown type parent')
                    visited.add(current)
                    current = parsed.types[current]
                require(compatible_type(kind, 'object', parsed.types), 'Subtype does not reach root')
            for signature in [*parsed.predicates.values(), *(a['parameters'] for a in parsed.actions.values())]:
                require(set(signature.values()) <= parsed.types.keys() | {'object'}, 'Undeclared parameter type')
            if name == BASE_DOMAIN:
                require(not LIQUID_ONLY & parsed.actions.keys(), 'Liquid action reintroduced into ordinary domain')
            elif name == LIQUID_DOMAIN:
                require(LIQUID_ONLY <= parsed.actions.keys(), 'Liquid action missing')
            if baseline:
                old = sexpr((args.baseline / path.name).read_text())
                require(sexpr(path.read_text()) == renamed_domain(old), 'Unexpected non-type domain change')
                counts['domains_with_only_type_changes'] += 1
            domains[name] = {'types': parsed.types, 'action_count': len(parsed.actions),
                             'independent_parser': 'passed', 'acyclic_rooted_tree': True}
            counts['domains_checked'] += 1
        except Exception as exc:
            failures.append({'domain': name, 'error': str(exc)})
    if baseline:
        require(sha(source) == baseline['source_sha256'], 'Source data changed')
        require([r['id'] for r in rows] == list(baseline['cases']), 'Task IDs/order changed')
        for file, digest in baseline['data_files'].items():
            require(sha(ROOT / file) == digest, f'Dataset bytes changed: {file}')
    external_problem_parser = ProblemParser()
    for row in rows:
        try:
            domain = task_domain(row)
            dropped = []
            problem = full_problem(row['scene_graph'], domain, dropped)
            require(not dropped, 'Initial facts dropped during type filtering')
            external_problem_parser(problem)
            declarations = typed_symbols(next(s[1:] for s in sexpr(problem)
                                              if isinstance(s, list) and s[0] == ':objects'))
            require('object' not in declarations.values(), 'Small items exported as universal root')
            initial = final_state(problem, [], domain)
            final = final_state(problem, row['plan'], domain)
            if baseline:
                before = baseline['cases'][row['id']]
                require(initial == before['initial'], 'Initial facts changed')
                require(final == before['final'], 'Final facts changed')
                old_declarations = typed_symbols(next(s[1:] for s in sexpr(before['problem'])
                                                      if isinstance(s, list) and s[0] == ':objects'))
                require(declarations == {name: 'small_object' if kind == 'object' else kind
                                         for name, kind in old_declarations.items()}, 'Unexpected object/type change')
                counts['unchanged_initial_and_final_states'] += 1
            manager = SceneGraphManager(row['scene_graph'], str(domain))
            for index, step in enumerate(row['plan']):
                action = sexpr(step)
                manager.apply_action(action[0], action[1:])
                replay_dropped = []
                actual = final_state(full_problem(manager.scene_graph, domain, replay_dropped), [], domain)
                require(not replay_dropped, f'Facts dropped after step {index + 1}')
                require(actual == final_state(problem, row['plan'][:index + 1], domain),
                        f'Scene/PDDL mismatch after step {index + 1}')
                counts['scene_replay_steps'] += 1
            counts['cases_checked'] += 1
            counts['independently_parsed_problems'] += 1
            counts['initial_facts_dropped'] += len(dropped)
            records.append({'id': row['id'], 'domain_id': row.get('domain_id', BASE_DOMAIN),
                            'objects': len(declarations), 'replay_steps': len(row['plan']),
                            'problem_sha256': hashlib.sha256(problem.encode()).hexdigest()})
        except Exception as exc:
            failures.append({'id': row['id'], 'error': str(exc)})
    report = {'revision': 'type-hierarchy-v1', 'scope': 'all active cases; archived/quarantined cases excluded',
              'source_sha256': sha(source), 'domains': registry, 'domain_checks': domains,
              'independent_parser': {'name': 'pddl', 'version': version('pddl')},
              'baseline_checked': baseline is not None,
              'counts': dict(counts), 'cases': records, 'failures': failures}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'counts': dict(counts), 'failures': failures}, ensure_ascii=False))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
