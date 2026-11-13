import copy
import os
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest

from ahat_benchmark.judge.evaluator import RubricEvaluator
from ahat_benchmark.judge.scene_summary import summarize_scene
from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.scene import normalize_links
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from helpers import DOMAIN, VAL, PROJECT, FakeClient, scene


def adjacency_scene(inside=False):
    graph = scene()
    graph['furnitures'][0]['states'] = {'can_be_opened': inside, 'is_open': inside}
    relation = 'in' if inside else 'on'
    graph['links'] = [['room_1', 'table_1', 'in'], ['table_1', 'cup_1', relation],
                      ['table_1', 'lid_1', relation],
                      {'relation': 'next_to', 'obj1': 'cup_1', 'obj2': 'lid_1', 'location': 'table_1'}]
    return graph


def native_goal(graph, plan, goals, domain=DOMAIN):
    problem = full_problem(graph, domain).replace('(:goal (and))', '(:goal (and ' + ' '.join(goals) + '))')
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        (folder / 'problem.pddl').write_text(problem)
        (folder / 'plan.txt').write_text('\n'.join(plan))
        env = {**os.environ, 'LD_LIBRARY_PATH': str(VAL.parent) + ':' + os.environ.get('LD_LIBRARY_PATH', '')}
        result = subprocess.run([str(VAL), '-v', str(domain), str(folder / 'problem.pddl'), str(folder / 'plan.txt')],
                                capture_output=True, text=True, timeout=10, env=env)
    return result.returncode == 0 and 'Successful plans:' in result.stdout


class AdjacencyTests(unittest.TestCase):
    def test_local_task_definitions_reproduce_bundled_records(self):
        records = runpy.run_path(str(PROJECT / 'scripts/next_to_cases.py'))['build_cases']()
        bundled = {r['id']: r for r in map(json.loads, (PROJECT / 'benchmarks/ahat_eval_set.jsonl').read_text().splitlines())}
        self.assertEqual(len({r['id'] for r in records}), 10)
        archived = {r['id']: r for r in map(json.loads, (PROJECT / 'benchmarks/easy-pruning-v1/removed.jsonl').read_text().splitlines())}
        self.assertFalse(set(bundled) & set(archived))
        self.assertEqual(sum(r['id'] in bundled for r in records), 8)
        self.assertEqual(sum(r['id'] in archived for r in records), 2)
        self.assertEqual([(bundled | archived)[r['id']] for r in records], records)

    def test_input_is_undirected_idempotent_and_does_not_invent_transitivity(self):
        graph = adjacency_scene()
        graph['objects'].append({'name': 'spoon_1', 'states': {}})
        graph['links'] += [['table_1', 'spoon_1', 'on'],
                           {'relation': 'next_to', 'obj1': 'lid_1', 'obj2': 'cup_1', 'location': 'table_1'},
                           {'relation': 'next_to', 'obj1': 'lid_1', 'obj2': 'spoon_1', 'location': 'table_1'}]
        original = copy.deepcopy(graph)
        links = normalize_links(graph)
        self.assertEqual(len([x for x in links if x['relation'] == 'next_to']), 2)
        self.assertEqual(links, normalize_links({**graph, 'links': links}))
        problem = full_problem(graph, DOMAIN)
        self.assertIn('(next_to cup_1 lid_1 table_1)', problem)
        self.assertIn('(next_to lid_1 cup_1 table_1)', problem)
        self.assertNotIn('(next_to cup_1 spoon_1 table_1)', problem)
        self.assertEqual(graph, original)

    def test_initial_adjacency_requires_real_shared_support(self):
        for variant in ('unknown', 'self', 'held', 'different_support', 'different_relation', 'legacy_adjacency', 'state_boolean'):
            with self.subTest(variant=variant):
                graph = adjacency_scene()
                if variant == 'unknown':
                    graph['links'][-1]['obj2'] = 'missing_1'
                elif variant == 'self':
                    graph['links'][-1]['obj2'] = 'cup_1'
                elif variant == 'held':
                    graph['agent'][0]['holding'] = 'cup_1'
                elif variant == 'different_support':
                    graph['links'][1][0] = 'room_1'
                elif variant == 'different_relation':
                    graph['links'][1][2] = 'in'
                elif variant == 'legacy_adjacency':
                    graph['links'][-1] = ['cup_1', 'lid_1', 'next_to']
                else:
                    graph['objects'][0]['states']['next_to'] = True
                with self.assertRaises(ValueError):
                    full_problem(graph, DOMAIN)

    def test_pick_clears_both_directions_in_val_simulator_and_scene_roundtrip(self):
        for inside in (False, True):
            with self.subTest(inside=inside):
                graph = adjacency_scene(inside)
                action = 'pick_from_receptacle' if inside else 'pick_from_surface'
                plan = [f'({action} agent_0 cup_1 table_1)']
                goals = ['(holding agent_0 cup_1)', '(not (next_to cup_1 lid_1 table_1))',
                         '(not (next_to lid_1 cup_1 table_1))']
                self.assertTrue(native_goal(graph, plan, goals))
                state = final_state(full_problem(graph, DOMAIN), plan, DOMAIN)
                self.assertFalse(any(f[0] == 'next_to' for f in state))
                manager = SceneGraphManager(graph, str(DOMAIN))
                manager.apply_action(action, ['agent_0', 'cup_1', 'table_1'])
                restored = full_problem(manager.scene_graph, DOMAIN)
                self.assertEqual(state, final_state(restored, [], DOMAIN))

    def test_pick_preserves_unrelated_pairs_and_ordinary_put_back_does_not_restore(self):
        graph = adjacency_scene()
        for name in ('fork_1', 'spoon_1'):
            graph['objects'].append({'name': name, 'states': {}})
            graph['links'].append(['table_1', name, 'on'])
        graph['links'].append({'relation': 'next_to', 'obj1': 'fork_1', 'obj2': 'spoon_1', 'location': 'table_1'})
        plan = ['(pick_from_surface agent_0 cup_1 table_1)', '(navigate agent_0 cup_1 table_1)',
                '(place_on_surface agent_0 cup_1 table_1)']
        goals = ['(not (next_to cup_1 lid_1 table_1))', '(next_to fork_1 spoon_1 table_1)',
                 '(next_to spoon_1 fork_1 table_1)']
        self.assertTrue(native_goal(graph, plan, goals))
        state = final_state(full_problem(graph, DOMAIN), plan, DOMAIN)
        self.assertIn(['next_to', 'fork_1', 'spoon_1', 'table_1'], state)
        self.assertNotIn(['next_to', 'cup_1', 'lid_1', 'table_1'], state)
        plan[-1] = '(place_next_to_surface agent_0 cup_1 lid_1 table_1)'
        self.assertTrue(native_goal(graph, plan, ['(next_to cup_1 lid_1 table_1)']))

    def test_goal_depends_on_instruction_not_optional_extra_adjacency(self):
        graph = adjacency_scene()
        graph['links'] = graph['links'][:-1]
        prefix = ['(pick_from_surface agent_0 cup_1 table_1)', '(navigate agent_0 cup_1 table_1)']
        ordinary = prefix + ['(place_on_surface agent_0 cup_1 table_1)']
        adjacent = prefix + ['(place_next_to_surface agent_0 cup_1 lid_1 table_1)']
        placement_goal = ['(item_on_surface cup_1 table_1)']
        adjacency_goal = placement_goal + ['(next_to cup_1 lid_1 table_1)']
        # Both fulfil placement; extra adjacency must not make the plan wrong.
        self.assertTrue(native_goal(graph, ordinary, placement_goal))
        self.assertTrue(native_goal(graph, adjacent, placement_goal))
        self.assertFalse(native_goal(graph, ordinary, adjacency_goal))
        self.assertTrue(native_goal(graph, adjacent, adjacency_goal))

    def test_scene_and_direct_effect_paths_ground_universal_deletions(self):
        graph = adjacency_scene()
        manager = SceneGraphManager(graph, str(DOMAIN))
        expressions = manager.pddl_parser.get_action_effects('(pick_from_surface agent_0 cup_1 table_1)')
        # Apply a complete action atomically; intermediate state need not satisfy invariants.
        manager.apply_predicates('(and ' + ' '.join(expressions) + ')')
        self.assertNotIn('next_to', full_problem(manager.scene_graph, DOMAIN))
        manager = SceneGraphManager(graph, str(DOMAIN))
        for expression in expressions:
            manager.apply_predicates(expression)
        self.assertNotIn('next_to', full_problem(manager.scene_graph, DOMAIN))

    def test_dictionary_links_reach_all_judge_dimensions(self):
        graph = adjacency_scene()
        graph['links'] = normalize_links(graph)
        plan = ['(pick_from_surface agent_0 cup_1 table_1)']
        result = validate_plan(scene_graph=graph, plan=plan, domain_path=DOMAIN, val_executable=VAL, timeout_seconds=10)
        self.assertEqual(result['status'], 'valid')
        client = FakeClient()
        judge = RubricEvaluator(client=client, model='test', domain_path=DOMAIN)
        result = judge.evaluate('Pick up cup_1.', graph, plan)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(client.calls), 4)
        self.assertIn('initial_next_to', result['inputs']['D2'])
        self.assertNotIn('(next_to ', result['inputs']['D1'])

    def test_legacy_and_dictionary_support_links_have_identical_summary(self):
        graph = scene()
        self.assertEqual(summarize_scene(graph), summarize_scene({**graph, 'links': normalize_links(graph)}))


if __name__ == '__main__':
    unittest.main()
