# T-040 — Downstream cell-data contract and `test/downstream`

- **Status:** ready
- **Phase:** 4
- **Epic:** E4 Downstream
- **Depends on:** T-022, T-052
- **Branch:** `feature/T-040-downstream-contract`
- **PR:** —
- **Owner:** unassigned
- **Labels:** downstream, contract, tests

## Context

`DTPatternRecognition` (dtpr) consumes mplDTs through a small surface, and
nothing in mplDTs tests it. Measured on 2026-11-08 against the `2.5.0` checkout:

- `StationsCache().get(0, 1, 1)` works; `get(..., dt_info=DataFrame)` returns an
  overlay and the value reaches the cell (`time` 400.0 read back).
- `DTStationPatch(station, ax, local=True, faceview="phi"/"eta", vmap="time")`
  works, exposes `.station` and two collections; `MultiDTSegmentsPatch` works.
- `layer._first_cell_id`/`_last_cell_id` and `layer.cell(id)` work.
- `AMDTSegments(..., reference_frame="Station")` **fails** on 2.5.0 (T-056).

The data shape dtpr sends is one row per hit: `(wh, sc, st, sl, l, w)` plus
value columns (`time`, `BX`, ...). That is the contract; it is not documented
and not tested.

## Scope

- `test/downstream/test_dtpr_contract.py`: import and exercise exactly the
  symbols dtpr imports, without ROOT and without Qt:
  - `mpldts.geometry.StationsCache`, `stations_cache`, `AMDTSegments`,
    `Station`;
  - `mpldts.patches.DTStationPatch`, `MultiDTSegmentsPatch`, `DTRelatedPatch`;
  - one chamber, one overlay row through a `DataFrame`, one patch per faceview,
    one segment per reference frame, and `.station`/`._collections` checks.
- Document the contract in `docs/src/geometry/runtime.rst`: accepted types
  (`dict`, `list[dict]`, `DataFrame`), the required keys, and that it is applied
  to the immutable station as an overlay (never on the cached one).
- `docs/src/geometry/migration.rst` (or the runtime page): the aliases and
  attributes that stay API until 3.0 (ADR-025).

## Out of scope

- Any event model in mplDTs (ADR-024): no `Event`, `Track`, `Jet`, `Cone`,
  collections, event JSON.
- Changing dtpr (that is T-055).

## Acceptance criteria

- [ ] `pytest -q test/downstream` passes with no ROOT and no Qt installed.
- [ ] The test fails if any name in the contract list is renamed or removed.
- [ ] The cell-data contract is documented with the required keys.
- [ ] The suite runs in the normal `pytest -q` run (< 2 s).

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs \
  /home/destrada/Geant4/DTG4Simulator/env/bin/python -m pytest -q test/downstream
```

## Risks / notes

- The test must not import PyQt or ROOT: dtpr's GUI modules are out.
- Keep it a contract test, not a second integration suite: one chamber is enough.

## Progress

- 2026-11-08: opened after reading dtpr; scope cut by ADR-024.
