"""D2 inventory/locations formatting from the audited review's sum_sg_content."""
from __future__ import annotations

import copy
from typing import Any

from ..scene import held_objects, normalize_links, normalize_person_locations, sync_agent_rooms


def organize_content_list(content_list: list[str]) -> list[str]:
    def get_sort_key(s):
        last_underscore = s.rfind('_')
        if last_underscore == -1:
            return (s, 0)
        index_str = s[last_underscore + 1:]
        return (s[:last_underscore], int(index_str)) if index_str.isdigit() else (s, 0)
    return sorted(content_list, key=get_sort_key)


def get_parents_str(name: str, links: list[list[str]]) -> str:
    related_links = [link for link in links if name == link[1]]
    if len(related_links) > 1:
        return '(' + ', '.join(f'{link[2]} {link[0]}' for link in related_links) + ')'
    if related_links:
        return f'({related_links[0][2]} {related_links[0][0]})'
    return ''


def summarize_scene(scene_graph: dict[str, Any]) -> str:
    scene_graph = copy.deepcopy(scene_graph)
    normalize_person_locations(scene_graph)
    sync_agent_rooms(scene_graph)
    normalized = normalize_links(scene_graph)
    links = [[link['to'], link['from'], link['relation']]
             for link in normalized if link['relation'] in {'on', 'in'}]

    def names(category, sort=True):
        items = scene_graph.get(category) or []
        result = [item if isinstance(item, str) else item['name'] for item in items]
        if sort:
            result = organize_content_list(result)
        return [name + get_parents_str(name, links) for name in result]

    room_list = names('rooms')
    furniture_list = names('furnitures')
    object_list = names('objects')
    agent_list = names('agent', sort=False)
    person_list = names('person', sort=False)
    summary = f"'room_list': {room_list}, 'furniture_list': {furniture_list}, 'object_list': {object_list}, 'agent_list': {agent_list}, 'person_list': {person_list}"
    if scene_graph.get('devices'):
        summary += f", 'device_list': {names('devices')}"
    adjacency = [(link['obj1'], link['obj2'], link['location'])
                 for link in normalized if link['relation'] == 'next_to']
    if adjacency:
        summary += f", 'initial_next_to (undirected)': {adjacency}"
    summary += f", 'agent_locations': { {a['name']: a.get('location') for a in scene_graph.get('agent') or []} }"
    inventories = {p['name']: held_objects(p.get('p_holding')) for p in scene_graph.get('person') or []}
    if scene_graph.get('person'):
        summary += f", 'person_locations': { {p['name']: p.get('location') for p in scene_graph['person']} }"
    if inventories:
        summary += f", 'person_holdings': {inventories}"
    return summary
