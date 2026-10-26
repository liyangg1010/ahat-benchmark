import json
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ahat_benchmark.val.validator import normalize_action, validate_plan
from helpers import DOMAIN, VAL, PLAN, scene


class ValTests(unittest.TestCase):
    def validate(self, graph, plan):
        return validate_plan(scene_graph=graph, plan=plan, domain_path=DOMAIN, val_executable=VAL, timeout_seconds=10)

    def test_supported_action_formats(self):
        action = "(navigate agent_0 room_1 table_1)"
        self.assertEqual(normalize_action(action), action)
        self.assertEqual(normalize_action("navigate(agent_0, room_1, table_1)"), action)

    def test_reject_empty_unbalanced_and_nested_actions(self):
        for action in (" ", "(navigate agent_0", "(one) (two)", "(navigate (agent_0) room_1)"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                normalize_action(action)

    def test_unmentioned_blocker_is_visible_to_negative_existential_precondition(self):
        allowed = self.validate(scene(), PLAN)
        blocked = self.validate(scene(blocked=True), PLAN)
        self.assertEqual(allowed["status"], "valid")
        self.assertEqual(blocked["status"], "invalid")
        self.assertIn("(item_on_surface lid_1 cup_1)", blocked["problem_pddl"])

    def test_output_without_verdict_is_infrastructure_error(self):
        process = SimpleNamespace(returncode=1, stdout="", stderr="failed to parse domain")
        with patch("ahat_benchmark.val.validator.subprocess.run", return_value=process):
            result = self.validate(scene(), PLAN)
        self.assertEqual(result["status"], "val_error")

    def test_floor_cleaning_supports_objects_and_rooms_with_existing_constraints(self):
        for target, category in [('rug_1', 'objects'), ('room_1', 'rooms')]:
            for variant in ('valid', 'wrong_tool', 'missing_requirement', 'already_clean'):
                with self.subTest(target=target, variant=variant):
                    graph = {
                        'rooms': [{'name': 'room_1', 'states': {}}],
                        'objects': [{'name': 'vacuum_1', 'states': {'is_floor_cleaner': variant != 'wrong_tool'}}],
                        'agent': [{'name': 'agent_0', 'location': target, 'holding': 'vacuum_1'}],
                        'furnitures': [], 'person': [], 'links': [],
                    }
                    target_node = {
                        'name': target,
                        'states': {'require_floor_cleaner': variant != 'missing_requirement',
                                   'is_clean': variant == 'already_clean'},
                    }
                    if category == 'rooms':
                        graph['rooms'][0] = target_node
                    else:
                        graph['objects'].append(target_node)
                    result = self.validate(graph, [f'(clean_room_floor agent_0 vacuum_1 {target})'])
                    self.assertEqual(result['status'], 'valid' if variant == 'valid' else 'invalid')

    def test_wrong_arity_and_unknown_actions_are_rejected_before_native_val(self):
        plans = [
            (["(navigate agent_0 room_1)"], "Wrong action argument count"),
            (["(navigate agent_0 room_1 cup_1 table_1)"], "Wrong action argument count"),
            (["(unknown_action agent_0 cup_1)"], "Unknown domain action"),
        ]
        for plan, reason in plans:
            with self.subTest(plan=plan), patch(
                "ahat_benchmark.val.validator.subprocess.run", side_effect=AssertionError("must not invoke native VAL")
            ):
                result = self.validate(scene(), plan)
            self.assertEqual(result["status"], "invalid")
            self.assertFalse(result["validate_result"])
            self.assertEqual(result["fail_reason"], reason)
            self.assertEqual(result["invalid_action"], plan[0])

    def test_timeout_bytes_can_be_checkpointed_as_json(self):
        failure = subprocess.TimeoutExpired("Validate", 10, output=b"partial", stderr=b"error")
        with patch("ahat_benchmark.val.validator.subprocess.run", side_effect=failure):
            result = self.validate(scene(), PLAN)
        self.assertEqual(result["status"], "val_timeout")
        self.assertEqual(result["stdout"], "partial")
        json.dumps(result)
