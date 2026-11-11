# D3 meal completeness policy

D3 policy revision: `ahat-rubric-portions-and-order-v6`, 2026-11-11
(FIX-008, updated by FIX-010 and FIX-013). The previous serves-two-v5 revision
changed only D1; the current revision explicitly assigns required-stage coverage
to D3 and required ordering to D4. D3's plan-only input still does not receive
scene portion attributes. See [capacity and plan stages](group-portions-and-order.md).

The old D3 example listed table setting as the minimum for "prepare dinner".
It left meal preparation unclear and could reward occasion-related setup while
missing actual food. The revised D3 distinguishes what the instruction requests:

- Meal preparation requires an actual edible meal ready to eat. Include serving
  or delivery when requested, including hosting a meal or providing meal service.
- Reasonable cold meals may satisfy a meal request. Thermal processing is
  required only where the instruction calls for it. Cooking, warming and
  reheating share the same heat action and heated result; no separate doneness
  state or initially cooked state is modeled. Heat-processing actual eggs
  satisfies the thermal subtask in this abstraction.
- Setting a table or creating an atmosphere does not require meal preparation
  unless the instruction also requests it. Fetching ingredients or preparing
  equipment does not require completing the meal.
- For a meal request, setup alone scores at most 0.25 in D3. It cannot receive
  the generic 0.50 minimum for progress toward the primary intent. Actual food
  preparation with omissions is assessed using the existing partial-credit scale.
- Do not invent food inside packages, food contents of empty cookware,
  portions, a mandatory menu or a particular table/dish/cutlery arrangement.
  Explicit diner counts are requirements, but two cups alone are not evidence
  of two food servings. Do not invent a number for "family" or "guests" or require
  a quantity predicate absent from the model.

The following are **manual policy examples**, not measured judge responses or
new benchmark tasks. Each completion description assumes its stated evidence is
available; no edible contents or portions are inferred from object names alone.

| Instruction | Plan coverage | D3 policy |
| --- | --- | --- |
| Prepare dinner | Only plates, candles and napkins arranged | At most 0.25; actual meal preparation is missing. |
| Set the dinner table | Requested table setting completed | Can be complete; do not add cooking or food requirements. |
| Create a dinner atmosphere | Requested lighting/decorations completed | Can be complete; do not add meal preparation. |
| Prepare breakfast and serve it | A reasonable cold meal is prepared and made available to eat | Can be complete; do not require a heat action, fixed menu or dining table. |
| Cook breakfast and serve it | Raw food packages moved to a table; stove switched on | Incomplete; neither cooking actual food nor serving a prepared meal is demonstrated. |
| Prepare a warm egg meal | Actual eggs undergo a valid heat action and are made ready to eat | Thermal subtask covered; do not add an unrepresented doneness requirement. |
| Reheat the casserole and return it | The food dish undergoes a heat action and is returned as requested | Can be complete; no initial doneness distinction is required. |
| Prepare breakfast for two | One unspecified aggregate food object and two cups arranged | Does not establish the requested food servings; do not invent portions. |
| Retrieve eggs and bread for breakfast | Requested ingredients fetched | Can be complete; the task does not request cooking or serving breakfast. |

FIX-008 changed only D3. The subsequent heated-v2 revision updates all four
prompts to the unified heat abstraction while preserving this meal/setup policy,
score values, weights and the critical-failure cap. Version and prompt hashes
are signed; use fresh evaluation outputs after upgrading. See
[current semantics and validation](heated.md).

These examples are manual policy guidance, not measured model responses.
Offline tests check protocol consistency and pipeline behavior; no live judge
calls or rescoring were run. The earlier
[D3-only checks](validation/d3_meal_policy_checks.json) remain historical.
