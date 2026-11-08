# T-055 — `DTPatternRecognition` migration to 2.6.0

- **Status:** ready
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

- [ ] `pyproject.toml` pins the tag; `pip show mplDTs` reports 2.6.0.
- [ ] `pytest -q tests` in dtpr is green (or each failure is triaged in this
      ticket with a reason).
- [ ] The visualizer opens one event, plots the station and a segment patch,
      and the pick opens `LocalPlotter`.
- [ ] Wall time of the plotting path is recorded before/after (T-006 numbers).

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
