from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Any

from ..domains import check_inference_binding, domain_binding
from ..datasets import align_cases, load_eval_set, load_inference
from ..io import read_json
from ..judge.evaluator import RubricEvaluator
from ..provenance import index_cases, make_provenance, require_compatible, result_digest, verify_stage_context
from .common import save_stage
from .cache import verify_val_cases


ZERO_STATUSES = {"invalid", "missing_plan", "malformed_plan"}


def run_judge_stage(
    *, dataset: str, inference_path: Path, val_results_path: Path, output_path: Path,
    evaluator: RubricEvaluator, workers: int, resume: bool = True,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    eval_cases = load_eval_set(dataset, registry_path=registry_path)
    inference_meta, inference_cases = load_inference(inference_path)
    val_data = read_json(val_results_path)
    val_provenance = verify_stage_context(
        val_data, stage="val", dataset=dataset, eval_cases=eval_cases,
        inference_path=inference_path, domain_path=evaluator.domain_path,
    )
    aligned = align_cases(eval_cases, inference_cases, allow_missing=val_provenance["protocol"].get("allow_missing", False))
    for case, inference in aligned:
        check_inference_binding(case, inference, evaluator.domain_path)
    val_by_id = index_cases(val_data, eval_cases)
    missing = [case.id for case in eval_cases if case.id not in val_by_id]
    if missing:
        raise ValueError(f"VAL stage is incomplete; missing {len(missing)} cases")
    verify_val_cases(aligned, val_by_id, evaluator.domain_path)

    provenance = make_provenance(
        stage="judge", dataset=dataset, eval_cases=eval_cases, inference_path=inference_path,
        domain_path=evaluator.domain_path, protocol=evaluator.protocol(), parent_signature=result_digest(val_data),
    )
    previous = {}
    if resume and output_path.exists():
        old = read_json(output_path)
        require_compatible(old, provenance)
        previous = index_cases(old, eval_cases)
    completed = {
        key: value for key, value in previous.items()
        if (value.get("status") == "success" and val_by_id[key].get("status") == "valid")
        or (value.get("status") == "skipped_val_invalid" and val_by_id[key].get("status") in ZERO_STATUSES)
    }
    results = dict(completed)
    # Keep unfinished dimensions on disk while resumed cases wait for a worker.
    results.update({key: value for key, value in previous.items()
                    if key not in completed and val_by_id[key].get("status") == "valid"})
    lock = Lock()

    def save():
        return save_stage(
            dataset, inference_path, inference_meta, eval_cases, results, output_path, provenance,
            evaluator.domain_path, {"eval_model": evaluator.model},
        )

    def checkpoint(case_id, result):
        with lock:
            results[case_id] = {"id": case_id, "val_status": "valid", **result}
            save()

    def evaluate(pair):
        eval_case, _ = pair
        validation = val_by_id[eval_case.id]
        expected_binding = domain_binding(eval_case.domain_id, evaluator.domain_path)
        if any(validation.get(k) != v for k, v in expected_binding.items()):
            raise ValueError(f'VAL domain binding mismatch for {eval_case.id}')
        if validation.get("status") != "valid":
            ordinary_invalid = validation.get("status") in ZERO_STATUSES
            return eval_case.id, {
                "id": eval_case.id,
                "status": "skipped_val_invalid" if ordinary_invalid else "skipped_val_error",
                "score": 0.0 if ordinary_invalid else None,
                "result": "Bad" if ordinary_invalid else None,
                "val_status": validation.get("status"), "dimensions": {},
                "error": None if ordinary_invalid else validation.get("fail_reason"),
            }
        result = evaluator.evaluate(
            eval_case.instruction, eval_case.scene_graph, validation["plan"],
            problem_text=validation["problem_pddl"], domain_id=eval_case.domain_id,
            previous_dimensions=previous.get(eval_case.id, {}).get("dimensions"),
            on_update=lambda value: checkpoint(eval_case.id, value),
        )
        return eval_case.id, {"id": eval_case.id, "val_status": "valid", **result}

    save()
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [executor.submit(evaluate, pair) for pair in aligned if pair[0].id not in completed]
        for future in as_completed(futures):
            case_id, result = future.result()
            with lock:
                results[case_id] = result
                save()
    return save()
