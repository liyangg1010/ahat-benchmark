import contextlib
import copy
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ahat_benchmark import cli
from ahat_benchmark.config import load_config
from ahat_benchmark.judge.evaluator import RubricEvaluator
from ahat_benchmark.judge.prompts import PROMPTS
from ahat_benchmark.pipeline.judge_stage import run_judge_stage
from ahat_benchmark.pipeline.summarize import summarize
from ahat_benchmark.pipeline.val_stage import run_val_stage
from ahat_benchmark.schemas import EvalCase
from ahat_benchmark.provenance import canonical, digest
from helpers import DOMAIN, VAL, PLAN, FakeClient, scene


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.inference = self.directory / 'inference.json'
        self.rows = [{'id': 'valid', 'plan': PLAN}, {'id': 'empty', 'plan': []}]
        self.inference.write_text(json.dumps(self.rows))
        self.cases = [EvalCase(row['id'], 'Pick up the cup.', scene()) for row in self.rows]
        self.val_path = self.directory / 'val_results.json'
        self.judge_path = self.directory / 'judge_results.json'
        self.summary_path = self.directory / 'final_results.json'
        for module in ['val_stage', 'judge_stage', 'summarize']:
            patcher = patch('ahat_benchmark.pipeline.' + module + '.load_eval_set', return_value=self.cases)
            patcher.start()
            self.addCleanup(patcher.stop)

    def val(self, **kwargs):
        return run_val_stage(
            dataset='fixture', inference_path=self.inference, output_path=self.val_path,
            domain_path=DOMAIN, val_executable=VAL, timeout_seconds=10, workers=2, **kwargs,
        )

    def judge(self, client, model='test-judge', **kwargs):
        evaluator = RubricEvaluator(client=client, model=model, domain_path=DOMAIN, max_attempts=1, dimension_workers=1)
        return run_judge_stage(
            dataset='fixture', inference_path=self.inference, val_results_path=self.val_path,
            output_path=self.judge_path, evaluator=evaluator, workers=2, **kwargs,
        )

    def summary(self):
        return summarize(
            dataset='fixture', inference_path=self.inference, val_results_path=self.val_path,
            judge_results_path=self.judge_path, output_path=self.summary_path, domain_path=DOMAIN,
        )

    def test_end_to_end_denominator_and_unchanged_resume(self):
        first = self.val()
        client = FakeClient()
        self.judge(client)
        self.assertEqual(self.summary()['statistics']['final_score'], .5)
        self.assertTrue(self.summary()['statistics']['publishable'])
        with patch('ahat_benchmark.pipeline.val_stage.validate_plan', side_effect=AssertionError('unexpected VAL call')):
            self.assertEqual(self.val()['meta']['signature'], first['meta']['signature'])
        self.judge(client)
        self.assertEqual(len(client.calls), 4)

    def rewrite_val(self, change, rehash=True):
        data = json.loads(self.val_path.read_text())
        change(data['cases'][0])
        if rehash:
            data['meta']['cases_sha256'] = digest(canonical(data['cases']).encode())
        self.val_path.write_text(json.dumps(data))

    def test_cached_plan_mismatch_is_rejected_before_resume_or_judge(self):
        self.val()
        self.judge(FakeClient())
        self.rewrite_val(lambda row: row.update(plan=['(place_on_surface agent_0 cup_1 table_1)']))
        before = self.val_path.read_bytes(), self.judge_path.read_bytes()
        client = FakeClient()
        for stage in (self.val, lambda: self.judge(client), self.summary):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    stage()
        self.assertEqual(client.calls, [])
        self.assertEqual(before, (self.val_path.read_bytes(), self.judge_path.read_bytes()))

    def test_cached_equivalent_plan_format_is_accepted(self):
        self.val()
        self.rewrite_val(lambda row: row.update(plan=['PICK_FROM_SURFACE(agent_0, cup_1, table_1)']))
        self.val()
        client = FakeClient()
        self.judge(client)
        self.assertEqual(len(client.calls), 4)
        self.assertEqual(self.summary()['statistics']['final_score'], .5)

    def test_result_corruption_and_upstream_case_changes_invalidate_judge_resume(self):
        self.val()
        self.judge(FakeClient())
        self.rewrite_val(lambda row: row.update(duration_seconds=999), rehash=False)
        with self.assertRaisesRegex(ValueError, 'content.*corrupt'):
            self.judge(FakeClient())
        self.rewrite_val(lambda row: None)
        with self.assertRaisesRegex(ValueError, 'inputs or protocol changed'):
            self.judge(FakeClient())
        with self.assertRaises(ValueError):
            self.summary()

    def test_rehashed_problem_must_still_match_dataset_scene(self):
        self.val()
        def change(row):
            row['problem_pddl'] = row['problem_pddl'].replace('(:init ', '(:init (is_clean cup_1) ')
            row['problem_sha256'] = digest(row['problem_pddl'].encode())
        self.rewrite_val(change)
        client = FakeClient()
        with self.assertRaisesRegex(ValueError, 'initial state does not match scene'):
            self.judge(client)
        self.assertEqual(client.calls, [])

    def test_malformed_plan_cache_remains_a_zero_scoring_submission(self):
        self.inference.write_text(json.dumps([{'id': 'valid', 'plan': ['unparseable']}, self.rows[1]]))
        self.val()
        self.val()
        client = FakeClient()
        self.judge(client)
        self.assertEqual(client.calls, [])
        self.assertEqual(self.summary()['statistics']['final_score'], 0)

    def test_changed_inference_or_scene_rejects_old_val_checkpoint(self):
        self.val()
        self.inference.write_text(json.dumps([{'id': 'valid', 'plan': []}, self.rows[1]]))
        with self.assertRaisesRegex(ValueError, 'inputs or protocol changed'):
            self.val()
        self.inference.write_text(json.dumps(self.rows))
        self.cases[0].scene_graph['rooms'][0]['states']['is_clean'] = True
        with self.assertRaisesRegex(ValueError, 'inputs or protocol changed'):
            self.val()

    def test_illegal_arguments_score_zero_without_system_errors_or_judge_calls(self):
        self.inference.write_text(json.dumps([
            {'id': 'valid', 'plan': ['(navigate agent_0 cup_1 ghost_1)']},
            {'id': 'empty', 'plan': ['(navigate agent_0 cup_1 agent_0)']},
        ]))
        with patch('ahat_benchmark.val.validator.subprocess.run') as native:
            checked = self.val()
        self.assertEqual(native.call_count, 0)
        self.assertTrue(all(row['status'] == 'invalid' for row in checked['cases']))
        client = FakeClient()
        self.judge(client)
        self.assertEqual(client.calls, [])
        statistics = self.summary()['statistics']
        self.assertEqual(statistics['val_invalid'], 2)
        self.assertEqual(statistics['system_errors'], 0)
        self.assertTrue(statistics['publishable'])
        self.assertEqual(statistics['final_score'], 0)

    def test_changed_model_or_endpoint_rejects_old_judge_checkpoint(self):
        self.val()
        self.judge(FakeClient())
        with self.assertRaisesRegex(ValueError, 'inputs or protocol changed'):
            self.judge(FakeClient(), model='other-judge')
        with self.assertRaisesRegex(ValueError, 'inputs or protocol changed'):
            self.judge(FakeClient(base_url='https://other.example/v1'))

    def test_changed_d3_policy_rejects_old_judge_checkpoint_before_api_calls(self):
        self.val()
        self.judge(FakeClient())
        original_checkpoint = self.judge_path.read_bytes()
        client = FakeClient()
        with patch.dict(PROMPTS, {'D3': PROMPTS['D3'] + '\nChanged meal policy.'}):
            with self.assertRaisesRegex(ValueError, 'inputs or protocol changed'):
                self.judge(client)
        self.assertEqual(client.calls, [])
        self.assertEqual(self.judge_path.read_bytes(), original_checkpoint)

    def test_failed_dimension_checkpoints_and_resumes_without_zero_score(self):
        self.val()
        def respond(key, count):
            if key == 'D4' and count == 2:
                checkpoint = json.loads(self.judge_path.read_text())
                record = next(case for case in checkpoint['cases'] if case['id'] == 'valid')
                self.assertTrue(all(record['dimensions'][dim]['status'] == 'success' for dim in ['D1', 'D2', 'D3']))
            return {'score': .61 if key == 'D4' and count == 1 else 1, 'rationale': 'checked', 'critical_failure': False}
        client = FakeClient(respond)
        self.judge(client)
        failed = self.summary()['statistics']
        self.assertFalse(failed['publishable'])
        self.assertIsNone(failed['final_score'])
        self.assertEqual(failed['system_errors'], 1)
        self.judge(client)
        self.assertEqual(len(client.calls), 5)
        self.assertEqual(self.summary()['statistics']['final_score'], .5)

    def test_legacy_unversioned_results_are_rejected(self):
        self.val_path.write_text(json.dumps({'meta': {'dataset': 'fixture'}, 'cases': []}))
        with self.assertRaisesRegex(ValueError, 'unversioned'):
            self.judge(FakeClient())

    def test_summary_rejects_results_for_changed_inference(self):
        self.val()
        self.judge(FakeClient())
        self.inference.write_text(json.dumps([{'id': 'valid', 'plan': []}, self.rows[1]]))
        with self.assertRaisesRegex(ValueError, 'inputs or protocol changed'):
            self.summary()

    def test_explicit_no_resume_recomputes_changed_inputs(self):
        self.val()
        self.judge(FakeClient())
        self.inference.write_text(json.dumps([{'id': 'valid', 'plan': []}, self.rows[1]]))
        self.val(resume=False)
        self.judge(FakeClient(), resume=False)
        self.assertEqual(self.summary()['statistics']['final_score'], 0)

    def test_allowed_missing_inference_is_zero_in_all_stages(self):
        self.inference.write_text(json.dumps(self.rows[:1]))
        self.val(allow_missing=True)
        self.judge(FakeClient())
        self.assertEqual(self.summary()['statistics']['final_score'], .5)

    def test_cli_honors_scoring_and_explicit_endpoint_with_env_credential(self):
        self.val()
        config = copy.deepcopy(load_config())
        config['judge']['base_url'] = 'https://judge.example/v1'
        config['scoring']['weights'] = {'D1': .2, 'D2': .2, 'D3': .2, 'D4': .4}
        client = FakeClient(
            lambda key, count: {'score': .5 if key in ['D3', 'D4'] else 1, 'rationale': 'checked', 'critical_failure': False},
            base_url=config['judge']['base_url'],
        )
        with patch.dict(os.environ, {'INF_API_KEY': 'test-credential'}, clear=True), \
             patch('ahat_benchmark.cli.load_dotenv', create=True), \
             patch('ahat_benchmark.cli.load_config', return_value=config), \
             patch('ahat_benchmark.cli.OpenAI', return_value=client) as constructor, \
             contextlib.redirect_stdout(io.StringIO()):
            code = cli.main(['judge', '--dataset', 'fixture', '--inference', str(self.inference), '--output-dir', str(self.directory)])
        self.assertEqual(code, 0)
        self.assertEqual(constructor.call_args.kwargs['base_url'], config['judge']['base_url'])
        output = json.loads(self.judge_path.read_text())
        self.assertEqual(output['meta']['protocol']['weights'], config['scoring']['weights'])
        self.assertEqual(next(case for case in output['cases'] if case['id'] == 'valid')['score'], .7)


class CustomRegistryPipelineTests(unittest.TestCase):
    def test_archived_scene_registry_is_used_by_every_stage_and_signed(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            cases_path = directory / 'cases.json'
            registry = directory / 'datasets.yaml'
            registry.write_text(json.dumps({'datasets': {'archived-cohort': 'cases.json'}}))
            cases = [{'id': 'valid', 'instruction': 'Pick up the cup.', 'scene_graph': scene()},
                     {'id': 'empty', 'instruction': 'Pick up the cup.', 'scene_graph': scene()}]

            def save_cases():
                cases_path.write_text(json.dumps(cases))
                (directory / 'manifest.json').write_text(json.dumps({
                    'case_count': len(cases), 'data_sha256': digest(cases_path.read_bytes()),
                }))

            save_cases()
            inference = directory / 'inference.json'
            inference.write_text(json.dumps([{'id': 'valid', 'plan': PLAN}, {'id': 'empty', 'plan': []}]))
            context = dict(dataset='archived-cohort', inference_path=inference, registry_path=registry)
            val_path, judge_path, final_path = [directory / name for name in ['val.json', 'judge.json', 'final.json']]
            evaluator = RubricEvaluator(client=FakeClient(), model='test-judge', domain_path=DOMAIN)

            def val():
                return run_val_stage(**context, output_path=val_path, domain_path=DOMAIN,
                                     val_executable=VAL, timeout_seconds=10, workers=2)

            def judge():
                return run_judge_stage(**context, val_results_path=val_path, output_path=judge_path,
                                       evaluator=evaluator, workers=2)

            def summary():
                return summarize(**context, val_results_path=val_path, judge_results_path=judge_path,
                                 output_path=final_path, domain_path=DOMAIN)

            self.assertEqual(val()['statistics']['valid'], 1)
            self.assertEqual(judge()['statistics']['success'], 1)
            self.assertEqual(summary()['statistics']['final_score'], .5)
            cases[0]['scene_graph']['rooms'][0]['states']['is_clean'] = True
            save_cases()
            for stage in [val, judge, summary]:
                with self.subTest(stage=stage.__name__):
                    with self.assertRaisesRegex(ValueError, 'inputs or protocol changed'):
                        stage()
