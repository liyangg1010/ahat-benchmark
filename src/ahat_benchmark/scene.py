"""Canonical scene links shared by initial-state conversion and judge inputs."""
from __future__ import annotations

import re
from typing import Any


def held_objects(value: Any) -> list[str]:
    """Canonical person's inventory, accepting legacy single-object scenes."""
    if value is None:
        return []
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list) or any(not isinstance(x, str) or not x for x in values):
        raise ValueError('p_holding must be an object name or a list of object names')
    return list(dict.fromkeys(values))


def normalize_person_locations(scene: dict[str, Any]) -> None:
    """Fill missing person locations from links, rejecting conflicting claims.

    A room edge may describe the room of a more precise physical location; it
    must not become a second person_at fact. Scenes without any position evidence
    remain unspecified. Call on an owned copy, as with sync_agent_rooms.
    """
    links = normalize_links(scene)
    physical = {n if isinstance(n, str) else n['name']: category
                for category in ('rooms', 'furnitures', 'devices', 'objects', 'containers')
                for n in scene.get(category) or []}
    parents: dict[str, set[str]] = {}
    for link in links:
        if link['relation'] in {'on', 'in'}:
            parents.setdefault(link['from'], set()).add(link['to'])

    def rooms_of(name: str, visited: set[str]) -> set[str]:
        if physical.get(name) == 'rooms':
            return {name}
        if name in visited:
            return set()
        return set().union(*(rooms_of(parent, visited | {name})
                             for parent in parents.get(name, set())))

    for person in scene.get('person') or []:
        name = person['name']
        explicit = person.get('location')
        targets = parents.get(name, set())
        for target in [*targets, *([explicit] if explicit is not None else [])]:
            if not isinstance(target, str) or target not in physical:
                raise ValueError(f'person {name} location must reference a declared physical object: {target!r}')
        precise = {target for target in targets if physical[target] != 'rooms'}
        room_links = targets - precise
        if len(precise) > 1 or len(room_links) > 1:
            raise ValueError(f'person {name} has ambiguous location links')
        location = explicit if explicit is not None else next(iter(precise or room_links), None)
        if location is None:
            continue
        if precise and precise != {location}:
            raise ValueError(f'person {name} location conflicts with location links')
        if room_links and rooms_of(location, set()) != room_links:
            raise ValueError(f'person {name} location conflicts with room links')
        person['location'] = location


def sync_agent_rooms(scene: dict[str, Any], previous_rooms: dict[str, str] | None = None) -> None:
    """Refresh redundant room links from precise locations after a full action.

    A picked-up object can remain the robot's navigation anchor. Its room then
    comes from its carrier's last room, not from the deleted support relation.
    These room links never create additional agent_at facts. This function is
    not a spatial-cycle validator; cycle prevention is a separate pending change.
    """
    links = normalize_links(scene)
    nodes = {n['name']: (category, n)
             for category, items in scene.items() if category != 'links' and isinstance(items, list)
             for raw in items for n in ([{'name': raw}] if isinstance(raw, str) else [raw])
             if isinstance(n, dict) and 'name' in n}
    rooms = {name for name, (category, _) in nodes.items() if category == 'rooms'}
    agents = {n['name']: n for n in scene.get('agent') or []}
    fallback = {name: set() for name in agents}
    parents: dict[str, list[str]] = {}
    for link in links:
        if link['relation'] not in {'on', 'in'}:
            continue
        child, parent = link['from'], link['to']
        if child in agents:
            if link['relation'] == 'in' and parent in rooms:
                fallback[child].add(parent)
        else:
            parents.setdefault(child, []).append(parent)
    for name, room in (previous_rooms or {}).items():
        if name in agents and room in rooms:
            fallback[name] = {room}
    carriers = {}
    for agent in agents.values():
        if agent.get('holding'):
            carriers[agent['holding']] = agent['name']
    for person in scene.get('person') or []:
        for obj in held_objects(person.get('p_holding')):
            carriers[obj] = person['name']

    def resolve(name, visited):
        if name in rooms:
            return {name}
        if name in visited or name not in nodes:
            return set()
        visited = visited | {name}
        category, node = nodes[name]
        if category in {'agent', 'person'}:
            found = resolve(node.get('location'), visited)
            if not found and category == 'person':
                found = set().union(*(resolve(p, visited) for p in parents.get(name, [])))
            return found or fallback.get(name, set())
        found = set().union(*(resolve(p, visited) for p in parents.get(name, [])))
        if not found and name in carriers:
            found = resolve(carriers[name], visited)
        return found

    inferred = {name: resolve(agent.get('location'), {name}) or fallback[name]
                for name, agent in agents.items()}
    scene['links'] = [link for link in links if not (
        link['relation'] == 'in' and link['from'] in agents and link['to'] in rooms)]
    for name, found in inferred.items():
        if len(found) == 1:
            scene['links'].append({'relation': 'in', 'from': name, 'to': next(iter(found))})


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
    held = {item.get('holding') for item in scene.get('agent') or [] if isinstance(item, dict)}
    held.update(obj for item in scene.get('person') or [] if isinstance(item, dict)
                for obj in held_objects(item.get('p_holding')))
    for link in links:
        if link['relation'] != 'next_to':
            continue
        a, b, location = (link[k] for k in ('obj1', 'obj2', 'location'))
        if a in held or b in held or not any(
            (rel, a, location) in supports and (rel, b, location) in supports for rel in ('on', 'in')
        ):
            raise ValueError(f'next_to objects must share the stated surface or receptacle: {a}, {b}, {location}')
    return links
