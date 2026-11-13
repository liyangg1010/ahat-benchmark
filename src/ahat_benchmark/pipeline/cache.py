"""Check persisted VAL cases before any resume, judge request or summary."""
from ..domains import domain_binding, resolve_domain
from ..pddl import full_problem, sexpr
from ..provenance import digest
from ..val.validator import normalize_action


def plan_identity(plan):
    if not isinstance(plan, list) or any(not isinstance(step, str) for step in plan):
        raise ValueError('VAL cached plan must be a list of actions')
    try:
        return [sexpr(normalize_action(step)) for step in plan]
    except ValueError:
        # Malformed submitted plans still have to match their stored raw input.
        return plan


def verify_val_cases(aligned, val_by_id, domain_path):
    for case, inference in aligned:
        value = val_by_id.get(case.id)
        if value is None:
            continue  # An unfinished VAL run can be resumed.
        expected = domain_binding(case.domain_id, domain_path)
        if any(value.get(key) != item for key, item in expected.items()):
            raise ValueError(f'VAL domain binding mismatch for {case.id}')
        if plan_identity(value.get('plan')) != plan_identity(inference.plan if inference else []):
            raise ValueError(f'VAL plan does not match inference for {case.id}; rerun VAL')
        if value.get('status') == 'valid':
            problem = value.get('problem_pddl')
            if not isinstance(problem, str) or digest(problem.encode()) != value.get('problem_sha256'):
                raise ValueError('VAL initial-state record is missing or corrupt; rerun VAL')
            current = full_problem(case.scene_graph, resolve_domain(case.domain_id, domain_path))
            if problem != current:
                raise ValueError(f'VAL initial state does not match scene for {case.id}; rerun VAL')
