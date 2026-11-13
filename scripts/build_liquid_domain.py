#!/usr/bin/env python3
"""Generate a standalone liquid domain by extending the ordinary domain.

Shared actions are copied unchanged; liquid actions are defined here independently.
Run --check in CI to detect drift.
"""
from pathlib import Path
import argparse
from ahat_benchmark.pddl import sexpr

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'vendor/pddl/domain_0102_test.pddl'
OUTPUT = ROOT / 'vendor/pddl/domain_liquid_v1.pddl'
KINDS = ('water', 'tea', 'coffee', 'other_drink')
CONTENT = tuple('contains_' + k for k in KINDS) + ('contents_heated',)
PREDICATES = (*CONTENT, 'is_liquid_container', 'is_kettle', 'is_coffee_machine',
              'tea_supply', 'coffee_supply', 'ingredient_available', 'tea_loaded', 'coffee_loaded',
              'is_plant_receiver', 'watered', 'water_checked', 'contains_noodles', 'noodles_prepared')

def clear(obj):
    return ' '.join(f'(not ({p} {obj}))' for p in (*CONTENT, 'noodles_prepared', 'water_checked'))

def action(name, params, pre, effect):
    return sexpr(f'(:action {name} :parameters ({params}) :precondition (and {pre}) :effect (and {effect}))')

def generated():
    domain = sexpr(BASE.read_text())
    next(x for x in domain if isinstance(x,list) and x[0]=='domain')[1] = 'ahat-liquid-v1'
    req = next(x for x in domain if isinstance(x,list) and x[0]==':requirements')
    if ':conditional-effects' not in req: req.append(':conditional-effects')
    preds = next(x for x in domain if isinstance(x,list) and x[0]==':predicates')
    preds.extend([[p,'?c','-','physobj'] for p in PREDICATES])
    liquid_actions = {}
    liquid_actions['fill_from_faucet'] = action('fill_from_faucet', '?ag - agent ?c - physobj ?faucet_loc - physobj',
        '(agent_at ?ag ?faucet_loc) (holding ?ag ?c) (not (handempty ?ag)) (has_faucet ?faucet_loc) (is_liquid_container ?c) (not (is_filled ?c)) (imply (can_be_opened ?c) (is_open ?c))',
        f'{clear("?c")} (is_filled ?c) (contains_water ?c)')
    liquid_actions['fill_device_with_water'] = action('fill_device_with_water', '?ag - agent ?d - physobj',
        '(agent_at ?ag ?d) (not (is_filled ?d)) (has_faucet ?d) (is_liquid_container ?d)',
        f'{clear("?d")} (is_filled ?d) (contains_water ?d)')
    transfer = ' '.join(f'(when ({p} ?c) ({p} ?target))' for p in CONTENT)
    liquid_actions['pour_into'] = action('pour_into', '?ag - agent ?c - physobj ?target - physobj',
        '(holding ?ag ?c) (not (handempty ?ag)) (is_filled ?c) (is_liquid_container ?c) (agent_at ?ag ?target) (is_liquid_container ?target) (not (is_filled ?target)) (not (= ?c ?target))',
        f'(not (is_filled ?c)) {clear("?c")} {clear("?target")} (is_filled ?target) {transfer}')
    liquid_actions['pour'] = action('pour', '?ag - agent ?c - physobj ?furn_with_faucet - furniture',
        '(holding ?ag ?c) (not (handempty ?ag)) (is_filled ?c) (is_liquid_container ?c) (agent_at ?ag ?furn_with_faucet) (has_faucet ?furn_with_faucet)',
        f'(not (is_filled ?c)) {clear("?c")}')
    liquid_actions['dispense_from_device'] = action('dispense_from_device','?ag - agent ?d - physobj ?c - physobj',
        '(agent_at ?ag ?d) (handempty ?ag) (is_coffee_machine ?d) (can_dispense ?d) (is_powered_on ?d) (is_filled ?d) (contains_water ?d) (coffee_loaded ?d) (is_liquid_container ?c) (item_on_surface ?c ?d) (not (is_filled ?c)) (not (= ?c ?d))',
        f'(not (is_filled ?d)) {clear("?d")} (not (coffee_loaded ?d)) {clear("?c")} (is_filled ?c) (contains_coffee ?c) (contents_heated ?c)')
    # Keep the established output ordering and fingerprint without requiring
    # unsafe placeholder liquid actions in the ordinary domain.
    insert_after = {'power_off': ('fill_from_faucet', 'dispense_from_device', 'pour_into'),
                    'clean_room_floor': ('fill_device_with_water', 'pour')}
    base_actions = {x[1] for x in domain if isinstance(x, list) and x and x[0] == ':action'}
    if base_actions & liquid_actions.keys() or not insert_after.keys() <= base_actions:
        raise ValueError('Ordinary domain action boundary changed; review liquid generation')
    extended = []
    for section in domain:
        extended.append(section)
        if isinstance(section, list) and section and section[0] == ':action':
            extended.extend(liquid_actions[name] for name in insert_after.get(section[1], ()))
    domain = extended
    domain.append(action('heat_liquid_in_kettle','?ag - agent ?c - physobj',
        '(agent_at ?ag ?c) (handempty ?ag) (is_kettle ?c) (is_liquid_container ?c) (is_filled ?c) (contains_water ?c) (is_powered_on ?c) (not (contents_heated ?c))', '(contents_heated ?c)'))
    domain.append(action('heat_liquid_on_stove','?ag - agent ?c - physobj ?d - physobj',
        '(agent_at ?ag ?d) (handempty ?ag) (is_liquid_container ?c) (is_heating_container ?c) (is_filled ?c) (contains_water ?c) (item_on_surface ?c ?d) (is_cooking_surface ?d) (is_powered_on ?d) (not (contents_heated ?c)) (not (= ?c ?d))', '(contents_heated ?c)'))
    for kind in ('tea','coffee'):
        target = '(is_coffee_machine ?c)' if kind=='coffee' else '(is_liquid_container ?c)'
        domain.append(action('load_'+kind, '?ag - agent ?s - physobj ?c - physobj',
            f'(agent_at ?ag ?c) (holding ?ag ?s) ({kind}_supply ?s) (ingredient_available ?s) (imply (can_be_opened ?s) (is_open ?s)) {target} (not ({kind}_loaded ?c)) (not (= ?s ?c))',
            f'({kind}_loaded ?c) (not (ingredient_available ?s))'))
    domain.append(action('brew_tea','?ag - agent ?c - physobj',
        '(agent_at ?ag ?c) (handempty ?ag) (is_liquid_container ?c) (is_filled ?c) (contains_water ?c) (contents_heated ?c) (tea_loaded ?c)',
        '(not (contains_water ?c)) (contains_tea ?c) (not (tea_loaded ?c)) (not (water_checked ?c))'))
    domain.append(action('water_plant','?ag - agent ?c - physobj ?p - physobj',
        '(agent_at ?ag ?p) (holding ?ag ?c) (is_liquid_container ?c) (is_filled ?c) (contains_water ?c) (is_plant_receiver ?p) (not (watered ?p)) (not (= ?c ?p))',
        f'(watered ?p) (not (is_filled ?c)) {clear("?c")}'))
    domain.append(action('prepare_instant_noodles','?ag - agent ?c - physobj',
        '(agent_at ?ag ?c) (handempty ?ag) (is_liquid_container ?c) (contains_noodles ?c) (is_filled ?c) (contains_water ?c) (contents_heated ?c) (not (noodles_prepared ?c))', '(noodles_prepared ?c)'))
    domain.append(action('inspect_water_container','?ag - agent ?c - physobj',
        '(agent_at ?ag ?c) (handempty ?ag) (is_liquid_container ?c) (is_filled ?c) (contains_water ?c)', '(water_checked ?c)'))
    def dump(x): return '('+' '.join(dump(v) if isinstance(v,list) else v for v in x)+')'
    return '; Generated by scripts/build_liquid_domain.py; do not edit.\n(define\n'+'\n'.join('  '+dump(x) for x in domain[1:])+'\n)\n'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    text=generated()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text()!=text: raise SystemExit('Liquid domain is stale')
    else: OUTPUT.write_text(text)
