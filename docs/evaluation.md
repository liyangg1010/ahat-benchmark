# Evaluation protocol

The evaluation pipeline follows AHAT's `baseline/llm/run_eval_rubric.py` reviewer used for
saved GPT results, with the action/arity guard from `review_luna_benchmark.py`.
The paper-derived prompts, current domain and VAL runtime are fingerprinted
in `benchmark_manifest.json`. Version 2.3.0 uses `ahat-rubric-scene-lighting-v7` and
`ahat-v8-group-portions`: the prompts distinguish required and optional
adjacency and unified thermal processing. Pickup removes old adjacency in the domain. These prompts are
local revisions of the original paper text. [Parity evidence](validation/parity.md)
records the historical implementation comparison, not parity of the new rubric.

The current task set has 274 cases (117/65/92): 244 use the ordinary
domain and rubric, while 30 use the liquid domain and liquid rubric. Seven
unsupported liquid candidates are quarantined outside the scoring denominator.
The preceding liquid-pruning revision had 296 tasks; its retained records were
unchanged at that stage. See [liquid-v1](liquid-domain.md) for the subsequent repairs.
Both domains use revision `type-hierarchy-v1`, reserving PDDL's built-in `object`
root and declaring scene items as `small_object`. The liquid domain retains
the bottle-refill-v1 rule requiring lidded containers to be open before faucet filling.
Filling, dispensing and pouring are available only in the liquid domain; ordinary
tasks using those removed actions are rejected as unknown actions. Cleaning and
soaking with a faucet remain supported in both domains.
See [type repair and full validation](domain-types.md); re-export problems and
regenerate results with the new domain hashes.
See [bottle refill repairs and deduplication](bottle-refill.md). The liquid rubric is
`ahat-rubric-liquid-lighting-v2`. Lighting uses light_on/off and is_light_on,
including furniture lamps; no separate power state is required for lights.
D2 includes precise agent locations, synchronized room links and complete human
inventories. See [the scene and lighting repair](scene-lighting.md).
Person positions now use `person.location` or, when absent/null, the unique
physical location in normalized `on`/`in` links. A consistent room edge is a
projection of a precise position, not a second `person_at`. Ambiguous/conflicting
positions and unknown/nonphysical targets are rejected; absent evidence remains
unspecified. This restores 61 missing initial/final `person_at` facts for D1;
D2 also includes normalized `person_locations`. No dataset or domain changes
are required. Implementation fingerprints invalidate previous caches; use fresh
VAL/judge outputs after upgrading. See [FIX-020](repair-log.md#fix-020人物位置从-scene-到-pddl-的转换).

All cache consumers compare VAL plans with normalized inference actions before
reuse or judge requests, and valid cached initial states with the current scene.
Result files carry a cases-content hash; judge upstream signatures bind that hash
as well as input/protocol provenance, so changing VAL results invalidates old
judge checkpoints. These checks detect corruption/mismatches, not malicious
rewriting of both a file and its checksums.

## Deterministic validation

VAL receives a **full-scene**, deterministically sorted PDDL problem. It is
independent of the plan's mentioned entities. This matters when a negative
existential precondition depends on an otherwise unmentioned object.
Facts incompatible with domain types or PDDL identifiers are dropped and
recorded in `excluded_ill_typed_initial_facts`.

Empty and malformed plans are rejected. Before native VAL, the validator checks
action names, argument counts, object declarations and argument types, including
subtype ancestry. Objects are checked against the actual generated problem and
domain constants, with PDDL's case-insensitive matching. Unknown objects and
incompatible types return `invalid` with `invalid_action` and an `argument_error`
containing the kind, one-based argument position, parameter, argument and
expected/actual types. These deterministic plan errors receive zero and do not
count as infrastructure failures. This guard prevents native crashes or hangs
on illegal arguments.

The validator protocol is `full-scene-val-typed-arguments-v3`; use a new evaluation
output directory after upgrading. The default timeout is 10 seconds. Beyond the
prechecks, `invalid` requires a native invalid verdict; process failures without
a verdict remain `val_error`, timeouts remain `val_timeout`, and scene/problem
preparation failures remain `val_error`.

## Rubric evidence and score

Each valid plan receives four independent chat-completions calls:

| Dimension | Input | Weight |
| --- | --- | ---: |
| D1 Goal Achievement | Instruction and exact final PDDL state | 0.40 |
| D2 Intent Understanding | Instruction, inventory/location summary and plan | 0.20 |
| D3 Completeness | Instruction and plan | 0.20 |
| D4 Execution Quality | Instruction and plan | 0.20 |

The final state starts from the initial PDDL persisted by VAL and applies the
domain's simultaneous delete/add effects, including typed `forall` and pre-state conditional `when`
effects for adjacency cleanup and liquid transfer. No additional effects are
inferred by mutating the scene graph. The domain's declared semantics, including
omissions, determine D1 evidence.

Static `serves_two` / `serves_group` facts on explicitly annotated food nodes survive execution
and reach D1 through this same state path. D1 checks quantity alongside requested
processing and serving; capacity alone is not completion. All six retained
two-person/family/guest meals have a relevant food-capacity declaration. Ordinary-domain D2/D3/D4
do not receive capacity facts; the later D2 inventory/location additions described above
do not change that policy. See
[food capacity and required plan stages](group-portions-and-order.md).

D3 checks required earlier phases even when cleanup later undoes their results;
D4 checks explicitly requested or necessary order between present phases. D1
must not infer prior dinner service from a clean final table. These prompt rules
preserve existing weights and add no hard success gate. A native-valid same-final-state
counterexample verifies that D3/D4 receive distinguishing plan evidence, not that
a live judge will necessarily score it correctly.

Adjacency is symmetric and support-specific, not transitive. If the instruction
requires next-to/beside placement, merely sharing a surface or receptacle does
not satisfy that requirement; missing required adjacency prevents full D1 goal
achievement while allowing partial credit for other goals. Valid optional
adjacency is not a planning error, and its absence is not a failure. The rubric
does not award a bonus merely for using `next_to`, or let it replace requested
states and locations. D4 still assesses actual redundant actions; necessary
rearrangement and requested cleanup are not contradictions.

`reference_goal` annotations remain offline reference checks, not a binary
runtime success metric or an override of the rubric. The regression suite uses
the same goal with ordinary and adjacent placement: both pass a placement-only
goal; only adjacent placement passes an explicit adjacency goal. The native VAL
reference checker also tests all 11 annotated explicit-adjacency tasks against
valid ordinary-placement controls. [Adjacency notes](next-to.md) list coverage.

Cooking, warming and reheating share the same three appliance-specific heat
actions and single `heated` result. Food and other explicitly heatable objects
use the same processing rules. No separate doneness or initial cooked state is
modeled; `is_food` identifies food but is not required to heat other objects.
Power-on alone does not establish `heated`. Require processing only when the
instruction requests it, not merely fetching food or setting a table. There are
19 offline reference goal annotations, including the four original processing tasks
and the guest-dinner example with legal controls that omit heating and fail their
targets. Seven adopted dinner/group-meal examples also have independent outcome
checks (one additionally requires an ordered serving stage). See
[current thermal semantics](heated.md). Existing quantity and full-meal coverage
limits remain; goal reachability does not certify all annotations sufficient.
The cooking audit reports its nine historical deferred records separately from
their current repaired reference examples; none of those nine remains an
unresolved reference repair. This does not claim a complete symbolic success
definition for every natural-language instruction.

These object-processing checks do not add liquid-temperature tracking. Fill/pour
and self-heating kettle tasks retain their container/device-state abstraction;
the rubric must not demand an undeclared liquid object or temperature fact.

D3 distinguishes preparing actual edible food from dining setup. A meal request
requires making a meal ready to eat, plus serving/delivery when requested;
decorations or table setting alone score at most 0.25 for that request. Setup-only
instructions do not require food. Reasonable cold meals and prepared food remain
valid where cooking/warmth is not required. Do not invent package contents,
portions, a menu or a specific serving arrangement. Explicit diner counts are
requirements; two cups alone do not demonstrate two food servings. See the
[D3 policy and contrasting examples](d3-meal-policy.md). The scale and aggregation
weights are unchanged. This prompt revision requires fresh judge outputs;
offline tests do not establish how a live judge will apply the policy.

Replies require a nonempty rationale and exactly one score from
`{0, 0.25, 0.5, 0.75, 1}`. Boolean and arbitrary numeric scores are rejected.
D1 also requires a real boolean `critical_failure`. A critical failure caps the
weighted score at `0.2`, even if the weighted score is higher. Good/Normal/Bad
labels supplement the numeric metric.

YAML weights, cap and label thresholds are passed to the evaluator and included
in the signed protocol. Changing these settings changes the evaluation
protocol. API sampling/reasoning parameters are omitted, preserving deployment
defaults. Judge output can vary between runs even with identical input.

## Denominator and failures

All dataset cases are in the denominator. `invalid`, `missing_plan` and
`malformed_plan` receive zero. `val_timeout`, `val_error`, incomplete reviews,
API failures and malformed judge replies produce no score. A final report is
publishable only when no such system errors remain.

`final_results.json` includes per-case scores, VAL status, the publishable flag,
full-case mean and descriptive statistics across valid judged tasks. A single
run's task variation is not a confidence interval across repeated judge runs.

## Checkpoints and parallelism

Stages write atomic checkpoints after each case; judge dimensions also checkpoint
individually. Resume reuses successful dimensions and retries failed ones.
Inputs and protocol signatures include code, data, inference, domain, native
runtime, prompts, model, endpoint, scoring and upstream signatures. Changed or
unversioned checkpoints are rejected. Use a new directory after upgrades.

`--workers` controls concurrent cases, and `--dimension-workers` controls
concurrent dimensions within a case. For a single CLI run, 16 × 4 permits at
most 64 concurrent chat-completions requests. Independently launched processes
each have their own limit. Retries remain inside a dimension's worker slot.
