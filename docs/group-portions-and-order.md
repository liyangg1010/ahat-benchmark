# Food portions and required plan stages — group-portions-v1

The current unreleased 2.3.0 snapshot uses domain `ahat-v8-group-portions` and
rubric `ahat-rubric-portions-and-order-v6`. At introduction there were 339 tasks (149/98/92).
At introduction, split versions were easy 1.6.0, medium 1.5.0 and open 1.7.0.
Subsequent [liquid pruning](liquid-pruning.md) reduces the total to 296
(130/74/92), with split versions 1.7.0/1.6.0/1.7.0. All six meal annotations
below and the domain/rubric are retained; counts in this document are historical.

## Explicit food capacity

All six retained meal instructions with an explicit two-person or family/guest
requirement now have a relevant actual food node with declared capacity:

| Task ID | Original instruction | Food | Static state |
| --- | --- | --- | --- |
| `f3ee3e87-d782-4870-8ed3-2bc92f344010` | Host a cozy dinner for two tonight. | `eggs_116` | `serves_two: true` (new) |
| `0cf41a97-9f6a-4e13-8542-1def6889483d` | Host a cozy brunch for two. | `eggs_66` | `serves_two: true` (new) |
| `198fd035-6f65-4740-8b01-0643a215ccb4` | Prepare a full family breakfast service | `eggs_90` | `serves_group: true` (new) |
| `dec162ab-e453-419f-971a-2e32987350f2` | Prepare an elegant dinner for guests | `cheese_block_106` | `serves_group: true` (new) |
| `4bddb476-f1ae-44e1-9558-add1571dd936` | Make a hot breakfast for two. | `eggs_116` | `serves_two: true` (existing) |
| `9027ed1b-fcf9-4f17-8b39-c397d4db7563` | Prepare a warm brunch for two. | `breakfast_eggs_1` | `serves_two: true` (existing) |

`serves_two` declares enough of the whole food portion for two diners.
`serves_group` declares enough for the intended family/guest group of this
scenario; it does not assign a number, assert capacity for an arbitrary group,
or prove a nutritionally complete meal. Both are static local scenario design,
not amounts inferred from names, packaging or tableware. Absence means capacity
was not declared, not proof of insufficiency. Sharing a portion is allowed.

For example, the existing cheese block is actual food, so its states become:

```json
{
  "is_clean": false,
  "can_be_moved": true,
  "is_food": true,
  "can_be_heated": true,
  "heated": false,
  "serves_group": true
}
```

The cheese identity/heatability annotation is confined to this named node;
ordinary containers and other scenes are not reclassified. Other new targets
already had food identity and heatability. Each newly annotated target explicitly
starts `heated: false`; capacity does not invent completed processing or doneness.
The group size remains unspecified, matching the original instruction.

Scene booleans use the existing conversion: `(serves_group cheese_block_106)`
appears in initial PDDL and survives to final PDDL. No action produces or consumes
either capacity predicate. D1 receives and interprets both alongside food identity,
requested processing and serving/location evidence. No action or converter changes
are needed. D2's inventory summary and D3/D4's plan-only inputs still do not receive
scene capacity declarations.

Only four source scenes change. All IDs, instructions, reference plans and goals
are unchanged. In particular, the two-person brunch plan still leaves its eggs in
storage: adding capacity does not imply they were prepared or served. The four
new annotations do not certify the entire old reference plans as sufficient.
No reference goal is added to these uncertain meals.

## Checking earlier stages with D3 and D4

The judge inputs retain their existing division:

| Dimension | Evidence | Responsibility for a phased task |
| --- | --- | --- |
| D1 | Instruction + exact final PDDL | Observable final outcomes; no unsupported claims about earlier events |
| D2 | Instruction + object/location summary + plan | Interpreting the requested intent |
| D3 | Instruction + plan | Presence of every required phase, including phases later undone |
| D4 | Instruction + plan | Explicit or necessary order between phases that are present |

For "host a dinner and clean up afterward", D3 requires actual meal preparation /
food made available and subsequent cleanup coverage. Only setting/removing
tableware or moving a sponge cannot stand in for a dinner. D4 checks that the
requested cleanup follows the meal stage. Preparation cleaning may legitimately
occur before food preparation; it is not the requested post-meal cleanup.
Do not add an eating, waiting or host action that the domain does not represent.

The revised prompts make these rules explicit. A missing required phase prevents
full D3 credit; violation of required order prevents full D4 credit. Missing phases
are not automatically additional navigation inefficiency or evidence of reversed
order. Independent steps need no invented ordering. D1 is told not to infer a prior
meal merely from a clean final table and not to require temporary serving arrangements
to persist after requested cleanup. Native VAL continues to enforce action
preconditions, which is distinct from instruction-level temporal coverage.

This supplies evidence and scoring guidance, **not a hard success gate**. Weights
remain D1 0.4 and D2/D3/D4 0.2 each; there is no new cross-dimension override.
For example, if only D3 scores zero and all others score one, the total is still
0.8. A rule that missing an earlier phase makes the whole task fail would require
an explicit success/aggregation policy and reliable phase evidence; it is not
silently introduced here. LLM scores are not deterministic phase proofs.

## Verification and provenance

The scene migration is idempotent in `scripts/repair_cooking.py`;
`hf_sync.json.local_group_portions` records the four changed nodes and baseline hash.
Historical revision entries remain intact. Dataset/domain/prompt hashes and split
manifests are synchronized. D2's prompt is unchanged; D1/D3/D4 prompts change.
Use fresh evaluation outputs and updated scene inputs after upgrading.

Tests verify actual simulated D1 request delivery, native capacity-fact controls,
and preservation across scene/PDDL replay. A native-valid counterexample pair
temporarily delivers then returns an object versus omits delivery: both have the
same final state and D1 input, while D3/D4 receive different plan evidence. This
demonstrates evidence availability, not a measured judge score or a hard gate.
Current evidence: [migration checks](validation/group_portions_migration_checks.json),
[goal audit](validation/group_portions_goal_checks.json) and
[reference checks](validation/group_portions_reference_checks.json).

[Liquid instruction classification](liquid-tasks.md) is a separate read-only
audit; no liquid-temperature/content model is added by this revision.
