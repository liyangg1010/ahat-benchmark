"""Shared grounding of atomic and universally quantified PDDL effects."""
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


def effects(
    expr: list[Any], bindings: dict[str, str], *,
    objects: dict[str, str] | None = None, parents: dict[str, str] | None = None,
) -> list[tuple[bool, tuple[str, ...]]]:
    """Ground effects before applying simultaneous delete/add sets.

    Unconditional forall is sufficient for adjacency cleanup. Conditional and
    numeric effects remain explicitly unsupported instead of being ignored.
    """
    if not expr:
        raise ValueError('Empty effect expression')
    if expr[0] == 'and':
        return [effect for child in expr[1:]
                for effect in effects(child, bindings, objects=objects, parents=parents)]
    if expr[0] == 'forall':
        if objects is None or len(expr) != 3 or not isinstance(expr[1], list):
            raise ValueError('forall effects require typed objects and a body')
        variables = typed_symbols(expr[1])
        choices = [[name for name, kind in objects.items() if compatible_type(kind, expected, parents or {})]
                   for expected in variables.values()]
        return [effect for values in product(*choices)
                for effect in effects(expr[2], {**bindings, **dict(zip(variables, values))},
                                      objects=objects, parents=parents)]
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
