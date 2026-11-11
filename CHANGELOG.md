# Changelog

## Unreleased

- Reduce four large liquid-task categories to six representatives each, removing
  43 variants. Bundled tasks become 296 (130/74/92); liquid instructions 85→42
  across nine categories. Correct one historical classification index error.
  Preserve surviving source lines, scenes, plans, goals, domain and rubric.
  Easy/medium/open versions are 1.7.0/1.6.0/1.7.0. Record exact deletion mappings
  and similarity evidence; use the current ID set and fresh evaluation outputs.

- Annotate the remaining two-person and family/guest food portions in four
  scenes. Add static `serves_group` for the intended scenario group without
  inventing a numeric group size; all six such meals now carry capacity evidence.
  Keep instructions/plans/goals unchanged. Use `ahat-v8-group-portions`,
  `ahat-rubric-portions-and-order-v6` and open split 1.7.0. D3 explicitly checks
  required earlier stages and D4 required order; weights and input formats remain
  unchanged, with no hard success gate. Audit 85 liquid instructions in nine
  classes separately; no liquid model is changed. Use fresh evaluation outputs.

- Prune 16 open meal variants by reviewed semantic coverage: retain seven of
  the 23 remaining meal candidates plus all four processing tasks. Bundled data
  becomes 339 cases (149/98/92), meal candidates 27→11 and explicit two-diner meals
  9→4. Preserve all surviving fields and source lines, domain and prompts. Open
  split is 1.6.0; record exact removal IDs, original instructions and hashes.
  Generate new inference and use fresh evaluation outputs.

- Add static `serves_two` capacity to actual egg nodes in the two hot-breakfast /
  warm-brunch scenes and their offline reference goals. D1 receives and interprets
  this quantity evidence alongside heating and serving; D2/D3/D4 are unchanged.
  Use `ahat-v7-serves-two`, `ahat-rubric-serves-two-v5` and split versions
  1.6.0/1.5.0/1.5.0 with fresh evaluation outputs. Instructions and plans are unchanged.

- Unify cooking and heating as three appliance-specific heat actions with only
  the `heated` result (`ahat-v6-heated-only`, `ahat-rubric-heated-v4`). Remove
  initial doneness flags, normalize legacy heat flags and migrate four reference
  goals and three plan steps. Preserve heatability/device/cookware guards and
  the meal/setup policy. Split versions: 1.6.0/1.5.0/1.4.0; re-evaluate with new outputs.
- Add cooked eggs to the warm-brunch reference goal, rejecting the legal
  heat-only raw-egg counterexample. The existing cooking plan reaches the
  stronger goal; the two-serving requirement remains outside this partial check.
- Clarify D3 meal preparation in `ahat-rubric-meal-completeness-v3`: require an
  edible meal, serving where requested and the explicit diner count; accept
  reasonable cold meals without inventing cooking, menu or place-setting rules.
  Table/ambience setup alone scores at most 0.25 for a meal request. Preserve
  setup-only tasks and reject judge checkpoints from the previous prompt policy.
- Audit 27 meal candidates, including four explicit cooking/hot-food tasks.
  Strengthen the two confirmed sufficient reference goals; simplify oven
  reheating from 19 to 16 steps. Preserve 25 uncertain tasks, document the
  portion-model gap and a raw-egg counterexample to the old warm-brunch goal.
  Reference goals remain offline sufficient witnesses, not required solutions.
- Split microwave, oven and stovetop cooking in `ahat-v5-cooking-and-heating`.
  Require explicit food, heatability, appliance and cookware capabilities;
  processing in closed powered appliances now works. Add separate heat actions:
  cooking sets cooked and heated, while heating alone does not imply cooked.
- Annotate capabilities in 294 scenes and repair four processing references,
  including actual egg objects instead of egg cartons. Keep all 355 task IDs and
  instructions. Update split versions, provenance and `ahat-rubric-cooking-v2`;
  preserve the required/optional adjacency policy. Re-evaluate in a new directory.
- Validate plan object declarations and inherited parameter types before native
  VAL. Unknown objects and incompatible types now return structured `invalid`
  results and score zero, rather than becoming system errors. Preserve actual
  process/timeout failures; upgrade the validator protocol to
  `full-scene-val-typed-arguments-v3` and use a new evaluation output directory.
- Prepare 2.3.0 with `ahat-v4-next-to-consistency` and `ahat-rubric-next-to-v1`.
  Normalize and validate undirected, support-specific scene adjacency; remove
  both directions on pickup in VAL, scene updates and typed universal-effect
  simulation. Dictionary links now reach the judge inventory summary.
- Require adjacency only where requested. Valid optional next-to placement is
  neither an error nor an automatic bonus; requested rearrangement/cleanup is
  not self-contradiction. These are local revisions of the paper prompts.
- Add 10 locally authored tasks (6 easy, 4 medium), with stable IDs and reference
  goals, plus goals for the original explicit-next-to task. The bundled set is
  now 355 cases (149/98/108), with 11 explicit-adjacency tasks. Add native VAL
  goal controls and scene/PDDL replay checks; preserve upstream provenance.
  Use a new output directory and regenerate inference for the new task set.
- Prune one instance each of the repeated cookie, water-delivery and instant-noodle
  instructions. The bundled set now has 345 cases (easy 143, medium 94, open 108),
  with easy snapshot version 1.3.0. Record removed/retained IDs and original source
  indices in `hf_sync.json`; surviving records are unchanged. Earlier task indices
  below refer to the 348-record snapshot. Use a new evaluation output directory.
- Clarify tasks 54 and 70 to request all bathroom sinks. Extend task 54's
  reference goal and plan to clean all four dirty bathroom sinks; synchronize
  instructions, easy snapshot version 1.2.2 and `sink-cleaning-v2` artifact hashes.
- Correct sink-cleaning cases at zero-based indices 39 and 70: initialize the
  requested sinks as dirty, add reference goals, and complete their reference
  plans. Update the easy snapshot and artifact hashes while preserving upstream
  provenance. Use a new evaluation output directory for the corrected scenes.
- Introduce the `ahat-v3-physobj-floor-cleaning` domain protocol: widen
  `require_floor_cleaner` and the `clean_room_floor` target from `room` to
  `physobj`, preserving carpet and mat attributes and allowing floor-cleaner
  actions on those objects. Existing tool and state preconditions still apply.
- Update the domain fingerprint and validation tests. Use a new evaluation
  output directory; retained attributes change the final-state judge input.
- Align all bundled split manifests with the active domain name and fingerprint;
  retain the upstream HF domain label separately for provenance.
- Sync the domain provenance to the current HF dataset revision while keeping
  the evaluation case snapshot pinned to its original revision.

## 2.2.0 — 2026-10-23

- Synchronize the bundled PDDL domain with `ahat_domain.pddl` from the pinned
  HF dataset revision.
- Remove stale `holding` facts when placing an object in a receptacle or
  handing it to a person, and require a nonempty hand for hand-dependent
  actions.
- Add the upstream `light_on` and `clean_item_with_faucet` actions and their
  predicates. All 348 bundled reference plans now validate.

## 2.1.0 — 2026-10-14

- Package all registered datasets, configuration, domain, prompts and VAL assets
  in a Linux x86-64 wheel. Installed evaluation works outside a source checkout.
- Require an explicit judge endpoint; remove the internal serving address from
  public configuration. Support a working-directory `.env` and model override.
- Expose custom dataset registries, case workers and dimension workers in the CLI.
- Add an offline end-to-end example, contribution guide, licensing, citation,
  release checks and CI. Archive local audit tools and experimental materials.
- Keep the audited full-scene validation, prompts, scoring and final-state
  computation from 2.0.0. Data and VAL/domain/prompt bytes are unchanged.

## 2.0.0 — 2026-10-14

- Pin the 348-case HF evaluation data at
  `44de8a66c58cfd4cea03923bed9dbb8bd69d8f85`.
- Match the audited AHAT reviewer: four original paper prompts, strict scores,
  weights `0.4/0.2/0.2/0.2`, critical-failure cap `0.2`, deterministic full-scene
  VAL and exact simultaneous STRIPS state updates.
- Sign inputs and protocols, checkpoint individual dimensions and distinguish
  infrastructure errors from invalid plans.
- Reject unknown actions and wrong argument counts before calling native VAL.
- Verify parity on 348 reference plans and 696 saved GPT plans, with fresh
  ds-v4.1 review. See [validation evidence](docs/validation/parity.md).
