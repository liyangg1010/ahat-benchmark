import copy
import json
import runpy
import unittest

from ahat_benchmark.judge.evaluator import RubricEvaluator, compute_final_state
from ahat_benchmark.judge.prompts import PROMPTS
from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from helpers import DOMAIN, PROJECT, FakeClient
from test_next_to import native_goal


class ServesTwoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repair = runpy.run_path(str(PROJECT / 'scripts/repair_cooking.py'))
        cls.rows = [json.loads(line) for line in
                    (PROJECT / 'benchmarks/ahat_eval_set.jsonl').read_text().splitlines()]
        cls.cases = {r['id']: r for r in cls.rows}

    def test_both_portion_annotations_reach_d1_api_request(self):
        for case_id, food in self.repair['TWO_SERVING_FOODS'].items():
            with self.subTest(case_id=case_id):
                row = self.cases[case_id]
                client = FakeClient()
                evaluator = RubricEvaluator(client=client, model='test-judge', domain_path=DOMAIN,
                                            max_attempts=1, dimension_workers=1)
                result = evaluator.evaluate(row['instruction'], row['scene_graph'], row['plan'])
                call = next(c for c in client.calls if c['messages'][0]['content'] == PROMPTS['D1'])
                evidence = call['messages'][1]['content']
                self.assertIn(f'(serves_two {food})', evidence)
                self.assertIn(f'(heated {food})', evidence)
                self.assertIn(f'(item_on_surface {food} ', evidence)
                self.assertIn(['serves_two', food], result['pddl_end_state'])
                # This verifies evidence delivery, not a real model's score.

    def test_capacity_survives_pick_heat_serve_and_scene_roundtrip(self):
        for case_id, food in self.repair['TWO_SERVING_FOODS'].items():
            row = self.cases[case_id]
            problem = full_problem(row['scene_graph'], DOMAIN)
            self.assertIn(['serves_two', food], final_state(problem, [], DOMAIN))
            manager = SceneGraphManager(row['scene_graph'], str(DOMAIN))
            for i, text in enumerate(row['plan'], 1):
                action = sexpr(text)
                manager.apply_action(action[0], action[1:])
                actual = final_state(full_problem(manager.scene_graph, DOMAIN), [], DOMAIN)
                self.assertIn(['serves_two', food], actual)
                self.assertEqual(actual, final_state(problem, row['plan'][:i], DOMAIN))

    def test_false_or_absent_capacity_is_not_inferred_from_food_name(self):
        for case_id, food in self.repair['TWO_SERVING_FOODS'].items():
            row = self.cases[case_id]
            for value in (False, None):
                graph = copy.deepcopy(row['scene_graph'])
                node = next(n for n in graph['objects'] if n['name'] == food)
                if value is None:
                    node['states'].pop('serves_two')
                else:
                    node['states']['serves_two'] = value
                state = compute_final_state(graph, row['plan'], DOMAIN)
                self.assertNotIn(['serves_two', food], state)
                self.assertFalse(native_goal(graph, row['plan'], row['reference_goal']))

    def test_capacity_does_not_replace_processing_or_serving(self):
        for case_id, food in self.repair['TWO_SERVING_FOODS'].items():
            row = self.cases[case_id]
            no_heat = [a for a in row['plan'] if not sexpr(a)[0].startswith('heat_')]
            state = compute_final_state(row['scene_graph'], no_heat, DOMAIN)
            self.assertIn(['serves_two', food], state)
            self.assertNotIn(['heated', food], state)
            self.assertFalse(native_goal(row['scene_graph'], no_heat, row['reference_goal']))
            heat_index = next(i for i, a in enumerate(row['plan']) if sexpr(a)[0].startswith('heat_'))
            no_serving = row['plan'][:heat_index + 2]
            state = compute_final_state(row['scene_graph'], no_serving, DOMAIN)
            self.assertIn(['serves_two', food], state)
            self.assertIn(['heated', food], state)
            self.assertFalse(native_goal(row['scene_graph'], no_serving, row['reference_goal']))

    def test_dataset_annotations_are_explicit_food_nodes_only(self):
        annotations = {}
        for row in self.rows:
            for group, nodes in row['scene_graph'].items():
                if group == 'links' or not isinstance(nodes, list):
                    continue
                for node in nodes:
                    if isinstance(node, dict) and node.get('states', {}).get('serves_two'):
                        self.assertTrue(node['states'].get('is_food'))
                        self.assertEqual(group, 'objects')
                        annotations[row['id']] = node['name']
        self.assertEqual(annotations, self.repair['ALL_TWO_SERVING_FOODS'])
        self.assertEqual(self.repair['repair_cases'](self.rows), self.rows)


if __name__ == '__main__':
    unittest.main()
