import copy
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

from helpers import DOMAIN, PROJECT


class CookingGoalAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(sys, 'path', [str(PROJECT / 'scripts'), *sys.path]):
            cls.audit_module = runpy.run_path(str(PROJECT / 'scripts/audit_cooking_goals.py'))
        cls.rows = [json.loads(line) for line in
                    (PROJECT / 'benchmarks/ahat_eval_set.jsonl').read_text().splitlines()]

    def test_confirmed_witnesses_and_partial_warm_brunch_under_unified_processing(self):
        result = self.audit_module['audit'](self.rows)
        self.assertEqual(result['confirmed_count'], 2)
        self.assertEqual(result['historical_deferred_meal_candidates'], 9)
        self.assertEqual(result['current_repaired_meal_references'], 9)
        self.assertEqual(result['current_deferred_reference_repairs'], 0)
        self.assertEqual(result['approved_pruned_inventory_count'], 33)
        self.assertEqual(result['group_counts']['food_processing_or_meal_service'], 11)
        self.assertTrue(result['warm_brunch_check']['reference_plan_reaches_goal'])
        self.assertTrue(result['warm_brunch_check']['no_processing_control_misses_goal'])
        self.assertEqual(sum(r['scene_replay_steps'] for r in result['confirmed_references']), 32)

    def test_changed_adopted_reference_cannot_be_reported_as_repaired(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r['id'] == 'dec162ab-e453-419f-971a-2e32987350f2')
        row['plan'] = row['plan'][:-1]
        with self.assertRaisesRegex(ValueError, 'Adopted meal reference changed'):
            self.audit_module['audit'](rows)

    def test_weaker_breakfast_goal_is_rejected_by_no_processing_control(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r['id'] == self.audit_module['BREAKFAST'])
        row['reference_goal'].remove('(heated breakfast_eggs_1)')
        with self.assertRaisesRegex(ValueError, 'omit_processing unexpectedly meets goal'):
            self.audit_module['audit'](rows)

    def test_warm_brunch_without_processing_result_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r['id'] == self.audit_module['WARM_BRUNCH'])
        row['reference_goal'].remove('(heated breakfast_eggs_1)')
        with self.assertRaisesRegex(ValueError, 'Warm-brunch goal omits heated eggs'):
            self.audit_module['audit'](rows)

    def test_new_heating_producer_requires_repeating_semantic_review(self):
        domain = DOMAIN.read_text().replace(':effect (is_open ?r)',
                                           ':effect (and (is_open ?r) (heated ?r))', 1)
        self.assertNotEqual(domain, DOMAIN.read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'domain.pddl'
            path.write_text(domain)
            with self.assertRaisesRegex(ValueError, 'Heating producer set changed'):
                self.audit_module['domain_premises'](path)


if __name__ == '__main__':
    unittest.main()
