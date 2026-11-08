# T-072 — The volume names stop being the C++ API

- **Status:** deferred (the 3.0 window; see [`migration-3.0.md`](../migration-3.0.md))
- **Phase:** 7
- **Epic:** E7 Removal
- **Depends on:** T-073 (release), T-005 (the excerptor path in the simulator)
- **Branch:** `feature/T-072-volume-names`
- **PR:** —
- **Labels:** breaking, downstream, 3.0

## Context

`DTG4Simulator`'s sensitive detectors parse `Station_W.._Sec.._St..` and
`DriftCell_.._SL<n>_<encoding>`, and decode `(layer, wire)` from the copy
number of the cell volume. T-057 gave the exporter a `name_of` hook so the
generator could keep that scheme while moving onto the sink; the hook exists
only for that.

## Scope

- mplDTs: drop `TgSink.name_of`; the exporter emits its natural names
  (`DriftCell_<station>_<SL>`, copy numbers per mother).
- `DTG4Simulator`: `generate_geometry_data.py` drops the naming function;
  `DriftCellSD::DecodeCellID` and `StationSD::DecodeStationID` read the new
  names, and `(layer, wire)` comes from something explicit — a copy-number
  block per super layer, or a field in the name.
- The golden table: for all 250 chambers, the new decoding must reproduce the
  old `(wheel, sector, station, sl, layer, wire)` for every one of the 171732
  cells (G2). Recorded as a test in the simulator or as a fixture in mplDTs.
- One seeded Geant4 run compared hit for hit against the old files (G4).

## Risks / notes

- Old ntuples store the decoded tuple, not the name, so they stay readable as
  long as G2 holds. If it does not, say so loudly in the release note.
- Do not change the names in a different release than T-070: the C++ would be
  broken in between.

## Acceptance criteria

- [ ] `name_of` is gone from `TgSink`; `test/export` pins the natural names.
- [ ] The golden table matches for all 250 chambers.
- [ ] The simulator builds its geometry and the seeded run matches.

## Progress

- 2026-11-08: planned; T-057 is the shim this ticket removes.
