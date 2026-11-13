"""Regression checks for the approved dataset migration and its safety guards."""
import copy
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = runpy.run_path(str(ROOT / 'scripts/prune_easy_cases.py'))


class EasyPruningTests(unittest.TestCase):
    def setUp(self):
        self.inventory = json.loads((ROOT / SCRIPT['INVENTORY']).read_bytes())
        self.active = [json.loads(line) for line in (ROOT / 'benchmarks/ahat_eval_set.jsonl').read_bytes().splitlines()]
        self.archived = [json.loads(line) for line in (ROOT / SCRIPT['ARCHIVE']).read_bytes().splitlines()]

    def test_archive_exactly_matches_approved_records_and_selection_is_stable(self):
        self.assertEqual({r['id'] for r in self.archived}, set(self.inventory['remove_ids']))
        self.assertEqual(len(self.archived), 13)
        self.assertFalse({r['id'] for r in self.active} & {r['id'] for r in self.archived})
        # Interleave archived records to exercise preservation of survivor order.
        before = self.active[:20] + self.archived + self.active[20:]
        self.assertEqual(SCRIPT['select_rows'](before, self.inventory), self.active)
        self.assertEqual(SCRIPT['migrate'](ROOT), {
            'removed_cases': 0, 'case_count': 274,
            'split_counts': {'easy': 117, 'medium': 65, 'open': 92},
        })

    def test_reject_partial_migration_duplicate_ids_and_record_drift(self):
        before = self.active + self.archived
        drift = copy.deepcopy(before)
        drift[-1]['plan'] = []
        retained_id = self.inventory['groups'][0]['records'][0]['id']
        variants = [self.active + self.archived[:1], before + before[:1], drift,
                    [r for r in before if r['id'] != retained_id]]
        for variant in variants:
            with self.subTest(size=len(variant)), self.assertRaises(ValueError):
                SCRIPT['select_rows'](variant, self.inventory)


if __name__ == '__main__':
    unittest.main()
