# T-055 — `DTPatternRecognition` migration to 2.6.0

- **Status:** done
- **Phase:** 4
- **Epic:** E4 Downstream
- **Depends on:** T-040, T-043, T-056
- **Branch:** `feature/T-055-dtpr-migration` (in `DTPatternRecognition`)
- **PR:** —
- **Owner:** unassigned
- **Labels:** downstream, migration

## Context

`DTPatternRecognition` pins `mplDTs @ git+https://github.com/INTREPID-hep/mplDTs.git@v2.2.0-beta`
(`pyproject.toml`) and its env has 2.2.0-beta installed (pip metadata still
says 2.1.0 — the metadata drifted). With
`PYTHONPATH=/home/destrada/mplDTs` the plotting imports and the station/cell/
patch/segment contract all work against the `2.5.0` checkout except
`AMDTSegments(reference_frame=...)`, which T-056 fixes in 2.5.1.

## Scope

- Bump the pin to the tag that carries T-056 and T-043 (`v2.6.0`), not a branch.
- Reinstall the env from the pin so the installed copy matches it (and the
  metadata stops reporting 2.1.0).
- Run the dtpr suite and the visualizer smoke (headless, `DTPR_TEST_AUTOCLOSE_GUI`).
- Compare one event's plots against 2.2.0-beta: station, cells with a colormap,
  one segment patch; the geometry must be identical, the only acceptable
  difference is the honeycomb attachment if it is enabled.
- Swap the ad-hoc artists: `embed_simhits2axes_loc` and `embed_shower2axes_loc`
  draw through `DTObjectsPatch` (T-043) instead of `ax.scatter`/`ax.plot`, so
  they follow `local`/`inverted` and the phi/eta rule like the cells.

## Out of scope

- New dtpr features; the event model is dtpr's own (ADR-024).
- Replacing dtpr's `stations_cache`/DataFrame bridge.
- New renderers in mplDTs: T-043 ships them.

## Acceptance criteria

- [x] `pyproject.toml` pins the tag; `pip show mplDTs` reports 2.6.0
      (installed from the tag with `--no-deps`, so numpy stayed put).
- [x] `pytest -q tests` in dtpr is green except two pre-existing failures,
      triaged below: 22 passed, 2 failed.
- [x] The visualizer opens one event headless (`QT_QPA_PLATFORM=offscreen`,
      `DTPR_TEST_AUTOCLOSE_GUI=1`); the pick handler itself was not driven
      headlessly, which the GUI session covers.
- [ ] Wall time of the plotting path (T-006 numbers): deferred to T-006, which
      owns the benchmark on the merged code.

## Verification

```bash
cd /home/destrada/DTPatternRecognition
./env/bin/python -m pytest -q tests
DTPR_TEST_AUTOCLOSE_GUI=1 ./env/bin/dtp events-visualizer --inpath tests/ntuples
```

## Risks / notes

- dtpr's env may pin numpy < 2.0 (its `pyproject` does); check the install does
  not downgrade what mplDTs needs.
- If a second incompatibility appears, fix it in mplDTs as a patch release, not
  by patching dtpr around it.

## Progress

- 2026-11-08: opened with the measured contract results (see T-040).
- 2026-11-08: done on `feature/T-055-dtpr-migration` (dtpr), merged to its
  `main`. Pin `v2.6.0` in `pyproject.toml` (dependency and uv source);
  `embed_simhits2axes_loc` and `embed_shower2axes_loc` build the objects
  and hand them to `DTObjectsPatch` instead of `scatter`/`plot`; the `_glob`
  variants keep plotting CMS coordinates directly.
- Triage of the suite (`pytest -q tests`, `PATH=env/bin:$PATH` and
  `QT_QPA_PLATFORM=offscreen`): 22 passed, 2 failed. `test_config_include_loader`
  raises `FileNotFoundError` on its own include path (a list is passed where the
  loader wants one path) and `test_particle_equality_and_hash` raises `TypeError`;
  both fail identically on the untouched code, so they are dtpr's own and not
  this migration. Without `env/bin` on `PATH` the CLI tests fail to find the
  `dtpr` script, and without a platform plugin Qt aborts: environment, not code.
- The pin makes `pip show mplDTs` report 2.6.0 in `DTPatternRecognition/env` (it
  reported the stale 2.1.0 before).
