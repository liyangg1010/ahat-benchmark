"""Container contents invariants for the liquid domain only."""
KINDS = ('contains_water', 'contains_tea', 'contains_coffee', 'contains_other_drink')
FIELDS = (*KINDS, 'contents_heated', 'is_liquid_container', 'is_kettle', 'is_coffee_machine',
          'tea_supply', 'coffee_supply', 'ingredient_available', 'tea_loaded', 'coffee_loaded',
          'is_plant_receiver', 'watered', 'water_checked', 'contains_noodles', 'noodles_prepared')


def validate_liquid_scene(scene):
    for values in scene.values():
        if not isinstance(values, list): continue
        for obj in values:
            if not isinstance(obj, dict): continue
            states = obj.get('states') or {}
            for field in FIELDS:
                if field in states and type(states[field]) is not bool:
                    raise ValueError(f'Liquid state must be boolean: {obj.get("name")}.{field}')
            tracked = states.get('is_liquid_container', False)
            kinds = sum(bool(states.get(k)) for k in KINDS)
            if kinds or states.get('contents_heated'):
                if not tracked: raise ValueError(f'Liquid contents require a container: {obj.get("name")}')
            if tracked and (kinds != int(bool(states.get('is_filled')))):
                raise ValueError(f'Filled liquid container must have exactly one content kind: {obj.get("name")}')
            if states.get('contents_heated') and not kinds:
                raise ValueError(f'Empty container has heated contents: {obj.get("name")}')
            if states.get('noodles_prepared') and not (states.get('contains_noodles') and states.get('contains_water') and states.get('contents_heated')):
                raise ValueError(f'Prepared noodles lack hot water: {obj.get("name")}')
            if states.get('water_checked') and not (states.get('is_filled') and states.get('contains_water')):
                raise ValueError(f'Water check lacks current water: {obj.get("name")}')
