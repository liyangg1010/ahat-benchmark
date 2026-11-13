"""Real-VAL regressions for unique robot location and placement capacity."""
import unittest

from ahat_benchmark.domains import BASE_DOMAIN, LIQUID_DOMAIN, resolve_domain
from ahat_benchmark.pddl import full_problem, final_state, sexpr
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from helpers import VAL
from test_next_to import native_goal


def moving_scene(kind):
    name = kind + '_1'
    return {
        'rooms': [{'name': r, 'states': {}} for r in ('room_1', 'room_2')],
        'furnitures' if kind == 'furniture' else 'devices': [
            {'name': name, 'states': {'can_be_moved': True}}],
        'objects': [],
        'agent': [{'name': 'agent_0', 'location': name},
                  {'name': 'agent_1', 'location': 'room_1'}],
        'person': [], 'links': [['room_1', name, 'in']],
    }


def placement_scene(inside, limited=True, occupied=True):
    return {
        'rooms': [{'name': 'room_1', 'states': {}}],
        'furnitures': [{'name': 'support_1', 'states': {
            'can_only_place_one_object': limited,
            'can_be_opened': True, 'is_open': True}}],
        'objects': [{'name': n, 'states': {}} for n in ('held_1', 'reference_1')],
        'agent': [{'name': 'agent_0', 'location': 'support_1', 'holding': 'held_1'}],
        'person': [],
        'links': [['room_1', 'support_1', 'in']] + (
            [['support_1', 'reference_1', 'in' if inside else 'on']] if occupied else []),
    }


class ActionInvariantTests(unittest.TestCase):
    def check(self, graph, plan, domain, status='valid'):
        result = validate_plan(scene_graph=graph, plan=plan, domain_path=domain,
                               val_executable=VAL, timeout_seconds=10)
        self.assertEqual(result['status'], status, result)
        return result

    def test_move_leaves_exactly_one_location_in_val_and_scene_replay(self):
        for domain_id in (BASE_DOMAIN, LIQUID_DOMAIN):
            domain = resolve_domain(domain_id)
            for kind in ('furniture', 'device'):
                with self.subTest(domain=domain_id, kind=kind):
                    graph = moving_scene(kind)
                    obj = kind + '_1'
                    action = 'move_' + kind + '_to_room'
                    plan = [f'({action} agent_0 {obj} room_1 room_2)',
                            f'(navigate agent_0 room_2 {obj})',
                            f'({action} agent_0 {obj} room_2 room_1)']
                    problem = self.check(graph, plan, domain)['problem_pddl']
                    self.assertTrue(native_goal(graph, plan[:1], [
                        '(agent_at agent_0 room_2)', f'(not (agent_at agent_0 {obj}))',
                        '(agent_at agent_1 room_1)', f'({kind}_in_room {obj} room_2)',
                        f'(not ({kind}_in_room {obj} room_1))'], domain))
                    manager = SceneGraphManager(graph, str(domain))
                    for i, step in enumerate(plan):
                        a = sexpr(step)
                        manager.apply_action(a[0], a[1:])
                        state = final_state(problem, plan[:i + 1], domain)
                        for agent in ('agent_0', 'agent_1'):
                            self.assertEqual(len([f for f in state if f[:2] == ['agent_at', agent]]), 1)
                        self.assertEqual(state, final_state(full_problem(manager.scene_graph, domain), [], domain))
                    # Before the fix this could act from the obsolete object location.
                    exploit = plan[:1] + [f'(navigate agent_0 {obj} room_1)']
                    self.check(graph, exploit, domain, 'invalid')

    def test_ordinary_and_adjacent_placement_cannot_overfill(self):
        for domain_id in (BASE_DOMAIN, LIQUID_DOMAIN):
            domain = resolve_domain(domain_id)
            for inside in (False, True):
                with self.subTest(domain=domain_id, inside=inside):
                    graph = placement_scene(inside)
                    ordinary = 'place_in_receptacle' if inside else 'place_on_surface'
                    adjacent = 'place_next_to_inside' if inside else 'place_next_to_surface'
                    normal = f'({ordinary} agent_0 held_1 support_1)'
                    next_to = f'({adjacent} agent_0 held_1 reference_1 support_1)'
                    self.check(graph, [normal], domain, 'invalid')
                    self.check(graph, [next_to], domain, 'invalid')
                    # Empty limited support can accept its first item.
                    empty = placement_scene(inside, occupied=False)
                    self.check(empty, [normal], domain)
                    # Unlimited support can still accept adjacent items, with symmetric relation.
                    unlimited = placement_scene(inside, limited=False)
                    self.check(unlimited, [normal], domain)
                    self.check(unlimited, [next_to], domain)
                    self.assertTrue(native_goal(unlimited, [next_to], [
                        '(next_to held_1 reference_1 support_1)',
                        '(next_to reference_1 held_1 support_1)'], domain))
                    manager = SceneGraphManager(unlimited, str(domain))
                    a = sexpr(next_to)
                    manager.apply_action(a[0], a[1:])
                    self.assertEqual(final_state(full_problem(unlimited, domain), [next_to], domain),
                                     final_state(full_problem(manager.scene_graph, domain), [], domain))

    def test_capacity_becomes_available_after_removing_existing_item(self):
        for domain_id in (BASE_DOMAIN, LIQUID_DOMAIN):
            domain = resolve_domain(domain_id)
            for inside in (False, True):
                graph = placement_scene(inside)
                graph['furnitures'].append({'name': 'spare_1', 'states': {}})
                graph['links'].append(['room_1', 'spare_1', 'in'])
                pick = 'pick_from_receptacle' if inside else 'pick_from_surface'
                place = 'place_in_receptacle' if inside else 'place_on_surface'
                plan = ['(navigate agent_0 support_1 spare_1)',
                        '(place_on_surface agent_0 held_1 spare_1)',
                        '(navigate agent_0 spare_1 reference_1)',
                        f'({pick} agent_0 reference_1 support_1)',
                        '(navigate agent_0 reference_1 spare_1)',
                        '(place_on_surface agent_0 reference_1 spare_1)',
                        '(navigate agent_0 spare_1 held_1)',
                        '(pick_from_surface agent_0 held_1 spare_1)',
                        '(navigate agent_0 held_1 support_1)',
                        f'({place} agent_0 held_1 support_1)']
                self.check(graph, plan, domain)

    def test_surface_and_interior_occupancy_use_their_own_relation(self):
        # Preserve the existing surface-capacity interpretation: objects inside
        # a cabinet do not occupy its top, nor do top objects occupy its interior.
        for domain_id in (BASE_DOMAIN, LIQUID_DOMAIN):
            domain = resolve_domain(domain_id)
            for inside in (False, True):
                graph = placement_scene(inside)
                graph['links'][-1][-1] = 'on' if inside else 'in'
                action = 'place_in_receptacle' if inside else 'place_on_surface'
                self.check(graph, [f'({action} agent_0 held_1 support_1)'], domain)


if __name__ == '__main__':
    unittest.main()
