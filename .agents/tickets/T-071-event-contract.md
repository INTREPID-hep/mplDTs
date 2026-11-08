# T-071 — The per-event contract replaces `StationsCache.get(dt_info=...)`

- **Status:** deferred (the 3.0 window; see [`migration-3.0.md`](../migration-3.0.md))
- **Phase:** 7
- **Epic:** E7 Removal
- **Depends on:** T-040 (the contract test)
- **Branch:** `feature/T-071-event-contract`
- **PR:** —
- **Labels:** breaking, downstream, 3.0

## Context

`StationsCache.get(dt_info=dataframe)` is dtpr's event overlay: it copies a
station and writes per-cell values on it. That mutation is what `BUG-02` was
about, and ADR-024 already replaced the concept with a `(sl, l, w)` + value
columns table that patches read. 2.x keeps the old call as a shim.

## Scope

- `DTPatternRecognition`: draw from the contract table instead of the overlay;
  its mplDTs surface is 7 imports across 3 files and 18 legacy attribute uses.
- mplDTs: delete `StationsCache`, `dt_info`, `set_cell_attrs` and
  `Station.overlay` once dtpr no longer calls them.
- `test/downstream` pins the table contract as the only per-event path.

## Acceptance criteria

- [ ] dtpr draws simhits, segment paths and event objects with no `dt_info`.
- [ ] No `DTGEOMETRY` or `StationsCache` left in `mpldts`.
- [ ] The table contract in `test/downstream/test_dtpr_contract.py` is the
      documented path, with the columns listed.

## Progress

- 2026-11-08: planned.
