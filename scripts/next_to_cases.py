"""Deterministic, locally authored adjacency tasks; no upstream records are rewritten.

The definitions are also used by the offline goal checks. Run this file to print
the ten source records as JSONL; integration into manifests is a release step.
"""
from __future__ import annotations

import json
from uuid import NAMESPACE_URL, uuid5


def build_cases():
    cases = []

    def add(slug, split, instruction, supports, items, operations, goals, adjacency=(), opened=()):
        graph = {
            'rooms': [{'name': 'room_1', 'states': {}}, {'name': 'room_2', 'states': {}}],
            'furnitures': [], 'objects': [],
            'agent': [{'name': 'agent_0', 'location': 'room_1', 'holding': None}],
            'person': [], 'links': [],
        }
        for index, (name, openable) in enumerate(supports):
            states = {'can_be_opened': True, 'is_open': name in opened} if openable else {}
            if name in {'pencil_case_1', 'craft_box_1'}:
                graph['objects'].append({'name': name, 'states': states})
                # Portable receptacles rest on the first surface, not inside a room as a container.
                graph['links'].append({'relation': 'on', 'from': name, 'to': supports[0][0]
                                       if supports[0][0] != name else 'storage_table_1'})
                if supports[0][0] == name:
                    graph['furnitures'].append({'name': 'storage_table_1', 'states': {}})
                    graph['links'].append({'relation': 'in', 'from': 'storage_table_1', 'to': 'room_1'})
            else:
                graph['furnitures'].append({'name': name, 'states': states})
                graph['links'].append({'relation': 'in', 'from': name, 'to': f'room_{1 + index % 2}'})
        for name, relation, support in items:
            graph['objects'].append({'name': name, 'states': {}})
            graph['links'].append({'relation': relation, 'from': name, 'to': support})
        for first, second, support in adjacency:
            graph['links'].append({'relation': 'next_to', 'obj1': first, 'obj2': second, 'location': support})
        locations = {name: (relation, support) for name, relation, support in items}
        position, plan = 'room_1', []

        def navigate(target):
            nonlocal position
            if position != target:
                plan.append(f'(navigate agent_0 {position} {target})')
                position = target

        for operation in operations:
            if operation[0] in ('open', 'close'):
                action, target = operation
                navigate(target)
                plan.append(f'({action} agent_0 {target})')
                continue
            _, obj, relation, target, reference = operation
            old_relation, old_support = locations[obj]
            navigate(obj)
            pick = 'pick_from_surface' if old_relation == 'on' else 'pick_from_receptacle'
            plan.append(f'({pick} agent_0 {obj} {old_support})')
            navigate(target)
            if reference:
                action = 'place_next_to_surface' if relation == 'on' else 'place_next_to_inside'
                plan.append(f'({action} agent_0 {obj} {reference} {target})')
            else:
                action = 'place_on_surface' if relation == 'on' else 'place_in_receptacle'
                plan.append(f'({action} agent_0 {obj} {target})')
            locations[obj] = (relation, target)
        case_id = str(uuid5(NAMESPACE_URL, f'ahat-benchmark/next-to-v1/{slug}'))
        cases.append({'record_id': case_id, 'id': case_id, 'instruction': instruction,
                      'scene_graph': graph, 'plan': plan, 'type': split,
                      'reference_goal': goals,
                      'source': {'kind': 'local_authored', 'revision': 'next-to-v1', 'scenario': slug}})

    add('cup-and-plate', 'easy',
        'Move cup_1 from counter_1 onto dining_table_1, next to plate_1. Leave plate_1 on that table.',
        [('counter_1', False), ('dining_table_1', False)],
        [('cup_1', 'on', 'counter_1'), ('plate_1', 'on', 'dining_table_1'), ('vase_1', 'on', 'counter_1')],
        [('move', 'cup_1', 'on', 'dining_table_1', 'plate_1')],
        ['(item_on_surface cup_1 dining_table_1)', '(item_on_surface plate_1 dining_table_1)', '(next_to cup_1 plate_1 dining_table_1)'])
    add('book-and-lamp', 'easy',
        'Put book_1 on nightstand_1 beside lamp_1, leaving the lamp in place.',
        [('shelf_1', False), ('nightstand_1', False)],
        [('book_1', 'on', 'shelf_1'), ('lamp_1', 'on', 'nightstand_1'), ('book_2', 'on', 'shelf_1')],
        [('move', 'book_1', 'on', 'nightstand_1', 'lamp_1')],
        ['(item_on_surface book_1 nightstand_1)', '(item_on_surface lamp_1 nightstand_1)', '(next_to book_1 lamp_1 nightstand_1)'])
    add('towel-and-soap', 'easy',
        'Take towel_1 from bench_1 and place it next to soap_1 on bathroom_shelf_1. Keep soap_1 there.',
        [('bench_1', False), ('bathroom_shelf_1', False)],
        [('towel_1', 'on', 'bench_1'), ('soap_1', 'on', 'bathroom_shelf_1'), ('brush_1', 'on', 'bench_1')],
        [('move', 'towel_1', 'on', 'bathroom_shelf_1', 'soap_1')],
        ['(item_on_surface towel_1 bathroom_shelf_1)', '(item_on_surface soap_1 bathroom_shelf_1)', '(next_to towel_1 soap_1 bathroom_shelf_1)'])
    add('pen-in-drawer', 'easy',
        'Put pen_1 inside drawer_1 next to notebook_1, leave the notebook inside, and close the drawer afterward.',
        [('desk_1', False), ('drawer_1', True)],
        [('pen_1', 'on', 'desk_1'), ('notebook_1', 'in', 'drawer_1'), ('ruler_1', 'on', 'desk_1')],
        [('open', 'drawer_1'), ('move', 'pen_1', 'in', 'drawer_1', 'notebook_1'), ('close', 'drawer_1')],
        ['(item_in_receptacle pen_1 drawer_1)', '(item_in_receptacle notebook_1 drawer_1)', '(next_to pen_1 notebook_1 drawer_1)', '(not (is_open drawer_1))'])
    add('preserve-existing-pair', 'easy',
        'Place spoon_1 on dining_table_1 next to plate_1. Keep cup_1 and plate_1 next to each other on that table.',
        [('counter_1', False), ('dining_table_1', False)],
        [('spoon_1', 'on', 'counter_1'), ('cup_1', 'on', 'dining_table_1'), ('plate_1', 'on', 'dining_table_1')],
        [('move', 'spoon_1', 'on', 'dining_table_1', 'plate_1')],
        ['(next_to spoon_1 plate_1 dining_table_1)', '(next_to cup_1 plate_1 dining_table_1)'],
        adjacency=[('cup_1', 'plate_1', 'dining_table_1')])
    add('replace-old-neighbor', 'easy',
        'Move cup_1 away from plate_1 on dining_table_1 and put it next to teapot_1 on counter_1. Leave the plate and teapot where they are.',
        [('counter_1', False), ('dining_table_1', False)],
        [('cup_1', 'on', 'dining_table_1'), ('plate_1', 'on', 'dining_table_1'), ('teapot_1', 'on', 'counter_1')],
        [('move', 'cup_1', 'on', 'counter_1', 'teapot_1')],
        ['(next_to cup_1 teapot_1 counter_1)', '(item_on_surface plate_1 dining_table_1)',
         '(not (next_to cup_1 plate_1 dining_table_1))', '(not (next_to plate_1 cup_1 dining_table_1))'],
        adjacency=[('cup_1', 'plate_1', 'dining_table_1')])
    add('two-required-neighbors', 'medium',
        'Bring cup_1 from counter_1 and napkin_1 from shelf_1 to dining_table_1. Put each one next to plate_1, keeping the plate on the table.',
        [('counter_1', False), ('shelf_1', False), ('dining_table_1', False)],
        [('cup_1', 'on', 'counter_1'), ('napkin_1', 'on', 'shelf_1'), ('plate_1', 'on', 'dining_table_1')],
        [('move', 'cup_1', 'on', 'dining_table_1', 'plate_1'), ('move', 'napkin_1', 'on', 'dining_table_1', 'plate_1')],
        ['(next_to cup_1 plate_1 dining_table_1)', '(next_to napkin_1 plate_1 dining_table_1)'])
    add('reestablish-pair-on-new-support', 'medium',
        'Move book_1 and book_2 from shelf_1 to desk_1 and arrange them next to each other on the desk. Leave neither book on the shelf.',
        [('shelf_1', False), ('desk_1', False)],
        [('book_1', 'on', 'shelf_1'), ('book_2', 'on', 'shelf_1'), ('lamp_1', 'on', 'desk_1')],
        [('move', 'book_1', 'on', 'desk_1', None), ('move', 'book_2', 'on', 'desk_1', 'book_1')],
        ['(next_to book_1 book_2 desk_1)', '(not (item_on_surface book_1 shelf_1))',
         '(not (item_on_surface book_2 shelf_1))', '(not (next_to book_1 book_2 shelf_1))'],
        adjacency=[('book_1', 'book_2', 'shelf_1')])
    add('change-receptacle-and-neighbor', 'medium',
        'Take pen_1 from beside eraser_1 inside pencil_case_1 and put it inside drawer_1 next to ruler_1. Leave the eraser in the pencil case, keep the ruler in the drawer, and close the drawer afterward.',
        [('pencil_case_1', True), ('drawer_1', True)],
        [('pen_1', 'in', 'pencil_case_1'), ('eraser_1', 'in', 'pencil_case_1'), ('ruler_1', 'in', 'drawer_1')],
        [('open', 'drawer_1'), ('move', 'pen_1', 'in', 'drawer_1', 'ruler_1'), ('close', 'drawer_1')],
        ['(next_to pen_1 ruler_1 drawer_1)', '(item_in_receptacle eraser_1 pencil_case_1)',
         '(not (next_to pen_1 eraser_1 pencil_case_1))', '(not (is_open drawer_1))'],
        adjacency=[('pen_1', 'eraser_1', 'pencil_case_1')], opened=['pencil_case_1'])
    add('surface-and-receptacle-goals', 'medium',
        'Put scissors_1 inside craft_box_1 next to tape_1 and close the box. Also put notebook_1 on desk_1 next to pencil_1. Leave the tape and pencil in place.',
        [('shelf_1', False), ('craft_box_1', True), ('desk_1', False)],
        [('scissors_1', 'on', 'shelf_1'), ('tape_1', 'in', 'craft_box_1'),
         ('notebook_1', 'on', 'shelf_1'), ('pencil_1', 'on', 'desk_1')],
        [('open', 'craft_box_1'), ('move', 'scissors_1', 'in', 'craft_box_1', 'tape_1'),
         ('close', 'craft_box_1'), ('move', 'notebook_1', 'on', 'desk_1', 'pencil_1')],
        ['(next_to scissors_1 tape_1 craft_box_1)', '(not (is_open craft_box_1))', '(next_to notebook_1 pencil_1 desk_1)'])
    return cases


if __name__ == '__main__':
    for record in build_cases():
        print(json.dumps(record, ensure_ascii=False))
