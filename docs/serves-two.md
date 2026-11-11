# Explicit two-serving capacity — serves-two-v1

The serves-two-v1 snapshot introduced domain `ahat-v7-serves-two` and
rubric `ahat-rubric-serves-two-v5`. Thermal processing still uses only `heated`;
see [thermal semantics](heated.md). This revision adds quantity evidence to D1.

## Scene representation and meaning

An actual food node can declare:

```json
{
  "name": "breakfast_eggs_1",
  "type": "eggs",
  "states": {
    "is_food": true,
    "can_be_heated": true,
    "heated": false,
    "serves_two": true
  }
}
```

`serves_two` means the whole food object contains enough food for two diners.
It is a static scenario declaration: actions neither create nor consume this
capacity. It does not describe grams, separate portions, ingredients or nutritional
completeness. It does not mean the food is heated, prepared or served. Shared
serving is allowed; two food nodes, plates or a splitting action are not required
unless requested. False or absent values do not emit a positive fact; absence
means undeclared capacity, not proof of a single serving.

The domain declares `(serves_two ?o - physobj)`. Existing boolean-state conversion
emits `(serves_two breakfast_eggs_1)` in the initial PDDL; execution preserves it,
and D1 receives it in the exact final PDDL state alongside facts such as
`(heated breakfast_eggs_1)` and the food's serving location. No separate converter
or action effect is required. Custom scenarios should annotate actual food,
not infer capacity from packaging, plural names or tableware counts.

## Annotated tasks

Current [group-portions-v1](group-portions-and-order.md) extends this to all
six retained two-person/family/guest meal tasks, with open version 1.7.0,
domain `ahat-v8-group-portions` and rubric `ahat-rubric-portions-and-order-v6`.
The original two annotations and processing goals below remain intact.

Subsequent [meal-pruning-v1](meal-pruning.md) keeps both tasks below and reduces
the overall set to 339 (149/98/92), with open version 1.6.0. Counts and checks
in this document describe the preceding serves-two-v1 snapshot.

| Task ID | Original instruction | Food with `serves_two: true` |
| --- | --- | --- |
| `4bddb476-f1ae-44e1-9558-add1571dd936` | Make a hot breakfast for two. | `eggs_116` |
| `9027ed1b-fcf9-4f17-8b39-c397d4db7563` | Prepare a warm brunch for two. | `breakfast_eggs_1` |

These are explicit local scenario revisions authorized to supply the missing
quantity model, not facts recovered from upstream scenes. Only these two source
records change: one food attribute and one additional reference-goal conjunct
per task. Instructions and plans remain unchanged; both plans already heat the
eggs and place them on a dining table. No quantities are assigned to accompanying
milk, yogurt, butter, fruit-bowl contents or other meal candidates. The task count
remains 355 (149/98/108); split versions are 1.6.0/1.5.0/1.5.0.

D1 explains quantity, processing and serving separately and gives no bonus where
diner count is irrelevant. D2's inventory summary, D3's and D4's plan-only inputs,
and their three prompts are unchanged. They do not automatically receive this
capacity evidence. The shared protocol version and signed hashes change; use
fresh evaluation output directories after upgrading.

## Reference checks and limitations

The two reference targets gain `(serves_two FOOD)`; all other conjuncts remain
intact. Native goal checks verify both plans reach their targets. Removing the
capacity declaration keeps the plan legal but makes its target fail. Omitting
heating or serving must also fail: static capacity alone cannot complete a task.
Reference goals remain offline checks, not runtime scoring overrides or necessary
solutions. This resolves these two tasks' quantity-evidence gap; it does not
certify other broad meal instructions or enlarge the historical two-task manually
certified goal inventory.

The idempotent `scripts/repair_cooking.py` writes annotations and manifests;
`hf_sync.json.local_serves_two` records the baseline hash, exact food-node mapping,
semantics and script hashes. Earlier records remain historical. Current evidence:
[goal audit](validation/serves_two_goal_checks.json),
[reference checks](validation/serves_two_reference_checks.json) and
[migration checks](validation/serves_two_migration_checks.json).

Tests verify actual D1 request content with a simulated client, native goal
controls, and capacity preservation through scene/PDDL replay. These establish
evidence delivery and symbolic behavior; no live judge scores were measured.
