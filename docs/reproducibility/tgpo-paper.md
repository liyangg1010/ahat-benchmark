# TGPO Paper evaluation version

This file is the version lock for the evaluation reported in the TGPO paper.
It is immutable. Future benchmark development should continue on `main` and
must not rewrite this record.

## Locked snapshot

The paper reproduction snapshot is the annotated Git tag `paper-tgpo-v1`,
pointing to the following commit:

| Item | Value |
| --- | --- |
| Repository tag | `paper-tgpo-v1` |
| Repository commit | `fafa4624cf4e99c4af10d1738d51fc9cd97e91fb` |
| Package version | `2.2.0` (the checkout also contains post-2.2.0 changes) |
| Benchmark manifest SHA-256 | `4e059de608ffd0a7cc5cff8334994194dc9f5ae0210464b50585484173473d49` |
| HF dataset revision | `44de8a66c58cfd4cea03923bed9dbb8bd69d8f85` |
| Domain SHA-256 | `65cf0f5503763acecbb728f598cee9b6baf7ae7f950087a597f8c99db2d4ff89` |
| VAL executable SHA-256 | `03fa000c6842d3fc5ea15740195e91178a2918f6454d4abd4438454ed136a136` |
| VAL library SHA-256 | `364cbf670a6085885a30fb3d05bbf1a6de923cc94b19f479500aa4dbe7058c95` |
| Judge protocol | `paper-rubric-2602.12244v2` |
| Judge model in default config | `ds-v4.1-flash-w8a8` |

Keep the result JSON files in the paper's artifact archive. Do not put API
keys or private endpoint URLs in Git. Cite both the tag and commit in the
paper, for example:

   > AHAT Benchmark, `paper-tgpo-v1` (`<full commit SHA>`), dataset revision
   > `<HF revision>`, accessed `<date>`.

The existing `benchmark_manifest.json` and per-run provenance signatures cover
the benchmark code, domain, prompts, validator, data and scoring protocol.
The paper record adds the missing link to the exact source checkout and the
specific inference/results artifacts.

## Snapshot verification

From a clean checkout:

```bash
git checkout paper-tgpo-v1
git cat-file -t paper-tgpo-v1
git show --no-patch --format='%H %s' paper-tgpo-v1
git status --short
sha256sum path/to/inference.json outputs/tgpo-paper/final_results.json
python -m pip freeze > outputs/tgpo-paper/environment.txt
```

A later release may change `main`, package versions, domains or prompts without
changing what `paper-tgpo-v1` means.
