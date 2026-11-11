"""Canonical scene links shared by initial-state conversion and judge inputs."""
from __future__ import annotations

import re
from typing import Any


def normalize_links(scene: dict[str, Any]) -> list[dict[str, str]]:
    """Store each undirected adjacency once; reject unsupported spatial claims.

    Legacy [parent, child, on/in] links remain accepted. Adjacency requires an
    explicit location and is never inferred merely from sharing a support.
    """
    raw = scene.get('links', [])
    if not isinstance(raw, list):
        raise ValueError('scene links must be a list')
    nodes = {}
    for category, items in scene.items():
        if category == 'links' or not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and 'name' in item:
                nodes[item['name']] = category
                if 'next_to' in (item.get('states') or {}):
                    raise ValueError('next_to belongs in links with obj1, obj2 and location, not states')
            elif isinstance(item, str):
                nodes[item] = category
    links, seen = [], set()
    for link in raw:
        if isinstance(link, list) and len(link) == 3 and link[2] in {'on', 'in'}:
            link = {'relation': link[2], 'from': link[1], 'to': link[0]}
        if not isinstance(link, dict):
            raise ValueError('links require [parent, child, on/in] or a relation dictionary; '
                             'next_to requires obj1, obj2 and location')
        relation = link.get('relation')
        keys = ('from', 'to') if relation in {'on', 'in'} else (
            ('obj1', 'obj2', 'location') if relation == 'next_to' else ())
        if not keys or any(not isinstance(link.get(k), str) or not link[k] for k in keys):
            raise ValueError(f'invalid scene link: {link!r}')
        values = tuple(link[k] for k in keys)
        if relation == 'next_to':
            a, b, location = values
            if len({a, b, location}) != 3:
                raise ValueError('next_to requires distinct objects and support')
            if any(nodes.get(x) not in {'rooms', 'furnitures', 'devices', 'objects', 'containers'}
                   for x in values):
                raise ValueError('next_to references an unknown or nonphysical object')
            if any(not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]*', x) for x in values):
                raise ValueError('next_to references an invalid PDDL identifier')
            values = (*sorted((a, b)), location)
        identity = (relation, *values)
        if identity not in seen:
            seen.add(identity)
            links.append({'relation': relation, **dict(zip(keys, values))})
    supports = {(x['relation'], x['from'], x['to']) for x in links
                if x['relation'] in {'on', 'in'}
                and not (x['relation'] == 'in' and nodes.get(x['from']) in {'furnitures', 'devices'}
                         and nodes.get(x['to']) == 'rooms')}
    held = {item.get(key) for category, key in (('agent', 'holding'), ('person', 'p_holding'))
            for item in scene.get(category) or [] if isinstance(item, dict)}
    for link in links:
        if link['relation'] != 'next_to':
            continue
        a, b, location = (link[k] for k in ('obj1', 'obj2', 'location'))
        if a in held or b in held or not any(
            (rel, a, location) in supports and (rel, b, location) in supports for rel in ('on', 'in')
        ):
            raise ValueError(f'next_to objects must share the stated surface or receptacle: {a}, {b}, {location}')
    return links
