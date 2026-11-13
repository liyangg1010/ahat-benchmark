"""Shared grounding of atomic, conditional and universally quantified PDDL effects."""
from __future__ import annotations

from itertools import product
from typing import Any


def typed_symbols(tokens: list[str], default: str = 'object') -> dict[str, str]:
    result, pending = {}, []
    i = 0
    while i < len(tokens):
        if tokens[i] == '-':
            if not pending or i + 1 >= len(tokens):
                raise ValueError('Malformed typed symbols')
            result.update((name, tokens[i + 1]) for name in pending)
            pending = []
            i += 2
        else:
            pending.append(tokens[i])
            i += 1
    result.update((name, default) for name in pending)
    return result


def compatible_type(actual: str, expected: str, parents: dict[str, str]) -> bool:
    seen = set()
    while actual and actual not in seen:
        if actual == expected:
            return True
        seen.add(actual)
        actual = parents.get(actual)
    return False


def condition(expr: list[Any], bindings: dict[str, str], state: set[tuple[str, ...]]) -> bool:
    """Evaluate supported conditional-effect guards against the pre-action state."""
    if not expr:
        raise ValueError('Empty condition')
    if expr[0] == 'and':
        return all(condition(x, bindings, state) for x in expr[1:])
    if expr[0] == 'or':
        return any(condition(x, bindings, state) for x in expr[1:])
    if expr[0] == 'not' and len(expr) == 2:
        return not condition(expr[1], bindings, state)
    if any(isinstance(x, list) for x in expr) or expr[0] in {'forall', 'exists', 'when'}:
        raise ValueError(f'Unsupported condition: {expr}')
    atom = tuple(bindings.get(x, x) for x in expr)
    if any(x.startswith('?') for x in atom):
        raise ValueError(f'Unbound condition: {atom}')
    if atom[0] == '=':
        if len(atom) != 3:
            raise ValueError('Malformed equality')
        return atom[1] == atom[2]
    return atom in state


def effects(
    expr: list[Any], bindings: dict[str, str], *,
    objects: dict[str, str] | None = None, parents: dict[str, str] | None = None,
    state: set[tuple[str, ...]] | None = None,
) -> list[tuple[bool, tuple[str, ...]]]:
    """Ground effects before applying simultaneous delete/add sets.

    Conditional guards read the immutable pre-action state. Numeric effects
    remain explicitly unsupported instead of being ignored.
    """
    if not expr:
        raise ValueError('Empty effect expression')
    if expr[0] == 'and':
        return [effect for child in expr[1:]
                for effect in effects(child, bindings, objects=objects, parents=parents, state=state)]
    if expr[0] == 'when':
        if state is None or len(expr) != 3:
            raise ValueError('Conditional effects require a pre-action state and guard/body')
        return effects(expr[2], bindings, objects=objects, parents=parents, state=state) if condition(expr[1], bindings, state) else []
    if expr[0] == 'forall':
        if objects is None or len(expr) != 3 or not isinstance(expr[1], list):
            raise ValueError('forall effects require typed objects and a body')
        variables = typed_symbols(expr[1])
        choices = [[name for name, kind in objects.items() if compatible_type(kind, expected, parents or {})]
                   for expected in variables.values()]
        return [effect for values in product(*choices)
                for effect in effects(expr[2], {**bindings, **dict(zip(variables, values))},
                                      objects=objects, parents=parents, state=state)]
    negative = expr[0] == 'not'
    if negative and (len(expr) != 2 or not isinstance(expr[1], list)):
        raise ValueError(f'Malformed negative effect: {expr}')
    atom = expr[1] if negative else expr
    if not atom or atom[0] in {'when', 'forall', 'exists', 'or', 'increase', 'assign'} or any(isinstance(x, list) for x in atom):
        raise ValueError(f'Unsupported effect: {expr}')
    grounded = tuple(bindings.get(x, x) for x in atom)
    if any(x.startswith('?') for x in grounded):
        raise ValueError(f'Unbound effect: {grounded}')
    return [(negative, grounded)]
