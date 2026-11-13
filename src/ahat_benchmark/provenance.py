"""Versioned input/protocol signatures for evaluation and checkpoint recovery."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .schemas import EvalCase
from .domains import domain_binding


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def result_digest(output: dict[str, Any]) -> str:
    """Bind consumers to the actual upstream cases as well as their inputs."""
    cases_hash = digest(canonical(output.get('cases', [])).encode())
    if output.get('meta', {}).get('cases_sha256') != cases_hash:
        raise ValueError('Evaluation result content is missing or corrupt; rerun the stage')
    return digest(canonical({'signature': output['meta']['signature'], 'cases_sha256': cases_hash}).encode())


def file_digest(path: Path) -> str | None:
    return digest(path.read_bytes()) if path.is_file() else None


def code_digest() -> str:
    root = Path(__file__).parent
    files = sorted([*root.rglob("*.py"), *root.rglob("*.txt")])
    return digest(canonical({str(p.relative_to(root)): file_digest(p) for p in files}).encode())


def make_provenance(
    *, stage: str, dataset: str, eval_cases: list[EvalCase], inference_path: Path,
    domain_path: Path, protocol: dict[str, Any], parent_signature: str | None = None,
) -> dict[str, Any]:
    inputs = {
        "dataset": dataset,
        "eval_cases_sha256": digest(canonical([
            {"id": case.id, "instruction": case.instruction, "scene_graph": case.scene_graph, "domain_id": case.domain_id}
            for case in eval_cases
        ]).encode()),
        "inference_sha256": file_digest(inference_path),
    }
    record = {
        "schema_version": "2.0", "stage": stage, "inputs": inputs,
        "protocol": {**protocol, "domain_sha256": file_digest(domain_path),
                     "task_domains": {case.id: domain_binding(case.domain_id, domain_path) for case in eval_cases},
                     "code_sha256": code_digest()},
        "parent_signature": parent_signature,
    }
    return {**record, "signature": digest(canonical(record).encode())}


def require_compatible(output: dict[str, Any], expected: dict[str, Any]) -> None:
    meta = output.get("meta", {})
    if meta.get("signature") != expected["signature"]:
        raise ValueError(
            "Evaluation inputs or protocol changed (or checkpoint is unversioned); "
            "use a new output directory or --no-resume"
        )
    for key in ("stage", "schema_version", "inputs", "protocol", "parent_signature"):
        if meta.get(key) != expected[key]:
            raise ValueError(f"Checkpoint metadata mismatch: {key}")
    result_digest(output)


def verify_stage_context(
    output: dict[str, Any], *, stage: str, dataset: str, eval_cases: list[EvalCase],
    inference_path: Path, domain_path: Path, parent_signature: str | None = None,
) -> dict[str, Any]:
    meta = output.get("meta", {})
    protocol = dict(meta.get("protocol", {}))
    if stage == "val":
        executable = Path(protocol.get("val_executable", ""))
        protocol["validator_sha256"] = file_digest(executable)
        protocol["validator_library_sha256"] = file_digest(executable.parent / "libVAL.so")
    expected = make_provenance(
        stage=stage, dataset=dataset, eval_cases=eval_cases, inference_path=inference_path,
        domain_path=domain_path, protocol=protocol, parent_signature=parent_signature,
    )
    require_compatible(output, expected)
    return expected


def index_cases(output: dict[str, Any], eval_cases: list[EvalCase]) -> dict[str, dict[str, Any]]:
    expected_ids = {case.id for case in eval_cases}
    result = {}
    for item in output.get("cases", []):
        case_id = item.get("id")
        if case_id not in expected_ids or case_id in result:
            raise ValueError(f"Unknown or duplicate evaluation result ID: {case_id}")
        result[case_id] = item
    return result
