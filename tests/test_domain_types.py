"""The built-in root and small-item subtype stay distinct across all consumers."""
import tempfile
import unittest
from pathlib import Path

from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser

from ahat_benchmark.domains import BASE_DOMAIN, LIQUID_DOMAIN, resolve_domain
from ahat_benchmark.pddl import final_state, full_problem
from ahat_benchmark.pddl_effects import compatible_type, typed_symbols
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import PDDLDomainParser, SceneGraphManager
from ahat_benchmark.vendor.problem_generator import PDDLProblemGenerator
from helpers import VAL, scene
from test_next_to import native_goal


class DomainTypeTests(unittest.TestCase):
    def test_domains_and_exported_problems_parse_independently(self):
        for domain_id in (BASE_DOMAIN, LIQUID_DOMAIN):
            with self.subTest(domain=domain_id):
                domain = resolve_domain(domain_id)
                DomainParser()(domain.read_text())
                graph = scene()
                manager = SceneGraphManager(graph, str(domain))
                self.assertEqual(manager.get_object_pddl_type('cup_1'), 'small_object')
                problem = full_problem(graph, domain)
                ProblemParser()(problem)
                self.assertIn('cup_1 - small_object', problem)
                legacy = PDDLProblemGenerator(manager).generate_problem_from_actions(
                    ['(pick_from_surface agent_0 cup_1 table_1)'])
                self.assertIn(' - small_object', legacy)
                ProblemParser()(legacy)

    def test_type_tree_has_a_single_builtin_root_and_no_cycles(self):
        for domain_id in (BASE_DOMAIN, LIQUID_DOMAIN):
            parents = PDDLDomainParser(resolve_domain(domain_id).read_text()).types
            self.assertNotIn('object', parents)
            self.assertEqual(parents['item'], 'object')
            self.assertEqual(parents['small_object'], 'physobj')
            self.assertEqual(parents['container'], 'small_object')
            for kind in parents:
                visited = set()
                current = kind
                while current != 'object':
                    self.assertNotIn(current, visited)
                    visited.add(current)
                    current = parents[current]
                self.assertTrue(compatible_type(kind, 'object', parents))
            self.assertFalse(compatible_type('furniture', 'small_object', parents))
            self.assertFalse(compatible_type('agent', 'physobj', parents))

    def test_small_item_action_accepts_container_but_rejects_furniture(self):
        for domain_id in (BASE_DOMAIN, LIQUID_DOMAIN):
            domain = resolve_domain(domain_id)
            graph = scene()
            graph['objects'][0]['states']['is_cleaning_tool'] = True
            graph['containers'] = [{'name': 'box_1', 'states': {}}]
            graph['agent'][0].update(location='box_1', holding='cup_1')
            graph['links'] = [['room_1', 'table_1', 'in'], ['table_1', 'box_1', 'on']]
            plan = ['(clean_item agent_0 cup_1 box_1)']
            self.assertTrue(native_goal(graph, plan, ['(is_clean box_1)'], domain))
            graph['agent'][0]['location'] = 'table_1'
            result = validate_plan(scene_graph=graph, plan=['(clean_item agent_0 cup_1 table_1)'],
                                   domain_path=domain, val_executable=VAL, timeout_seconds=10)
            self.assertEqual(result['status'], 'invalid')
            self.assertEqual(result['argument_error']['expected_type'], 'small_object')
            self.assertEqual(result['argument_error']['actual_type'], 'furniture')

    def test_root_quantification_ranges_over_all_subtypes_and_defaults_stay_root(self):
        self.assertEqual(typed_symbols(['?x']), {'?x': 'object'})
        graph = scene()
        graph['person'] = [{'name': 'person_0', 'location': 'room_1'}]
        graph['devices'] = [{'name': 'device_1', 'states': {}}]
        graph['containers'] = [{'name': 'box_1', 'states': {}}]
        names = {'agent_0', 'person_0', 'room_1', 'table_1', 'cup_1', 'lid_1', 'device_1', 'box_1'}
        for domain_id in (BASE_DOMAIN, LIQUID_DOMAIN):
            text = resolve_domain(domain_id).read_text().replace(
                '(:predicates', '(:predicates (marked ?x - object)', 1)
            text = text.rstrip()[:-1] + '''
  (:action mark_all :parameters () :precondition (and)
    :effect (forall (?x - object) (marked ?x)))
)'''
            with tempfile.TemporaryDirectory() as directory:
                domain = Path(directory) / 'domain.pddl'
                domain.write_text(text)
                goals = [f'(marked {name})' for name in sorted(names)]
                self.assertTrue(native_goal(graph, ['(mark_all)'], goals, domain))
                problem = full_problem(graph, domain)
                state = final_state(problem, ['(mark_all)'], domain)
                self.assertEqual({f[1] for f in state if f[0] == 'marked'}, names)
                manager = SceneGraphManager(graph, str(domain))
                manager.apply_action('mark_all', [])
                self.assertEqual(final_state(full_problem(manager.scene_graph, domain), [], domain), state)
