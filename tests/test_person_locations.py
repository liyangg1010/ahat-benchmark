"""Person positions survive scene conversion without inventing extra locations."""
import copy
import unittest

from ahat_benchmark.domains import BASE_DOMAIN, LIQUID_DOMAIN, resolve_domain
from ahat_benchmark.judge.scene_summary import summarize_scene
from ahat_benchmark.pddl import final_state, full_problem, sexpr
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from helpers import VAL, scene
from test_next_to import native_goal


class PersonLocationTests(unittest.TestCase):
    def test_link_only_location_survives_delivery_and_replay(self):
        for domain_id in (BASE_DOMAIN, LIQUID_DOMAIN):
            for link in (['room_1', 'person_0', 'in'],
                         {'relation': 'in', 'from': 'person_0', 'to': 'room_1'}):
                with self.subTest(domain=domain_id, link=link):
                    graph = scene()
                    graph['person'] = [{'name': 'person_0'}]
                    graph['links'].append(link)
                    original = copy.deepcopy(graph)
                    domain = resolve_domain(domain_id)
                    plan = ['(pick_from_surface agent_0 cup_1 table_1)',
                            '(navigate agent_0 cup_1 person_0)',
                            '(hand_over_to_person agent_0 person_0 cup_1)']
                    checked = validate_plan(scene_graph=graph, plan=plan, domain_path=domain,
                                            val_executable=VAL, timeout_seconds=10)
                    self.assertEqual(checked['status'], 'valid', checked)
                    self.assertTrue(native_goal(graph, plan, ['(person_at person_0 room_1)',
                                                            '(p_holding person_0 cup_1)'], domain))
                    manager = SceneGraphManager(graph, str(domain))
                    for i, step in enumerate(plan):
                        action = sexpr(step)
                        manager.apply_action(action[0], action[1:])
                        self.assertEqual(final_state(checked['problem_pddl'], plan[:i + 1], domain),
                                         final_state(full_problem(manager.scene_graph, domain), [], domain))
                    self.assertIn("'person_locations': {'person_0': 'room_1'}", summarize_scene(graph))
                    self.assertEqual(graph, original)

    def test_precise_location_and_room_projection_produce_one_fact(self):
        domain = resolve_domain(BASE_DOMAIN)
        for explicit in (None, 'table_1'):
            graph = scene()
            graph['person'] = [{'name': 'person_0', 'location': explicit}]
            graph['links'] += [['room_1', 'person_0', 'in'], ['table_1', 'person_0', 'on'],
                               {'relation': 'on', 'from': 'person_0', 'to': 'table_1'}]
            facts = final_state(full_problem(graph, domain), [], domain)
            self.assertEqual([f for f in facts if f[0] == 'person_at'],
                             [['person_at', 'person_0', 'table_1']])
        # Explicit precise position may also be paired with only its room edge.
        graph['links'] = [l for l in graph['links'] if l != ['table_1', 'person_0', 'on']
                          and not isinstance(l, dict)]
        self.assertIn('(person_at person_0 table_1)', full_problem(graph, domain))

    def test_ambiguous_conflicting_and_nonphysical_locations_are_rejected(self):
        for location, targets in [('room_1', ['room_2']), (None, ['room_1', 'room_2']),
                                  (None, ['table_1', 'cup_1']), ('table_1', ['room_2']),
                                  ('missing_1', []), (None, ['missing_1']),
                                  (None, ['agent_0']), ('person_0', []), ('', [])]:
            with self.subTest(location=location, targets=targets):
                graph = scene()
                graph['rooms'].append({'name': 'room_2', 'states': {}})
                graph['person'] = [{'name': 'person_0', 'location': location}]
                graph['links'] += [[target, 'person_0', 'in'] for target in targets]
                with self.assertRaisesRegex(ValueError, 'person person_0'):
                    full_problem(graph, resolve_domain(BASE_DOMAIN))
                with self.assertRaisesRegex(ValueError, 'person person_0'):
                    summarize_scene(graph)

    def test_absent_evidence_stays_unspecified_and_explicit_only_is_preserved(self):
        graph = scene()
        graph['person'] = [{'name': 'person_0'}, {'name': 'person_1', 'location': 'room_1'}]
        problem = full_problem(graph, resolve_domain(BASE_DOMAIN))
        self.assertNotIn('(person_at person_0', problem)
        self.assertEqual(problem.count('(person_at person_1 room_1)'), 1)
