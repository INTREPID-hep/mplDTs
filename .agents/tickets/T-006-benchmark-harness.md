# T-006 — Benchmark harness

- **Status:** done
- **Phase:** 0
- **Epic:** E0 Safety net
- **Depends on:** T-001
- **Branch:** `feature/T-006-benchmark-harness`
- **PR:** —
- **Owner:** unassigned
- **Labels:** performance, tooling

## Context

The refactor targets < 20 ms/station. The checkout currently builds a station in ~0.7–1.0 s (installed package ~1.3–2.3 s), so the target is a large but plausible reduction. Without a reproducible benchmark, the claim cannot be verified and regressions will go unnoticed.

## Scope

- Add `test/benchmarks/bench_station.py` (plain script; no pytest dependency)
  that measures:
  - import + XML parse;
  - one station (`(-2,1,2)`, `(2,14,4)`, `(0,1,1)`);
  - the six representative chambers;
  - optional all 250 behind a flag;
  - peak memory (optional, `tracemalloc`).
- Print a stable table and a JSON output for comparison.
- Include the baseline numbers from `state.md` in the script's docstring.
- Document the command in `.agents/commands.md`.

## Out of scope

- Optimizing anything (Phase 1/T-014).
- CI gating on wall-clock times (machine-dependent); report, do not fail.

## Acceptance criteria

- [x] Script runs from a single command and prints per-case timings.
- [x] JSON output is stable and can be diffed between runs.
- [x] It runs against the source (`PYTHONPATH`) and states the package path.
- [x] A `--compare baseline.json` mode prints deltas.
- [x] The baseline in `state.md` is reproducible within a reasonable margin.

## Verification

```bash
cd /home/destrada/mplDTs
source /home/destrada/Geant4/DTG4Simulator/env/bin/activate
PYTHONPATH=/home/destrada/mplDTs python test/benchmarks/bench_station.py --json out.json
PYTHONPATH=/home/destrada/mplDTs python test/benchmarks/bench_station.py --compare out.json
```

## Risks / notes

- Timing is noisy on WSL; use medians of 3 and report the environment.
- Do not make CI fail on absolute times; use a generous threshold or report
  only.

## Progress

- 2026-11-05: proposed, awaiting review.
- 2026-11-06: done. `test/benchmarks/bench_station.py`; measured on the
  checkout: import 1.32 s, XML parse 0.53 s, stations 0.65 / 0.46 / 0.57 s.
- 2026-11-08: baseline re-measured on the merged code (2.8.0) and the model
  path added. The script now measures, per chamber, the legacy view
  (`Station(*key)`) **and** `build_station(source.station(*key))` with the XML
  parsed once, so the number the < 20 ms target refers to is in the table
  itself.

| Case | 2.8.0, checkout, median of 3 |
|---|---|
| import | 0.3 s |
| XML parse (`DTGeometry`) | 0.3 s |
| `Station(-2, 1, 2)` | 2-3 ms |
| `Station(2, 14, 4)` | 1.6-3.3 ms |
| `Station(0, 1, 1)` | 1.8-2.5 ms |
| model path (same chambers) | 3.7-8.4 ms |

The millisecond cases move up to 50% between runs on WSL, so the docstring
states them as an order of magnitude; `--compare` prints the delta between
two JSON runs and never fails the run.
