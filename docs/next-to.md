# Adjacency representation, tasks and judging

Version 2.3.0 keeps `next_to` as a supported relation and repairs its lifecycle.
It introduces `ahat-v4-next-to-consistency` and `ahat-rubric-next-to-v1`; earlier
scores and parity reports describe earlier protocols.
The subsequent `ahat-v5-cooking-and-heating` / `ahat-rubric-cooking-v2` revision
preserves this adjacency contract; its current validation is recorded in
[cooking notes](cooking.md). The linked next-to-v1 evidence remains the original
snapshot and is not a fingerprint of the later cooking implementation. The
current [heated-v2 domain](heated.md) also preserves this adjacency contract.

## Scene and PDDL contract

Adjacency belongs in `links`, not a boolean in an object's `states`:

```json
{
  "links": [
    ["room_1", "table_1", "in"],
    ["table_1", "cup_1", "on"],
    ["table_1", "plate_1", "on"],
    {"relation": "next_to", "obj1": "cup_1", "obj2": "plate_1", "location": "table_1"}
  ]
}
```

This fragment requires declarations for the named room, table and objects in a
complete scene. List-form `on` / `in` links and equivalent dictionary links
`{"relation": "on", "from": "cup_1", "to": "table_1"}` may coexist.
Adjacency requires the dictionary form with all three participants; a legacy
three-element list cannot identify its support and is rejected explicitly.

The normalizer stores one undirected link in canonical object-name order and
deduplicates reverse duplicates. The initial-state converter emits both:

```lisp
(next_to cup_1 plate_1 table_1)
(next_to plate_1 cup_1 table_1)
```

Both objects must be declared physical objects, distinct from each other and
from the support. They must share either the stated surface or the stated
receptacle, and neither may be held. Furniture being in a room does not count
as being inside a receptacle. Invalid initial claims are rejected rather than
silently dropped. Sharing a support does not create adjacency; adjacency is
symmetric and is not transitive.

`pick_from_surface` and `pick_from_receptacle` universally delete both directions
of every adjacency involving the picked object at that support. They preserve
unrelated pairs. Ordinary placement does not restore an old relation;
`place_next_to_surface` / `place_next_to_inside` establish the requested pair.

Native VAL, the Python final-state simulator and SceneGraphManager use these
same effects. Typed universal deletion is grounded from the complete declared
object universe, not from the objects mentioned in the plan. SceneGraphManager
validates complete action updates; legacy callers applying an action's effects
separately may pass through temporary intermediate states, but converting a
scene to an initial PDDL problem validates the final scene again. Conditional
`when` and numeric effects remain unsupported by the Python effect interpreter.

The D2 scene summary accepts both link formats and includes declared initial
adjacency. D1 receives the final PDDL state after deletions and additions.

## What affects task achievement

| Instruction | Ordinary placement on the correct support | Valid adjacent placement on the correct support |
| --- | --- | --- |
| Put the cup on the table | Satisfies the placement goal | Also satisfies it; adjacency is not an error |
| Put the cup next to the plate on the table | Does not satisfy the full goal | Satisfies the stated spatial goal |
| Prepare dinner / a movie night / guests | Assess the actual core goals | Assess the same core goals; no automatic adjacency bonus |

An extra relation does not make a valid plan wrong. Relocating the wrong object,
violating a requested location or missing another goal may still be wrong,
irrespective of whether a `place_next_to` action was used. Missing explicitly
required adjacency prevents full D1 goal credit, but other achieved goals can
still earn partial credit under the existing rubric. The critical-failure rule,
dimension weights and score scale are unchanged.

D2 and D3 follow the same distinction between required and optional adjacency.
D4 judges actual inefficiency, not the action name: adjacent placement can
replace ordinary placement without adding a step. Requested rearrangement or
cleanup is not self-contradiction. A temporary arrangement that must later be
cleaned up should not be required to remain in the final state; D2–D4 have the
plan as evidence of intermediate work.

`reference_goal` is an offline annotation, not an extra planner input or a
deterministic override of runtime rubric scores. These changes revise the
rubric instructions; offline tests do not establish a judge model's empirical
compliance or the size of historical score changes.

## Explicit task coverage

Ten independent locally authored tasks extend explicit adjacency coverage
from 1 to 11 of 355 cases. They are focused capability tests, not a claim of
natural task-frequency balance. Existing scenes, instructions and reference
plans are preserved. The original laptop task additionally receives reference
goals matching its already explicit instruction.

| Scenario | Split | ID | Reference actions | Coverage |
| --- | --- | --- | ---: | --- |
| Cup and plate | easy | `ce1d381a-2c02-5720-bd6f-bb4cbec0bc7e` | 4 | Move to another surface and establish a pair |
| Book and lamp | easy | `66405407-b3f4-549d-bec3-dc68b8fa5813` | 4 | Named target/reference with distractor object |
| Towel and soap | easy | `cc6ac010-2c28-55cb-8a12-5c5b0aa07b75` | 4 | Bathroom shelf placement |
| Pen inside drawer | easy | `101df926-f674-57ac-96b1-ffc6111e6e21` | 7 | Open, place adjacent inside, close |
| Preserve existing pair | easy | `1277c042-3a66-5c9d-b6b4-7e201d28b62f` | 4 | Keep initial adjacency while adding another pair |
| Replace old neighbor | easy | `01cf3cd4-5412-5d0c-ab92-c92faf724386` | 4 | Remove old pair, establish new pair on another support |
| Two required neighbors | medium | `6eb04295-170f-5fe1-b4ef-b80b5c493c66` | 8 | Two separate objects each beside a fixed reference |
| Reestablish pair on new support | medium | `815eae12-96e6-51a7-a056-34cd118ace9b` | 8 | Move both initially adjacent objects and rebuild the relation |
| Change receptacle and neighbor | medium | `507931f2-3566-57de-a6f3-6b8e00363df0` | 7 | Remove adjacency inside one receptacle and establish another |
| Surface and receptacle goals | medium | `3af07561-c24f-5819-9671-5b552fbdbe22` | 11 | Conjunction across both placement kinds |
| Existing laptop setup | easy | `ab270610-f68d-4ccf-8ced-455a237f8dc5` | 32 | Three requested items each beside the laptop |

`scripts/next_to_cases.py` deterministically reproduces the ten local records,
including initial links, complete plans and goals. They are identified as
`local_authored` in the JSONL and in `hf_sync.json.local_additions`, under the
bundled data's CC BY-NC 4.0 license. They are not attributed to the pinned
upstream HF file. Runtime splits retain only ID, instruction and scene.

## Validation and upgrades

Run from a source checkout:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/check_reference_plans.py
PYTHONPATH=src python -m ahat_benchmark doctor
python scripts/check_release.py
```

The native reference checker verifies all 355 plans, annotated goals for 14
records, and ordinary-placement controls for all 11 explicit-adjacency tasks.
Those control plans remain action-valid but fail the explicit adjacency goals.
It also compares scene-to-PDDL round trips against exact simulation after every
step of the ten new reference plans. Unit tests separately establish that
ordinary and adjacent placement both satisfy a placement-only goal, and cover
symmetry, invalid initial claims, pickup cleanup and restoration behavior.

[Offline validation evidence](validation/next_to_v1_checks.json) records input
hashes and results. Comparing the original 345 reference plans under the old
and new domains leaves 338 final states identical; 7 differ only by deletion
of old adjacency facts. This also catches relations left behind after an object
is picked up and eventually returned to the same support, which a co-location
check alone would miss.

No LLM scores or new algorithm rankings are inferred from
these checks. Use current task IDs and a new evaluation output directory after
the data/domain/rubric upgrade; old 348- and 345-case aggregate scores are not
directly comparable to the 355-case release.
