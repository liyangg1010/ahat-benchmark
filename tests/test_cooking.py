import copy
import json
import runpy
import unittest

from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import PDDLDomainParser, SceneGraphManager
from helpers import DOMAIN, VAL, PROJECT
from test_next_to import native_goal


def heating_scene(kind='microwave', food=True, heated=False):
    surface = kind == 'surface'
    return {
        'rooms': [{'name': 'room_1', 'states': {}}],
        'furnitures': [{'name': 'heater_1', 'states': {
            'is_heating_device': True, 'is_powerable': True, 'is_powered_on': True,
            {'microwave': 'is_microwave', 'oven': 'is_oven', 'surface': 'is_cooking_surface'}[kind]: True,
            'can_be_opened': not surface, 'is_open': False,
        }}],
        'objects': [
            {'name': 'target_1', 'states': {'is_food': food, 'can_be_heated': True, 'heated': heated}},
            {'name': 'pot_1', 'states': {'is_heating_container': True}},
        ],
        'agent': [{'name': 'agent_0', 'location': 'heater_1', 'holding': None}],
        'person': [],
        'links': [['room_1', 'heater_1', 'in'], ['heater_1', 'pot_1', 'on'],
                  ['pot_1', 'target_1', 'on'] if surface else ['heater_1', 'target_1', 'in']],
    }


def action(kind):
    return ('(heat_on_heating_device agent_0 target_1 pot_1 heater_1)' if kind == 'surface'
            else f'(heat_with_{kind} agent_0 target_1 heater_1)')


class CookingTests(unittest.TestCase):
    def validate(self, graph, plan):
        return validate_plan(scene_graph=graph, plan=plan, domain_path=DOMAIN,
                             val_executable=VAL, timeout_seconds=10)

    def test_food_and_nonfood_share_one_thermal_result_and_scene_roundtrip(self):
        for kind in ('microwave', 'oven', 'surface'):
            for food in (True, False):
                with self.subTest(kind=kind, food=food):
                    graph = heating_scene(kind, food=food)
                    plan = [action(kind)]
                    checked = self.validate(graph, plan)
                    self.assertEqual(checked['status'], 'valid', checked.get('fail_reason'))
                    self.assertTrue(native_goal(graph, plan, ['(heated target_1)']))
                    manager = SceneGraphManager(graph, str(DOMAIN))
                    parsed = sexpr(plan[0])
                    manager.apply_action(parsed[0], parsed[1:])
                    self.assertEqual(final_state(checked['problem_pddl'], plan, DOMAIN),
                                     final_state(full_problem(manager.scene_graph, DOMAIN), [], DOMAIN))
                    self.assertTrue(manager.scene_graph['objects'][0]['states']['heated'])

    def test_heatability_and_appliance_state_guards(self):
        for kind in ('microwave', 'oven', 'surface'):
            for variant in ('not_heatable', 'not_powered', 'wrong_device', 'wrong_placement', 'holding'):
                with self.subTest(kind=kind, variant=variant):
                    graph = heating_scene(kind)
                    states = graph['furnitures'][0]['states']
                    if variant == 'not_heatable':
                        graph['objects'][0]['states']['can_be_heated'] = False
                    elif variant == 'not_powered':
                        states['is_powered_on'] = False
                    elif variant == 'wrong_device':
                        states[{'microwave': 'is_microwave', 'oven': 'is_oven', 'surface': 'is_cooking_surface'}[kind]] = False
                    elif variant == 'wrong_placement':
                        graph['links'][-1] = ['room_1', 'target_1', 'on']
                    else:
                        graph['agent'][0]['holding'] = 'pot_1'
                    self.assertEqual(self.validate(graph, [action(kind)])['status'], 'invalid')

    def test_stovetop_requires_real_cookware(self):
        graph = heating_scene('surface')
        graph['objects'][1]['states']['is_heating_container'] = False
        self.assertEqual(self.validate(graph, [action('surface')])['status'], 'invalid')

    def test_closed_powered_appliances_process_without_reopening(self):
        for kind in ('microwave', 'oven'):
            graph = heating_scene(kind)
            graph['furnitures'][0]['states'].update(is_open=True, is_powered_on=False)
            prefix = ['(close agent_0 heater_1)', '(power_on agent_0 heater_1)']
            self.assertEqual(self.validate(graph, prefix + [action(kind)])['status'], 'valid')
            reopened = prefix + ['(open agent_0 heater_1)', action(kind)]
            self.assertEqual(self.validate(graph, reopened)['status'], 'invalid')

    def test_initial_heated_state_and_removed_action_family(self):
        parsed = PDDLDomainParser(DOMAIN.read_text())
        self.assertNotIn('cooked', parsed.predicates)
        self.assertFalse(any(name.startswith('cook_') for name in parsed.actions))
        for kind in ('microwave', 'oven', 'surface'):
            graph = heating_scene(kind, heated=True)
            self.assertIn(['heated', 'target_1'], final_state(full_problem(graph, DOMAIN), [], DOMAIN))
            self.assertEqual(self.validate(graph, [action(kind)])['status'], 'invalid')
            graph = heating_scene(kind)
            self.assertEqual(self.validate(graph, [action(kind).replace('(heat_', '(cook_')])['status'], 'invalid')

    def test_power_on_alone_does_not_establish_processing_result(self):
        for kind in ('microwave', 'oven', 'surface'):
            graph = heating_scene(kind)
            graph['furnitures'][0]['states']['is_powered_on'] = False
            self.assertTrue(native_goal(graph, ['(power_on agent_0 heater_1)'], ['(not (heated target_1))']))

    def test_legacy_state_migration_does_not_infer_heated_from_cooked(self):
        repair = runpy.run_path(str(PROJECT / 'scripts/repair_cooking.py'))
        graph = heating_scene()
        graph['objects'][0]['states'] = {'cooked': True, 'is_heated': False, 'can_be_heated': True}
        row = {'id': 'custom-legacy', 'scene_graph': graph, 'plan': [], 'reference_goal': [
            '(cooked target_1)', '(heated target_1)']}
        new = repair['repair_cases']([row])[0]
        self.assertEqual(new['scene_graph']['objects'][0]['states'], {'heated': False, 'can_be_heated': True})
        self.assertEqual(new['reference_goal'], ['(heated target_1)'])
        self.assertEqual(repair['repair_cases']([new]), [new])

    def test_repair_is_idempotent_and_preserves_task_intent(self):
        repair = runpy.run_path(str(PROJECT / 'scripts/repair_cooking.py'))
        rows = [json.loads(line) for line in (PROJECT / 'benchmarks/ahat_eval_set.jsonl').read_text().splitlines()]
        original = copy.deepcopy(rows)
        self.assertEqual(repair['repair_cases'](rows), rows)
        self.assertEqual(rows, original)
        cases = {r['id']: r for r in rows}
        for row in rows:
            for group, nodes in row['scene_graph'].items():
                if group == 'links' or not isinstance(nodes, list):
                    continue
                for node in nodes:
                    if not isinstance(node, dict):
                        continue
                    self.assertNotIn('cooked', node.get('states', {}))
                    self.assertNotIn('is_heated', node.get('states', {}))
                    if repair['semantic_type'](node) in ('egg_carton', 'flower_pot', 'toy_food', 'plant_pot'):
                        self.assertFalse(node.get('states', {}).get('is_food'))
                        self.assertFalse(node.get('states', {}).get('is_heating_container'))
            if any(sexpr(goal)[0] == 'heated' for goal in row.get('reference_goal', [])):
                self.assertIn(row['id'], repair['REPAIRED_IDS'])
        for case_id in repair['REPAIRED_IDS']:
            row = cases[case_id]
            self.assertTrue(native_goal(row['scene_graph'], row['plan'], row['reference_goal']))
            control = [text for text in row['plan'] if not sexpr(text)[0].startswith('heat_')]
            self.assertEqual(self.validate(row['scene_graph'], control)['status'], 'valid')
            self.assertFalse(native_goal(row['scene_graph'], control, row['reference_goal']))
            manager = SceneGraphManager(row['scene_graph'], str(DOMAIN))
            problem = full_problem(row['scene_graph'], DOMAIN)
            for i, text in enumerate(row['plan'], 1):
                parsed = sexpr(text)
                manager.apply_action(parsed[0], parsed[1:])
                self.assertEqual(final_state(problem, row['plan'][:i], DOMAIN),
                                 final_state(full_problem(manager.scene_graph, DOMAIN), [], DOMAIN))


if __name__ == '__main__':
    unittest.main()
