# Cooking and heating

This document records the historical cooking-v1 / goal-audit revisions. They
were superseded by [heated-v2](heated.md), which uses only heated and three heat
actions. The cooked state, separate cook actions and initial doneness distinctions
below no longer describe the active domain or rubric. Historical validation
files retain their original fingerprints.

The cooking-v1 repair introduced domain `ahat-v5-cooking-and-heating` and
rubric `ahat-rubric-cooking-v2`. It preserves adjacency consistency and the
required/optional adjacency policy. This revision changes legal actions, scene
capabilities and judge evidence; historical scores require reevaluation.
The subsequent rubric was `ahat-rubric-meal-completeness-v3`; its
[D3 meal policy](d3-meal-policy.md) clarifies meal preparation versus dining
setup while retaining these processing and adjacency rules.

The subsequent [cooking-goals-v1 audit](cooking-goal-audit.md) reviewed 27 meal
candidates, including four explicit food processing/hot-meal tasks. Only the
simple breakfast and oven reheating references are confirmed sufficient within
the symbolic model. Their goals are strengthened; reheating now uses 16 steps.
The two existing "for two" annotations remain partial checks: they do not express
portions and are not certified sufficient. FIX-009 subsequently added cooked to
the warm-brunch goal, rejecting the previously admitted heated raw eggs while
preserving its existing cooking plan. The quantity ambiguity remains separate.
The counts and validation below describe the earlier cooking-v1 repair snapshot.

## Scene attributes and results

All attributes below are explicit boolean entries in a node's `states`.
Scene-to-initial-state conversion emits the corresponding declared unary PDDL
predicates. Runtime conversion does not guess capabilities from object names.
SceneGraphManager applies processing effects back to the same boolean states.

| Predicate | Meaning |
| --- | --- |
| `is_food` | The node denotes actual food, not packaging or an empty vessel. |
| `can_be_heated` | Heating this particular object is an allowed operation. It is a capability, not a completed result. |
| `is_heating_container` | The node is suitable cookware or a heat-resistant cooking vessel/support. |
| `is_microwave` | The device supports microwave processing. |
| `is_oven` | The device supports oven processing. Bundled stove_oven nodes use this capability for their oven compartment. |
| `is_cooking_surface` | The device supports cooking on a hob, induction surface or grill. |
| `is_heating_device` | General heating capability, required together with the specific processing capability. |
| `cooked` | Food has been cooked. Cold prepared food may start cooked without being heated. |
| `heated` | The object has completed a heating operation. This boolean abstraction has no temperature or cooling dynamics. |

For example, raw eggs can have `is_food: true`, `can_be_heated: true`,
`cooked: false`, `heated: false`; a pan has `is_heating_container: true` but
not `is_food`. Egg cartons, toys and flower pots are not food. Heating may apply
to an explicitly heatable nonfood object; cooking additionally requires food.

## Actions

| Action | Arguments after agent | Placement and device conditions | Effect |
| --- | --- | --- | --- |
| `cook_with_microwave` | food, device | Inside a microwave, closed and powered | cooked + heated |
| `cook_with_oven` | food, device | Inside an oven, closed and powered | cooked + heated |
| `cook_on_heating_device` | food, cookware, device | Food on cookware, cookware on a cooking surface, powered | cooked + heated |
| `heat_with_microwave` | object, device | Inside a microwave, closed and powered | heated |
| `heat_with_oven` | object, device | Inside an oven, closed and powered | heated |
| `heat_on_heating_device` | object, cookware, device | Object on cookware, cookware on a cooking surface, powered | heated |

All require the agent at the device with an empty hand, a heatable target and
the matching device capability. Cooking requires not cooked; heating requires
not heated and preserves any cooked state. On-surface processing additionally
requires `is_heating_container` and distinct target, vessel and device.
The existing `item_on_surface food cookware` convention is retained: the
separate `item_in_receptacle` relation represents loading enclosed appliances.
The old openable/non-openable OR branch is removed. The on-device action keeps
its four-argument signature; microwave/oven actions do not take an unused vessel.

Power-on alone establishes neither processing result. Opening a powered device
cannot bypass the closed-door processing requirement. This change does not add
automatic heat transfer through fill/pour, temperature tracking or appliance
cycles; those would need a separate liquid/temperature model and protocol.

## Data changes

No task IDs, instructions, splits or task counts change: 355 tasks remain
(149 easy, 98 medium, 108 open). Explicit allowlists in
`scripts/repair_cooking.py` annotate 294 scenes (114 easy, 74 medium, 106 open).
They select semantic `type` where present, otherwise the complete name stem,
not substrings such as `pot` within `flower_pot`. Uncertain packaging and
generic serving containers are excluded. Custom scenes declare their own flags.

| Attribute | Scene count | Object count |
| --- | ---: | ---: |
| is_heating_container | 181 | 345 |
| is_food | 120 | 178 |
| can_be_heated | 142 | 232 |
| is_microwave | 92 | 101 |
| is_oven | 100 | 143 |
| is_cooking_surface | 92 | 128 |

Counts overlap. The earlier estimate of 176 cookware candidate scenes did not
include all microwave-safe dishes; the final list includes those explicit types.
Existing can_be_heated declarations are retained. Legacy is_heater flags alone
do not establish a food-processing capability; device flags are set only for
the specific appliance types listed in the repair script. Candle/shower heating
attributes cannot authorize cooking without a matching processing capability.

Four reference repairs use stable IDs:

| ID | Instruction | Repair and offline target |
| --- | --- | --- |
| `fd22ff41-4720-497c-bad3-7411b468b6cc` | Cook a simple breakfast and serve it | Add actual eggs inside egg_carton_46; retrieve, cook in pot_2, turn stove_2 off and serve on plate_48 on the dining table. Check cooked, heated and serving. |
| `4bddb476-f1ae-44e1-9558-add1571dd936` | Make a hot breakfast for two. | Cook existing eggs_116, serve with yogurt and milk, turn stove_26 off. Check cooked, heated and serving. |
| `9027ed1b-fcf9-4f17-8b39-c397d4db7563` | Prepare a warm brunch for two. | Add actual eggs inside egg_carton_139 and prepare a warm serving with the existing butter and fruit bowl. Initially required heated and serving; FIX-009 adds cooked to reject raw heated eggs. Two servings remain unrepresented. |
| `02a5f844-c663-4336-b6c9-fad5540b7cd5` | Reheat the casserole in the oven and return it | Mark this node specifically as a prepared casserole, initially cooked and cold. Insert heat_with_oven while closed and powered; require heated, returned and powered off. |

The two carton objects remain packaging and are not marked food. The other
351 reference plans and all instructions remain unchanged. No cooked/heated
goals are added to fetching, table-setting or other broadly worded meal tasks.
These are 18 total offline reference annotations, not runtime scoring overrides.
The rubric distinguishes actual processing from power operations and continues
to evaluate only the goals implied by each instruction.

Provenance remains in `hf_sync.json`, with the upstream revision/hash unchanged
and local annotation IDs/nodes, repair script hash, base-data hash and artifact
hashes recorded separately. Split versions are easy 1.5.0, medium 1.4.0, open 1.3.0.
`PYTHONPATH=src python scripts/repair_cooking.py` is a nonwriting idempotence
check; `--write` regenerates the documented snapshot and hashes.

## Verification

- 63 unit/integration tests passed. The seven cooking tests cover all six
  processing actions, food/heatability/device/cookware guards, closed-door
  processing, reheating cooked food, separate effects, scene conversion and
  processing-free negative controls.
- 355/355 reference plans valid; 18/18 annotated goals passed.
- Four legal controls omitting processing all miss their corresponding goal.
- All 83 steps of the four repaired plans agree between scene updates and PDDL
  simulation. Existing 11 adjacency controls and 61 replay steps still pass.
- [Machine reference checks](validation/cooking_v1_checks.json) record input and
  implementation hashes. The next-to-v1 validation file is a historical snapshot.
- Doctor, the offline demo, public-source/export checks and sdist/wheel inspection
  passed. An installed wheel outside the checkout passed doctor, the offline demo,
  all four repaired references/goals/controls and their 83 scene replay steps.

No live LLM rescoring was performed. Use new inference/evaluation output
directories with the revised domain, scenes and rubric.
