# AHAT Benchmark

Standalone evaluation of household robot plans with **VAL validation** and the
**four-dimension AHAT LLM rubric**. It includes the evaluation data, PDDL domain,
paper-derived prompts with an explicit adjacency policy and a pinned Linux VAL runtime.

[Project page](https://tgpo2026.github.io/TGPO/) ·
[Paper](https://arxiv.org/html/2602.12244v2) ·
[Dataset](https://huggingface.co/datasets/SII-liyang2024/AHAT-dataset) ·
[Evaluation protocol](docs/evaluation.md) ·
[Validation evidence](docs/validation/parity.md) ·
[TGPO paper version lock](docs/reproducibility/tgpo-paper.md)

## Released versions

| Use | Tag | Tasks (easy / medium / open) |
| --- | --- | --- |
| Current benchmark | [`v2.3.0`](https://github.com/liyangg1010/ahat-benchmark/releases/tag/v2.3.0) | 274 (117 / 65 / 92) |
| TGPO paper reproduction | [`paper-tgpo-v1`](https://github.com/liyangg1010/ahat-benchmark/releases/tag/paper-tgpo-v1) | 348 (146 / 94 / 108) |

For the 274-task snapshot, use `git checkout v2.3.0`. Its dataset, domains and
rubric have changed since the paper snapshot; aggregate scores are not directly
comparable. See [v2.3.0 release notes](docs/releases/v2.3.0.md).

## TGPO paper reproduction

The results reported in the TGPO paper use the immutable
`paper-tgpo-v1` snapshot at commit
`fafa4624cf4e99c4af10d1738d51fc9cd97e91fb`. Reproduce those results from a
clean checkout with:

```bash
git checkout paper-tgpo-v1
```

The `main` branch remains the active development branch for
`ahat-benchmark`; later changes do not change the paper snapshot. See the
[version lock](docs/reproducibility/tgpo-paper.md) for the dataset revision,
domain, validator, prompts and evaluation protocol used by this snapshot.

## Install

Use **Python 3.10+ on Linux x86-64**, with **glibc 2.34+** and a C++ runtime
providing `GLIBCXX_3.4.29` (for example, Ubuntu 22.04+ with `libstdc++6`).
From this repository:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
ahat-benchmark doctor
```

For a regular installation, use `python -m pip install .` or install a built
wheel. Registered data, configuration, prompts, domain and VAL are included;
evaluation also works outside the repository directory.

## Offline example

Run a complete two-case example without an API or credentials:

```bash
python examples/offline_demo.py
```

The example calls the real VAL runtime, then supplies **mock judge replies**.
One plan is valid and one is blocked by the full scene. It checks all four
rubric dimensions, the zero for the invalid plan, and the full-case denominator.
Its synthetic score is `0.5`; this is a software example, not a model result.
Outputs are written to `outputs/offline-demo/`.

## Evaluate model plans

Copy `.env.example` to `.env` in your working directory and fill in your
OpenAI-compatible chat-completions endpoint and key:

```dotenv
RUBRIC_EVAL_OPENAI_BASE_URL=https://your-endpoint.example/v1
RUBRIC_EVAL_OPENAI_API_KEY=your-api-key
RUBRIC_EVAL_MODEL=ds-v4.1-flash-w8a8
```

The judge model must be available at your endpoint. Sampling and reasoning
parameters use the API defaults. Shell variables override `.env`.
`API_BASE_URL`, `INF_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_API_KEY` and `API_MODEL`
are also accepted. No internal endpoint or credential is supplied by this repo.

Evaluate an inference file whose IDs cover the chosen split:

```bash
ahat-benchmark run \
  --dataset ahat-easy \
  --inference path/to/inference.json \
  --output-dir outputs/easy-run1 \
  --workers 16 --dimension-workers 4
```

This configuration permits up to **64 simultaneous judge requests** in one run
(16 cases × 4 dimensions). The default is 8 cases × 4 dimensions = 32.

Stages can also be run separately in the same output directory:

```bash
ahat-benchmark val --dataset ahat-easy --inference path/to/inference.json --output-dir outputs/easy-run1
ahat-benchmark judge --dataset ahat-easy --inference path/to/inference.json --output-dir outputs/easy-run1
ahat-benchmark summarize --dataset ahat-easy --inference path/to/inference.json --output-dir outputs/easy-run1
```

`val` and `summarize` do not make API calls. See `ahat-benchmark --help` and
`ahat-benchmark run --help` for options. Custom `--config` and `--registry`
arguments go **before** the subcommand; paths in those YAML files are resolved
relative to each YAML file.

## Input format

Inference is a JSON array or an object containing `results`:

```json
{
  "meta": {"model": "your-planner", "method": "your-method"},
  "results": [
    {"id": "dataset-case-id", "plan": ["(navigate agent_0 room_1 cup_1)"]}
  ]
}
```

Use the exact case IDs and entity names from the selected dataset. The example
above illustrates the format; it is not a complete split submission.
Plans can be lists of action strings or newline-separated strings. Duplicate,
unknown or missing IDs are rejected; `val` and `run` support `--allow-missing`
when intentionally scoring absent plans as zero. The
[JSON Schema](schemas/inference.schema.json) documents both input forms.

An optional planning example can generate your inference file:

```bash
python scripts/generate_inference.py --dataset ahat-easy --limit 0 --model YOUR_PLANNER_MODEL
```

`--limit 0` covers the entire split. The default one-case run is a connectivity
example and does not cover the full evaluation set.
The example selects each task's domain and saves its ID/hash with the plan.
It generates a complete plan in one request; it is not the historical stepwise
GPT Direct protocol. See [current readiness and retest notes](docs/benchmark-recap-20261112.md).

## Data and metric

| Dataset | Cases |
| --- | ---: |
| `ahat-easy` | 117 |
| `ahat-medium` | 65 |
| `ahat-open` | 92 |
| Total | **274** |

The current snapshot uses two task-bound domains: 244 ordinary cases and 30
liquid cases. Seven unsupported cases are archived outside the scored splits.
See [liquid modeling and migration](docs/liquid-domain.md) for the exact inventory,
limitations and reference-free inference export. Generation and evaluation must
use each task's declared domain; liquid results require its ID and SHA-256.
The current [scene-lighting-v1 repair](docs/scene-lighting.md) preserves multi-item
deliveries, normalizes lighting and agent room links, repairs coffee placement and
object names, and strengthens cache binding. Spatial-cycle prevention is deferred.
The subsequent [bottle-refill-v1 repair](docs/bottle-refill.md) keeps two of four
water-bottle tasks and requires opening lidded containers before faucet filling
in the liquid domain. Reference plans include opening before pickup.
The ordinary domain retains the `ordinary-core-v1` boundary: five filling/dispensing/pouring
actions are exclusive to the liquid domain. That revision preserved all 287 task
records and the liquid domain. See [FIX-021](docs/repair-log.md#fix-021普通-domain-移除液体制作与转移动作);
regenerate ordinary-domain plans against the new fingerprint and use fresh evaluation outputs.
Both domains now use [type-hierarchy-v1](docs/domain-types.md): the built-in
`object` root is distinct from `small_object`, with no type inheritance cycles.
All 274 reference plans and 4,107 replay steps pass. Re-export inference inputs
and use the new domain hashes for both ordinary and liquid tasks.

Data derive from HF revision
[`44de8a66c58cfd4cea03923bed9dbb8bd69d8f85`](https://huggingface.co/datasets/SII-liyang2024/AHAT-dataset/tree/44de8a66c58cfd4cea03923bed9dbb8bd69d8f85),
with documented local sink-cleaning corrections, repeated-instruction pruning
and eight active locally authored adjacency tasks (ten originally added). [Meal pruning](docs/meal-pruning.md)
removes 16 overlapping open meal variants, retaining seven representatives and
all four processing references. [Liquid pruning](docs/liquid-pruning.md) removes another 43
similar variants, keeping six representatives in each of four large liquid
categories. [Current liquid classes](docs/liquid-tasks.md) list 42 retained tasks.
[Easy pruning](docs/easy-pruning.md) archives 13 overlapping easy variants, yielding
117/65/92 tasks. Nine tasks explicitly require
next-to placement. [Adjacency notes](docs/next-to.md) explain scene representation,
task coverage and required versus optional adjacency.
`benchmarks/ahat_eval_set.jsonl` retains reference plans and the corrected tasks'
reference goals; runtime
split files expose only IDs, instructions and scenes. Hashes and source
provenance are bundled. [Dataset notes](docs/datasets.md) record the domain
snapshot used by this release and explain custom registries.

| Dimension | Weight |
| --- | ---: |
| D1 Goal Achievement | 0.40 |
| D2 Intent Understanding | 0.20 |
| D3 Completeness | 0.20 |
| D4 Execution Quality | 0.20 |

Scores must be `0`, `0.25`, `0.5`, `0.75` or `1`. D1 critical failure caps the
weighted total at `0.2`. VAL uses a deterministic full scene; D1 receives the
exact final state derived from the validated initial PDDL and domain effects.
The `ahat-rubric-scene-lighting-v7` rubric requires adjacency when the instruction
requires it. Valid optional adjacency is neither an error nor an automatic bonus.
The `ahat-v8-group-portions` domain removes old adjacency on pickup and
uses three appliance-specific heat actions. Cooking, warming and reheating all
produce the single `heated` result for food or other explicitly heatable objects.
No separate doneness state is modeled. Switching a device on is not processing
completion. See [thermal-processing notes](docs/heated.md).
D1 also receives explicit `serves_two` / `serves_group` food capacity for all
six retained two-person / family / guest meals. D3 checks required earlier stages,
and D4 checks requested ordering. Capacity does not replace preparation or serving;
see [portions and plan stages](docs/group-portions-and-order.md).
D3 distinguishes preparing an edible meal from setting a table or atmosphere.
For meal preparation, setup alone scores at most 0.25; reasonable cold meals are
allowed when thermal processing is not required. See [meal policy](docs/d3-meal-policy.md).

The split score is `sum(case scores) / all split cases`. Invalid, malformed and
empty plans score zero. Infrastructure failures and failed judge calls remain
unscored and make the report non-publishable.

## Results and recovery

Each run writes `val_results.json`, `judge_results.json` and
`final_results.json`. The judge stores per-dimension raw replies, returned
model, usage and attempt history. Repeating the same command resumes successful
dimensions and retries failed ones.

Checkpoints sign the data, inference, code, domain, native runtime, prompts,
judge model, endpoint and scoring settings. They also hash result content and bind
judge checkpoints to actual VAL results. Cached VAL plans must match normalized
inference actions before reuse. After an input or evaluator update,
use a new output directory or explicitly recompute with `--no-resume`.

## Repository layout

```text
benchmarks/       pinned 274-case data and manifests
configs/          public defaults and dataset registry
docs/             protocol, data and validation evidence
examples/         offline example and small input fixtures
licenses/         original third-party license texts
schemas/          inference JSON Schema
scripts/          inference and release utilities
src/ahat_benchmark/  evaluation package
tests/            offline regression suite
vendor/           audited PDDL domain and Linux VAL snapshot
```

Local credentials, outputs, archives, caches and crash dumps are excluded from
Git and distribution packages. See [CONTRIBUTING.md](CONTRIBUTING.md) for tests
and [release preparation](docs/releasing.md) for clean exports and builds.

## License and citation

Own code: **MIT**. Evaluation data: **CC BY-NC 4.0**. VAL: **BSD-3-Clause**.
Paper rubric: attributed to the AHAT paper, **CC BY 4.0**. See
[all third-party notices](THIRD_PARTY_NOTICES.md) for exact scope and terms.

```bibtex
@article{liu2026ahat,
  title={Any House Any Task: Scalable Long-Horizon Planning for Abstract Human Tasks},
  author={Liu, Zhihong and Li, Yang and Huang, Rengming and Lu, Cewu and Cai, Panpan},
  journal={arXiv preprint arXiv:2602.12244},
  year={2026}
}
```
