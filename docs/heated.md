# Unified thermal processing — heated-v2

The heated-v2 revision introduced domain `ahat-v6-heated-only` and
rubric `ahat-rubric-heated-v4`. The current 2.3.0 development snapshot adds
[two-person/group capacity and plan stages](group-portions-and-order.md) with
`ahat-v8-group-portions` and `ahat-rubric-portions-and-order-v6`, retaining
the thermal semantics below.
Cooking, warming and reheating share one
result, `heated`, for food and other explicitly heatable objects. There is no
separate doneness predicate or initial doneness classification.

## State and actions

Scene nodes declare boolean attributes in `states`. Initial-state conversion
emits the corresponding unary predicates; scene updates write heat effects back
to the same `heated` field.

| Attribute | Meaning |
| --- | --- |
| `heated` | The object has completed thermal processing in this abstraction. |
| `can_be_heated` | Processing this object is allowed; a capability, not a result. |
| `is_food` | Descriptive food identity. Used to interpret food tasks, not to restrict heating to food. |
| `is_heating_container` | Suitable cookware/support for processing on a cooking surface. |
| `is_microwave`, `is_oven`, `is_cooking_surface` | Specific appliance capability. |
| `is_heating_device`, `is_powerable` | General appliance capabilities. |

| Action | Arguments after agent | Required placement/device state | Result |
| --- | --- | --- | --- |
| `heat_with_microwave` | object, device | Inside a matching closed, powered microwave | heated |
| `heat_with_oven` | object, device | Inside a matching closed, powered oven | heated |
| `heat_on_heating_device` | object, cookware, device | Object on suitable cookware, cookware on a powered cooking surface | heated |

All require an empty hand, the agent at the device, an explicitly heatable
target not already heated, and distinct target/device (also distinct cookware
for stovetop processing). The two enclosed-appliance actions require an openable
device with its door closed. Loading/unloading still uses the normal placement
and pickup actions. Stovetop processing retains the food/object-on-cookware
convention used by the benchmark.

For example:

```lisp
; Actual eggs are already on the pot; the pot is on the stove.
; The agent is at the stove with an empty hand.
(power_on agent_0 stove_16)
(heat_on_heating_device agent_0 breakfast_eggs_1 cooking_pot_52 stove_16)
(power_off agent_0 stove_16)
```

After processing, `(heated breakfast_eggs_1)` is true. This is sufficient for
the thermal subtask in a cooking instruction; do not demand an additional
doneness result. A nonfood target uses the same action if explicitly heatable.
Food packaging is not the food itself: heating packaging does not establish
that an actual food node was processed.

Power-on alone does not establish heated. Shutdown, pickup or serving do not
clear it. There is no automatic cooling, continuous temperature, liquid contents
or transfer of heat through fill/pour. A true initial heated state can represent
an already processed object; the supplied four processing references all start
their targets with heated false. A second heat action is blocked while the
result remains true; the model does not track repeated heating cycles.

## Migration and task goals

The six old cook/heat actions become the three heat actions above. The separate
`cooked` predicate is removed, including initial scene flags and reference
goals. Old cook reference steps become the corresponding heat steps. The
casserole food node retains its name and uses type `casserole_dish`; it has no
initial doneness classification. Initial cooked flags are **not** converted to
heated true. Five legacy `is_heated: false` fields become `heated: false`.

Eight source records change (easy 1, medium 4, open 3): seven scenes and the four
processing reference goals, with overlap. Three reference plans rename one cook
step each; the oven plan already uses heat and remains unchanged. All 355 IDs,
instructions, splits and task counts remain unchanged. At this revision, split
versions were easy 1.6.0, medium 1.5.0, open 1.4.0; serves-two-v1 subsequently
updates open to 1.5.0. The package remains unreleased 2.3.0.

The simple-breakfast and oven-return reference targets remain sufficient
witnesses within this symbolic model, not necessary goals. Their processing
condition is heated, together with the serving/location/shutdown conditions.
For the oven task, the only processing device is the fixed kitchen oven, so
achieving heated establishes that it was used before returning the dish.
At heated-v2, two-person breakfast/brunch targets were partial because portions
were not represented. The subsequent [serves-two-v1](serves-two.md) revision
explicitly declares two-serving capacity on their egg nodes and adds it to the
targets. It retains the processing/serving requirements and adds no liquid model.

FIX-009's raw-egg heat-only counterexample belonged to the old distinction and
is retired: a valid heat action now completes the thermal subtask for eggs.
Omitting processing entirely must still fail the reference goals. The
[meal versus setup policy](d3-meal-policy.md), instruction-based adjacency,
and all existing appliance/cookware guards are retained. A cold meal is allowed
when processing is not requested; table setting alone does not complete a meal.

## Verification and provenance

The subsequent [meal-pruning-v1](meal-pruning.md) snapshot contains 339 tasks
and retains all four processing references; counts below are heated-v2 history.

`scripts/repair_cooking.py` is the idempotent migration/annotation script.
Without `--write` it reports proposed changes. `hf_sync.json.local_heated`
records the baseline source hash, affected records, script hashes and references.
Earlier cooking/goal repair entries and validation artifacts remain historical,
including the removed doneness model. They do not describe current behavior.

```sh
PYTHONPATH=src python scripts/repair_cooking.py
PYTHONPATH=src python scripts/audit_cooking_goals.py
PYTHONPATH=src python scripts/check_reference_plans.py
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m ahat_benchmark doctor
python scripts/check_release.py
```

Heated-v2 machine evidence: [goal audit](validation/heated_v2_goal_checks.json) and
[reference checks](validation/heated_v2_reference_checks.json). Use fresh
inference/evaluation outputs for the revised actions, scenes, domain and rubric.
Offline validation does not measure judge compliance; no live LLM rescoring or
publication is performed as part of this revision.

69 tests passed; all 355 references are legal and all 18 annotated goals are
reached. Four processing-omission controls and eleven adjacency controls pass;
80 thermal-reference steps and 61 adjacency steps agree between scene updates
and PDDL execution. Source doctor, the offline demo, sdist/wheel inspection and
an isolated installed-wheel check pass. The installed wheel also passes the four
processing goals and all 80 scene replay steps. See the
[migration/build record](validation/heated_v2_migration_checks.json).
