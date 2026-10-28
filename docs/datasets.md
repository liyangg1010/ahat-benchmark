# Datasets and custom inputs

The bundled release has 348 cases: easy 146, medium 94 and open 108.
The raw file is pinned to HF revision
[`44de8a66c58cfd4cea03923bed9dbb8bd69d8f85`](https://huggingface.co/datasets/SII-liyang2024/AHAT-dataset/tree/44de8a66c58cfd4cea03923bed9dbb8bd69d8f85).
Source SHA-256:
`05cb4e725b5a8a93feb8c8609c768dc7a93371fb00c076f09ddaa104bdf8fc94`.
Data license: [CC BY-NC 4.0](../licenses/CC-BY-NC-4.0).

`ahat_eval_set.jsonl` is retained verbatim, including reference plans.
Runtime `ahat-{easy,medium,open}/cases.json` files split by source `type`,
preserve source order, and project to `id`, `instruction` and `scene_graph`.
Each split manifest records the active runtime domain name and hash, case count,
file hash, source revision and license. The `source_domain` field records the
upstream HF domain label; it is retained for provenance and is not the runtime
evaluation protocol.
`ahat-benchmark doctor` checks these snapshots. `benchmarks/hf_sync.json`
records source provenance and all local data/manifest hashes.

## Reference-plan compatibility

The bundled domain is based on the `ahat_domain.pddl` snapshot shipped with the
pinned HF dataset. It includes `light_on` and `clean_item_with_faucet`, and fixes the
missing `holding` deletions in `place_in_receptacle` and
`hand_over_to_person`. All 348 bundled reference plans validate with this
domain: easy 146, medium 94 and open 108. Reference plans are not supplied to
the LLM reviewer.

The local `ahat-v3-physobj-floor-cleaning` protocol widens the `?r` parameter of
`require_floor_cleaner` and `clean_room_floor` from `room` to `physobj`. This
preserves the attribute on carpets and mats and allows them to be cleaned with
a floor cleaner when all existing action preconditions hold. Other cleaning
actions do not enforce this attribute as an exclusive tool requirement.
The evaluation cases remain pinned to the source revision recorded in each
split manifest, while the domain is synced independently from the current HF
domain revision recorded in `benchmarks/hf_sync.json`. The modified domain
fingerprint is recorded in `benchmark_manifest.json`.
All 348 reference plans remain valid, but 115 cases retain additional facts in
their final state, changing the D1 judge input. Re-evaluate with a new output
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
fixture. The public registry contains only the three HF splits; additional
local datasets can be registered separately without changing bundled data.
