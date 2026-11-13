import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from ahat_benchmark.datasets import load_eval_set, load_inference
from ahat_benchmark.domains import BASE_DOMAIN, LIQUID_DOMAIN, check_inference_binding, resolve_domain
from ahat_benchmark.val.validator import validate_plan
from helpers import DOMAIN, PROJECT, VAL


class GenerateInferenceTests(unittest.TestCase):
    def test_mixed_domain_requests_and_saved_results_use_task_bindings(self):
        spec = importlib.util.spec_from_file_location('generate_inference', PROJECT / 'scripts/generate_inference.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cases = load_eval_set('ahat-medium')
        selected = [next(c for c in cases if c.domain_id == domain)
                    for domain in (BASE_DOMAIN, LIQUID_DOMAIN)]
        references = {r['id']: r['plan'] for r in map(json.loads,
                      (PROJECT / 'benchmarks/ahat_eval_set.jsonl').read_text().splitlines())}
        calls = []

        def complete(**kwargs):
            calls.append(kwargs)
            plan = references[selected[len(calls) - 1].id]
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({'plan': plan})))])

        client = Mock()
        client.chat.completions.create.side_effect = complete
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'inference.json'
            argv = ['generate_inference', '--dataset', 'ahat-medium', '--limit', '0',
                    '--model', 'test-planner', '--base-url', 'https://planner.example/v1', '--output', str(output)]
            with patch.object(sys, 'argv', argv), patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}, clear=True), \
                 patch.object(module, 'load_dotenv'), patch.object(module, 'OpenAI', return_value=client), \
                 patch.object(module, 'load_eval_set', return_value=selected), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(module.main(), 0)
            _, inference = load_inference(output)
            for case, call in zip(selected, calls):
                domain = resolve_domain(case.domain_id)
                prompt = call['messages'][1]['content']
                self.assertTrue(prompt.endswith(domain.read_text()))
                self.assertNotIn('reference_goal', prompt)
                self.assertNotIn('"plan":', prompt)
                self.assertEqual(':action fill_from_faucet' in prompt, case.domain_id == LIQUID_DOMAIN)
                check_inference_binding(case, inference[case.id], DOMAIN)
                result = validate_plan(scene_graph=case.scene_graph, plan=inference[case.id].plan,
                                       domain_path=domain, val_executable=VAL, timeout_seconds=10)
                self.assertEqual(result['status'], 'valid', result)
