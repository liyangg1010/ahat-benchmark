import copy
import json
import runpy
import unittest

from ahat_benchmark.judge.evaluator import RubricEvaluator, build_inputs, compute_final_state
from ahat_benchmark.judge.prompts import PROMPTS
from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from helpers import DOMAIN, VAL, PROJECT, FakeClient, scene
from test_next_to import native_goal


class GroupPortionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repair = runpy.run_path(str(PROJECT / 'scripts/repair_cooking.py'))
        cls.rows = list(map(json.loads, (PROJECT / 'benchmarks/ahat_eval_set.jsonl').read_text().splitlines()))
        cls.cases = {r['id']: r for r in cls.rows}
        cls.additions = [(i, food, pred) for mapping, pred in [
            (cls.repair['ADDITIONAL_TWO_SERVING_FOODS'], 'serves_two'),
            (cls.repair['GROUP_SERVING_FOODS'], 'serves_group')]
            for i, food in mapping.items()]
        for name in ['group_meal_reference_v1_adoption.json', 'guest_dinner_v1_adoption.json']:
            adoption = json.loads((PROJECT / 'docs/validation' / name).read_text())
            cls.additions = sorted(set(cls.additions) | {
                (r['id'], c['food'], c['predicate']) for r in adoption['records']
                for c in r['controls']['missing_capacity']})

    def test_new_capacity_facts_reach_actual_d1_requests_without_inventing_processing(self):
        for case_id, food, pred in self.additions:
            with self.subTest(case_id=case_id):
                row = self.cases[case_id]
                client = FakeClient()
                result = RubricEvaluator(client=client, model='test', domain_path=DOMAIN,
                                         max_attempts=1, dimension_workers=1).evaluate(
                    row['instruction'], row['scene_graph'], row['plan'])
                call = next(c for c in client.calls if c['messages'][0]['content'] == PROMPTS['D1'])
                self.assertIn(f'({pred} {food})', call['messages'][1]['content'])
                self.assertIn(['is_food', food], result['pddl_end_state'])
                self.assertNotIn(['heated', food], compute_final_state(row['scene_graph'], [], DOMAIN))
                no_heat = [step for step in row['plan'] if not sexpr(step)[0].startswith('heat_')]
                unprocessed = compute_final_state(row['scene_graph'], no_heat, DOMAIN)
                self.assertNotIn(['heated', food], unprocessed)
                self.assertIn([pred, food], unprocessed)
                if pred == 'serves_group':
                    self.assertNotIn(['serves_two', food], result['pddl_end_state'])

    def test_static_capacity_survives_original_plans_and_scene_roundtrips(self):
        for case_id, food, pred in self.additions:
            row = self.cases[case_id]
            problem = full_problem(row['scene_graph'], DOMAIN)
            manager = SceneGraphManager(row['scene_graph'], str(DOMAIN))
            for i, step in enumerate(row['plan'], 1):
                action = sexpr(step)
                manager.apply_action(action[0], action[1:])
                state = final_state(full_problem(manager.scene_graph, DOMAIN), [], DOMAIN)
                self.assertIn([pred, food], state)
                self.assertEqual(state, final_state(problem, row['plan'][:i], DOMAIN))

    def test_false_absent_capacity_is_not_inferred_and_annotations_stay_explicit(self):
        annotations = set()
        for row in self.rows:
            for node in row['scene_graph']['objects']:
                if node.get('states', {}).get('serves_group'):
                    self.assertTrue(node['states']['is_food'])
                    annotations.add((row['id'], node['name']))
        self.assertEqual(annotations, {(i, food) for i, food, pred in self.additions if pred == 'serves_group'})
        self.assertEqual(self.repair['repair_cases'](self.rows), self.rows)
        for case_id, food, pred in self.additions:
            row = self.cases[case_id]
            self.assertTrue(native_goal(row['scene_graph'], row['plan'], [f'({pred} {food})']))
            for value in (False, None):
                graph = copy.deepcopy(row['scene_graph'])
                node = next(n for n in graph['objects'] if n['name'] == food)
                if value is None:
                    node['states'].pop(pred)
                else:
                    node['states'][pred] = value
                self.assertNotIn([pred, food], compute_final_state(graph, row['plan'], DOMAIN))
                self.assertFalse(native_goal(graph, row['plan'], [f'({pred} {food})']))

    def test_temporary_delivery_and_omission_have_same_d1_but_distinct_plan_evidence(self):
        graph = scene()
        graph['furnitures'].append({'name': 'counter_1', 'states': {}})
        graph['links'] = [['room_1', 'table_1', 'in'], ['room_1', 'counter_1', 'in'],
                          ['counter_1', 'cup_1', 'on']]
        graph['agent'][0]['location'] = 'counter_1'
        complete = ['(navigate agent_0 counter_1 cup_1)',
                    '(pick_from_surface agent_0 cup_1 counter_1)',
                    '(navigate agent_0 cup_1 table_1)', '(place_on_surface agent_0 cup_1 table_1)',
                    '(navigate agent_0 table_1 cup_1)', '(pick_from_surface agent_0 cup_1 table_1)',
                    '(navigate agent_0 cup_1 counter_1)', '(place_on_surface agent_0 cup_1 counter_1)']
        omitted = ['(navigate agent_0 counter_1 table_1)', '(navigate agent_0 table_1 counter_1)']
        evidence = []
        for plan in (complete, omitted):
            checked = validate_plan(scene_graph=graph, plan=plan, domain_path=DOMAIN,
                                    val_executable=VAL, timeout_seconds=10)
            self.assertEqual(checked['status'], 'valid')
            state = compute_final_state(graph, plan, DOMAIN)
            evidence.append(build_inputs('Place cup_1 on table_1, then return it to counter_1.', graph, plan, state))
        self.assertEqual(evidence[0]['D1'], evidence[1]['D1'])
        self.assertNotEqual(evidence[0]['D3'], evidence[1]['D3'])
        self.assertNotEqual(evidence[0]['D4'], evidence[1]['D4'])
