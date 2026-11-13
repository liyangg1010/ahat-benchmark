"""Resolve each task's fixed domain; generation and evaluation share this API."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .config import PROJECT_DIR

BASE_DOMAIN = 'ahat-v8-group-portions'
LIQUID_DOMAIN = 'ahat-liquid-v1'


def domain_registry() -> dict:
    manifest = json.loads((PROJECT_DIR / 'benchmark_manifest.json').read_text())
    return manifest.get('domains', {manifest['domain']['name']: manifest['domain']})


def resolve_domain(domain_id: str | None = None, default_path: Path | None = None) -> Path:
    if domain_id is None and default_path is not None:
        return default_path
    name = domain_id or BASE_DOMAIN
    registry = domain_registry()
    if name not in registry:
        raise ValueError(f'Unknown task domain: {name}')
    entry = registry[name]
    path = PROJECT_DIR / entry['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
        raise ValueError(f'Domain fingerprint mismatch: {name}')
    return path


def task_domain(record: dict, default_path: Path | None = None) -> Path:
    return resolve_domain(record.get('domain_id'), default_path)


def domain_binding(domain_id: str | None, default_path: Path | None = None) -> dict:
    path = resolve_domain(domain_id, default_path)
    return {'domain_id': domain_id or BASE_DOMAIN, 'domain_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def check_inference_binding(case, inference, default_path: Path) -> None:
    if inference is None:
        return
    required = case.domain_id == LIQUID_DOMAIN
    if required or inference.domain_id is not None or inference.domain_sha256 is not None:
        expected = domain_binding(case.domain_id, default_path)
        if (inference.domain_id, inference.domain_sha256) != (expected['domain_id'], expected['domain_sha256']):
            raise ValueError(f'Inference domain mismatch for {case.id}; regenerate using the task domain and record its ID/hash')
