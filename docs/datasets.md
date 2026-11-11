# Datasets and custom inputs

The bundled release has 296 cases: easy 130, medium 74 and open 92.
The upstream snapshot is pinned to HF revision
[`44de8a66c58cfd4cea03923bed9dbb8bd69d8f85`](https://huggingface.co/datasets/SII-liyang2024/AHAT-dataset/tree/44de8a66c58cfd4cea03923bed9dbb8bd69d8f85).
Source SHA-256:
`05cb4e725b5a8a93feb8c8609c768dc7a93371fb00c076f09ddaa104bdf8fc94`.
Data license: [CC BY-NC 4.0](../licenses/CC-BY-NC-4.0).

`ahat_eval_set.jsonl` includes reference plans in `plan`, the local corrections,
pruning and 10 locally authored adjacency tasks listed below. The source SHA-256 above identifies the unmodified
348-record upstream file;
`benchmarks/hf_sync.json` records hashes of the corrected bundled artifacts.
Runtime `ahat-{easy,medium,open}/cases.json` files split by source `type`,
preserve source order, and project to `id`, `instruction` and `scene_graph`.
Each split manifest records the active runtime domain name and hash, case count,
file hash, source revision and license. The `source_domain` field records the
upstream HF domain label; it is retained for provenance and is not the runtime
evaluation protocol.
`ahat-benchmark doctor` checks these snapshots. `benchmarks/hf_sync.json`
records source provenance and all local data/manifest hashes.

The ongoing [repair log](repair-log.md) records individual fixes, validation
results and a template for future corrections.

## Liquid coverage pruning

The current [liquid-pruning-v1](liquid-pruning.md) revision removes 43 variants
from four categories: plain water 26→6, ready drinks 13→6, hot water 16→6 and
plant/vase water 12→6. The other five categories are unchanged; current liquid
coverage is 42 tasks in nine classes. A prior classification index error is
corrected without removing either affected benchmark task. All surviving source
lines, fields and order are unchanged, including all 18 reference goals.
Split versions are easy `1.7.0`, medium `1.6.0`, open `1.7.0`; open data/manifest,
domain and rubric remain unchanged. `hf_sync.json.local_liquid_pruning` records
the exact IDs, original instructions, representative mappings and snapshot hashes.
See [current instructions](liquid-tasks.md). Use the current ID set and fresh
evaluation outputs; historical aggregate scores have different denominators.

## Meal coverage pruning

The subsequent [group-portions-v1](group-portions-and-order.md) revision adds
food capacity to the other two-person and family/guest meals: four scenes change,
with no instruction/plan/goal changes. Current split versions are 1.6.0/1.5.0/1.7.0,
domain `ahat-v8-group-portions`. All six such meals now declare actual food capacity.
`serves_group` means enough for the scenario's intended group; no numeric family/guest
size is invented. [Liquid instruction classes](liquid-tasks.md) document a separate
audit of 85 instructions, including the earlier 33-task screening set; the current
liquid-pruning revision retains 42 after correcting one classification mistake.

The [meal-pruning-v1](meal-pruning.md) revision removes 16 open meal
variants from the preceding 355-task snapshot. It retains seven of the 23
remaining meal candidates plus all four processing references: meal candidates
27→11, explicit two-diner meal candidates 9→4. All surviving records, source
lines and their order are unchanged. Only open data and its manifest change;
split versions are easy `1.6.0`, medium `1.5.0`, open `1.6.0`. Domain, rubric,
easy/medium data and earlier provenance entries are unchanged. Exact IDs,
instructions and review metrics are recorded in `hf_sync.json.local_meal_pruning`
and [the pruning inventory](validation/meal_pruning_inventory.json).
This is semantic coverage reduction, not a claim of exact task equivalence or
certification that the retained meal references are complete. Use fresh inference
and evaluation outputs; 348/355-task aggregate scores are historical.

## Explicit adjacency additions

`next-to-v1` adds 10 independent tasks (6 easy, 4 medium), bringing explicit
adjacency coverage from 1 to 11 tasks. Source records identify these as
`local_authored`; their stable IDs are derived from fixed scenario names in
`scripts/next_to_cases.py`, not assigned to upstream HF provenance.
At introduction of the adjacency revision, the other 345 records kept their scenes,
instructions and plans. The subsequent cooking revision below updates capabilities
and four reference plans. The original
explicit-adjacency task `ab270610-f68d-4ccf-8ced-455a237f8dc5` additionally receives
three `reference_goal` predicates, one per requested item next to the laptop.

See [adjacency notes](next-to.md) for the scene schema, task inventory and
scoring policy. That revision used split versions easy `1.4.0`, medium `1.3.0`,
open `1.2.1` and `ahat-v4-next-to-consistency`. Upstream source and domain hashes
remain distinct from local artifact and domain hashes in `hf_sync.json`.

## Cooking and heating corrections

The earlier `cooking-v1` revision uses domain `ahat-v5-cooking-and-heating` and
split versions easy `1.5.0`, medium `1.4.0`, open `1.3.0`. It annotates explicit
food, heatability, cookware and appliance capabilities in 294 scenes
(114 easy, 74 medium, 106 open). Instructions and task IDs are unchanged.
The source JSONL changes four reference plans and adds their offline goals;
runtime splits still omit plans and goals. The two egg-carton reference repairs
add actual eggs inside the existing carton rather than treating packaging as food.

`scripts/repair_cooking.py` contains the semantic allowlists and idempotent repair;
it does not infer capabilities at runtime or assign processing goals to all meal tasks.
At that revision, the bundled set remained 355 tasks. [Cooking notes](cooking.md) describe predicates,
actions, four repaired IDs, scope and verification. `hf_sync.json.local_cooking`
records changed case IDs, nodes, reference repairs and script/base-data hashes.

The `heated-v2` revision removes the separate doneness state, migrates the
three cook reference steps to heat actions, and keeps only `heated` goals.
Initial doneness is not converted to an already-heated result. Seven scenes
change: three lose obsolete doneness flags and five legacy `is_heated: false`
attributes in four other scenes become `heated: false`. Eight source records
change in total, including the four processing references. Instructions, IDs and
355-task count remain unchanged. Its split versions were easy `1.6.0`, medium
`1.5.0`, open `1.4.0`. `hf_sync.json.local_heated` records the migration; older
revision entries retain their historical provenance. See [current semantics](heated.md).

The `serves-two-v1` revision adds explicit `serves_two: true` to the
actual egg nodes in the two hot-breakfast / warm-brunch scenes and appends the
corresponding reference goals. Instructions and plans are unchanged. Its
split versions are easy `1.6.0`, medium `1.5.0`, open `1.5.0`; domain is
`ahat-v7-serves-two`. D1 receives this static capacity in the final state;
D2/D3/D4 inputs and prompts are unchanged. See [quantity semantics and scope](serves-two.md)
and `hf_sync.json.local_serves_two` for provenance.

## Repeated-instruction pruning

The `repeated-instruction-pruning-v1` revision removes one instance each of three
repeated instructions. These were different scenes selected for reduction, not
identical records. All surviving records and their IDs remain unchanged.

| Task | Removed ID (original index) | Retained ID (original index) | Selection |
| --- | --- | --- | --- |
| Pick up a cookie | `921cf3ea-7615-4272-b50a-700cd2a39230` (45) | `b87dc669-7852-4267-8d4e-7dd2fd167f4a` (115) | Both require opening a cabinet; retain the scene with more furniture candidates. |
| Bring a glass of water | `f496da5a-81d0-4c4a-a1d0-04d61aee0e1d` (142) | `78caec8e-5332-4cd0-82f1-0550a430df58` (80) | Retain the glass on a dining table, separate from the kitchen faucet. |
| Bring instant noodles | `1e347a4c-ab36-4e80-9008-1d3e3ecaaeee` (114) | `8f039a4c-e583-4152-82be-bce9d2112dfc` (124) | Retain cabinet opening and retrieval from inside the cabinet. |

Indices above and in the sink-correction section refer to the original 348-record
source, not current JSONL line positions. Locate current records by ID.
The pruning revision used easy version `1.3.0` and reduced the set to 345 cases;
the adjacency additions brought it to 355, and meal-pruning-v1 now reduces it to
339; liquid-pruning-v1 subsequently reduces it to 296. `hf_sync.json` preserves these
transformations and upstream provenance. Previous 348- or 345-case aggregate
scores are not directly comparable to this release.
Generate inference for the current IDs and use a new evaluation output directory;
old inference files containing removed IDs are rejected.

## Sink-cleaning corrections

The `sink-cleaning-v1` revision fixes two tasks whose target sinks were already
clean. The current `sink-cleaning-v2` revision also clarifies the instructions for
54 and 70 to request all bathroom sinks, and extends task 54's reference goal and
plan to clean its four dirty bathroom sinks. Indices are zero-based in the original
source JSONL and easy split, before repeated-instruction pruning.

| Index | Case ID | Initial `is_clean: false` | `reference_goal` |
| --- | --- | --- | --- |
| 39 | `913ca94e-5eb2-44ec-8c82-867844780d57` | `sink_6` | `["(is_clean sink_6)"]` |
| 54 | `8c934a7d-48a8-4069-b6cf-3e9fb9451316` | `sink_51`, `sink_53`, `sink_54`, `sink_56` (already dirty before correction) | `["(is_clean sink_51)", "(is_clean sink_53)", "(is_clean sink_54)", "(is_clean sink_56)"]` |
| 70 | `fa3376d5-18a6-41e1-9a80-42bdb5349c75` | `sink_4`, `sink_5` | `["(is_clean sink_4)", "(is_clean sink_5)"]` |

Each reference plan now navigates to and cleans every listed sink after picking
up the original cleaning tool. `reference_goal` is an optional list of PDDL
predicates that must all hold in the final state (positive `is_clean` means true).
These three corrected records, the original explicit-adjacency record and the
10 new tasks have reference goals (14 records total). Goals are retained in the
JSONL alongside `plan`; runtime splits still expose only IDs, instructions and
scenes. They support offline validation and are not supplied to the rubric judge
or used to override its scores.
Task 54 now says "Clean all the sinks in the bathrooms." and task 70 says
"Clean all the sinks in the bathroom." Task 54's other two bathroom sinks are
already clean and remain clean after its 10-action reference plan; task 70's
6-action reference plan cleans both bathroom sinks.
Use a new evaluation output directory when adopting the corrected data.

## Reference-plan compatibility

The bundled domain is based on the `ahat_domain.pddl` snapshot shipped with the
pinned HF dataset. It includes `light_on` and `clean_item_with_faucet`, and fixes the
missing `holding` deletions in `place_in_receptacle` and
`hand_over_to_person`. All 296 reference plans validate with the current
domain: easy 130, medium 74 and open 92. Reference plans are not supplied to
the LLM reviewer.

The earlier local `ahat-v3-physobj-floor-cleaning` protocol widened the `?r` parameter of
`require_floor_cleaner` and `clean_room_floor` from `room` to `physobj`. This
preserves the attribute on carpets and mats and allows them to be cleaned with
a floor cleaner when all existing action preconditions hold. Other cleaning
actions do not enforce this attribute as an exclusive tool requirement.
The `ahat-v4-next-to-consistency` domain retained this extension and
adds universal deletion of both directions of `next_to` when either participating
object is picked up from the stated support. Unrelated adjacency is preserved.
The initial-state converter, scene updater and final-state simulator share the
same relation and effect semantics. Scene links do not infer adjacency from
co-location; initial adjacency must be declared and validated explicitly.
The current `ahat-v8-group-portions` domain retains these changes, uses the
three appliance-specific heat actions described in [heated-v2](heated.md), and
declares static [two-person and group capacity](group-portions-and-order.md).
The local domain fingerprint is recorded in `benchmark_manifest.json` and
`hf_sync.json.local_domain`, separately from the upstream domain snapshot.
Before pruning, all 348 reference plans remained valid, but 115 cases retained
additional facts in their final state, changing the D1 judge input. Re-evaluate with a new output
directory when adopting this protocol.

`validation/reference_plan_val_failures.json` is retained as historical evidence
from the previous `ahat-v1` domain and is not a failure report for this release.
Changing the domain remains a protocol change; published results must record
the domain hash and use a new output directory after an upgrade.

## Custom dataset registry

Prepare an array of cases:

```json
[{"id": "stable-id", "instruction": "Pick up the cup.", "scene_graph": {}}]
```

Replace the empty scene above with a complete scene graph; empty scenes are
rejected. Put `cases.json` and `manifest.json` in the same directory:

```json
{"case_count": 1, "data_sha256": "SHA256_OF_CASES_JSON_BYTES"}
```

Write a registry YAML with paths relative to that YAML file:

```yaml
datasets:
  my-dataset: data/my-dataset/cases.json
```

Then run:

```bash
ahat-benchmark --registry path/to/datasets.yaml val \
  --dataset my-dataset --inference path/to/inference.json \
  --output-dir outputs/my-dataset-run1
```

The same registry must be supplied to `judge`, `summarize` or `run`.
`examples/datasets.yaml` and `examples/data/demo/` provide a complete working
fixture. The public registry contains the three bundled splits; additional
local datasets can be registered separately without changing bundled data.
