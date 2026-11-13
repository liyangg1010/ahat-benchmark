"""Real-VAL and scene round-trip checks for inventories, lighting and room links."""
import copy
import json
from pathlib import Path
import runpy
import unittest

from ahat_benchmark.domains import BASE_DOMAIN, LIQUID_DOMAIN, resolve_domain
from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.scene import held_objects, normalize_links
from ahat_benchmark.judge.scene_summary import summarize_scene
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from helpers import PROJECT, VAL, scene
from test_next_to import native_goal


class SceneLightingTests(unittest.TestCase):
    def check(self, graph, plan, domain, status='valid'):
        result = validate_plan(scene_graph=graph, plan=plan, domain_path=domain,
                               val_executable=VAL, timeout_seconds=10)
        self.assertEqual(result['status'], status, result)
        return result

    def test_multiple_deliveries_preserve_inventory_at_every_step(self):
        graph = scene()
        graph['objects'].append({'name': 'book_1', 'states': {}})
        graph['links'].append(['table_1', 'lid_1', 'on'])
        graph['person'] = [{'name': 'person_0', 'location': 'room_1', 'p_holding': 'book_1'}]
        plan = ['(pick_from_surface agent_0 cup_1 table_1)',
                '(navigate agent_0 cup_1 person_0)', '(hand_over_to_person agent_0 person_0 cup_1)',
                '(navigate agent_0 person_0 lid_1)', '(pick_from_surface agent_0 lid_1 table_1)',
                '(navigate agent_0 lid_1 person_0)', '(hand_over_to_person agent_0 person_0 lid_1)']
        original = copy.deepcopy(graph)
        for name in (BASE_DOMAIN, LIQUID_DOMAIN):
            domain = resolve_domain(name)
            problem = self.check(graph, plan, domain)['problem_pddl']
            self.assertTrue(native_goal(graph, plan, [f'(p_holding person_0 {x})'
                                                    for x in ('book_1', 'cup_1', 'lid_1')], domain))
            manager = SceneGraphManager(graph, str(domain))
            for i, step in enumerate(plan):
                action = sexpr(step)
                manager.apply_action(action[0], action[1:])
                self.assertEqual(final_state(problem, plan[:i + 1], domain),
                                 final_state(full_problem(manager.scene_graph, domain), [], domain))
            inventory = manager.scene_graph['person'][0]['p_holding']
            self.assertEqual(inventory, ['book_1', 'cup_1', 'lid_1'])
            summary = summarize_scene(manager.scene_graph)
            self.assertIn("'person_0': ['book_1', 'cup_1', 'lid_1']", summary)
            manager.apply_predicates('(p_holding person_0 cup_1)')
            self.assertEqual(manager.scene_graph['person'][0]['p_holding'], inventory)
            manager.apply_predicates('(not (p_holding person_0 cup_1))')
            self.assertEqual(manager.scene_graph['person'][0]['p_holding'], ['book_1', 'lid_1'])
        self.assertEqual(graph, original)

    def test_initial_inventory_lists_validate_all_items_and_adjacency(self):
        domain = resolve_domain(BASE_DOMAIN)
        graph = scene()
        graph['person'] = [{'name': 'person_0', 'p_holding': ['cup_1', 'lid_1', 'cup_1']}]
        graph['links'] = [['room_1', 'table_1', 'in']]
        problem = full_problem(graph, domain)
        self.assertEqual(problem.count('(p_holding person_0 cup_1)'), 1)
        self.assertIn('(p_holding person_0 lid_1)', problem)
        for value in (1, ['cup_1', None], {'cup_1': True}):
            with self.assertRaises(ValueError):
                held_objects(value)
        graph['person'][0]['p_holding'].append('unknown_1')
        with self.assertRaisesRegex(ValueError, 'undeclared'):
            full_problem(graph, domain)
        graph['person'][0]['p_holding'] = ['cup_1']
        graph['links'] += [['table_1', 'cup_1', 'on'], ['table_1', 'lid_1', 'on'],
                           {'relation': 'next_to', 'obj1': 'cup_1', 'obj2': 'lid_1', 'location': 'table_1'}]
        with self.assertRaises(ValueError):
            normalize_links(graph)

    def test_lighting_works_for_objects_furniture_and_devices_without_power(self):
        for name in (BASE_DOMAIN, LIQUID_DOMAIN):
            domain = resolve_domain(name)
            for category in ('objects', 'furnitures', 'devices'):
                graph = scene()
                graph.setdefault(category, []).append({'name': 'lamp_1', 'states': {'can_be_lighted': True}})
                graph['agent'][0]['location'] = 'lamp_1'
                relation = 'on' if category == 'objects' else 'in'
                graph['links'].append(['table_1' if category == 'objects' else 'room_1', 'lamp_1', relation])
                on = ['(light_on agent_0 lamp_1)']
                self.check(graph, on, domain)
                self.assertTrue(native_goal(graph, on, ['(is_light_on lamp_1)', '(not (is_powered_on lamp_1))'], domain))
                self.check(graph, ['(power_on agent_0 lamp_1)'], domain, 'invalid')
                plan = on + ['(light_off agent_0 lamp_1)']
                self.assertTrue(native_goal(graph, plan, ['(not (is_light_on lamp_1))'], domain))
                manager = SceneGraphManager(graph, str(domain))
                for step in plan:
                    action = sexpr(step); manager.apply_action(action[0], action[1:])
                self.assertEqual(final_state(full_problem(graph, domain), plan, domain),
                                 final_state(full_problem(manager.scene_graph, domain), [], domain))
            graph = scene()
            graph['agent'][0]['location'] = 'table_1'
            self.check(graph, ['(light_on agent_0 table_1)'], domain, 'invalid')
            graph['furnitures'][0]['states']['is_powerable'] = True
            self.check(graph, ['(power_on agent_0 table_1)', '(power_off agent_0 table_1)'], domain)

    def test_robot_room_links_follow_pick_navigation_and_moving_support(self):
        domain = resolve_domain(BASE_DOMAIN)
        graph = scene()
        graph['rooms'].append({'name': 'room_2', 'states': {}})
        graph['furnitures'].append({'name': 'table_2', 'states': {'can_be_moved': True}})
        graph['links'] += [['room_2', 'table_2', 'in'], ['room_2', 'agent_0', 'in']]
        manager = SceneGraphManager(graph, str(domain))
        def room_of(name):
            return [l['to'] for l in manager.scene_graph['links'] if l['relation'] == 'in' and l['from'] == name]
        self.assertEqual(room_of('agent_0'), ['room_1'])
        plan = ['(pick_from_surface agent_0 cup_1 table_1)',
                '(navigate agent_0 cup_1 table_2)', '(place_on_surface agent_0 cup_1 table_2)']
        problem = self.check(graph, plan, domain)['problem_pddl']
        for i, step in enumerate(plan):
            a = sexpr(step);manager.apply_action(a[0], a[1:])
            self.assertEqual(room_of('agent_0'), ['room_1' if i == 0 else 'room_2'])
            facts = final_state(full_problem(manager.scene_graph, domain), [], domain)
            self.assertEqual(facts, final_state(problem, plan[:i + 1], domain))
            self.assertEqual(sum(f[0] == 'agent_at' for f in facts), 1)
        # A second robot tracks a moved furniture anchor without acquiring a second agent_at.
        graph['agent'] = [{'name': 'agent_0', 'location': 'table_2'}, {'name': 'agent_1', 'location': 'table_2'}]
        manager = SceneGraphManager(graph, str(domain))
        move = ['(move_furniture_to_room agent_0 table_2 room_2 room_1)']
        self.check(graph, move, domain)
        manager.apply_action('move_furniture_to_room', ['agent_0', 'table_2', 'room_2', 'room_1'])
        self.assertEqual(room_of('agent_0'), ['room_1'])
        self.assertEqual(room_of('agent_1'), ['room_1'])

    def test_robot_can_navigate_to_person_with_room_link_only(self):
        graph = scene()
        graph['rooms'].append({'name': 'room_2', 'states': {}})
        graph['person'] = [{'name': 'person_0'}]
        graph['links'].append(['room_2', 'person_0', 'in'])
        manager = SceneGraphManager(graph, str(resolve_domain(BASE_DOMAIN)))
        manager.apply_action('navigate', ['agent_0', 'cup_1', 'person_0'])
        self.assertIn({'relation': 'in', 'from': 'agent_0', 'to': 'room_2'}, manager.scene_graph['links'])

    def test_migration_is_idempotent_and_preserves_nonlighting_appliances(self):
        repair = runpy.run_path(str(PROJECT / 'scripts/repair_scene_lighting.py'))['repair']
        graph = scene()
        graph['objects'].append({'name': 'lamp_0', 'states': {'can_be_lighted': True, 'is_powerable': True, 'is_powered_on': True}})
        graph['furnitures'][0]['states'] = {'is_powerable': True, 'is_powered_on': True}
        row = {'id': 'fixture', 'scene_graph': graph, 'plan': ['(power_off agent_0 lamp_0)']}
        repaired, _ = repair(row)
        self.assertEqual(repaired['plan'], ['(light_off agent_0 lamp_0)'])
        self.assertEqual(repaired['scene_graph']['objects'][-1]['states'], {'can_be_lighted': True, 'is_light_on': True})
        self.assertEqual(repaired['scene_graph']['furnitures'][0], row['scene_graph']['furnitures'][0])
        self.assertEqual(repair(repaired), (repaired, {}))
