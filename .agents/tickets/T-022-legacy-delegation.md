# T-022 — Legacy constructors delegate

- **Status:** done
- **Phase:** 2
- **Epic:** E2 Runtime model
- **Depends on:** T-020, T-021
- **Branch:** `feature/phase-2-runtime`
- **PR:** —
- **Owner:** unassigned
- **Labels:** compatibility, model

## Context

`Station`, `SuperLayer`, `Layer` and `DriftCell` still read the XML through
`DTGEOMETRY` query strings and each one copies a `TransformManager` from its
parent. That copy is where `BUG-01` lives: the SL2 cell local is a mixed-frame
value and the old chain rotates a station-frame subtraction.

## Scope

- The four legacy classes build from `CMSXMLSource` + `build_station`;
  `obj.transformer` becomes a `FrameView` on the station graph.
- `CMSXMLSource.record()` and `chamber_of(raw_id)`: the values the model does
  not carry (raw ids, XML local positions, super-layer/layer bounds).
- The plotting virtual frames (`StationNvPhi`, `StationNvEta`, `SectorRef`,
  `SL13Center`) are registered on the station graph, so the patches keep
  working.
- Keep the constructor signatures from conventions §8.1, including the
  standalone `SuperLayer(rawId=...)` and `Layer(rawId=...)` forms.
- `test/geometry/test_legacy.py`: the wrappers, the standalone forms, the
  frame names and one headless patch build.

## Decisions

- **Data attributes stay verbatim XML** (`local_center`, `global_center`,
  `direction`, `bounds`, `id`). Conventions §7.3 keeps node fields at `1e-6`,
  and the pinned generator rotates the SL2 cell local itself. Nothing in the
  frame path reads them any more: `BUG-01` was a chain error, and the chain is
  now the node poses from T-020.
- `station.super_layers` keeps XML document order (`[SL1, SL3, SL2]`).

## Out of scope

- Immutable geometry + per-event overlay (T-023).
- `DTGEOMETRY` shim and the performance pass (T-024).
- Triaging `test/` (T-025).

## Acceptance criteria

- [x] The SL2 oracle test passes with the `xfail` removed; the all-chamber
  sweep is green.
- [x] Node fields still match the XML at `1e-6` cm.
- [x] `DTStationPatch` draws the same rectangles as the old code (18 cases,
  worst vertex deviation 0.0 cm).
- [x] Standalone `SuperLayer(rawId)`, `Layer(rawId)`, `DriftCell(number)` work.
- [x] `"SuperLayer"` and `"SL{n}"` both resolve from a super-layer view.
- [x] No XML import outside `sources/`.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
PYTHONPATH=/home/destrada/mplDTs pytest -q -m slow test/geometry/test_oracle.py
```

## What changed

- `sources/cms_xml.py`: `record()` (the verbatim XML values), `chamber_of(raw_id)`
  (rawId -> chamber) and `position()` (the text parser, now public because
  `DriftCell` reads the XML wire local). Wire locals stay text in the record:
  only the legacy wrappers parse them, so the model path does not pay for them.
- `station.py`: `CMSXMLSource` + `build_station` + one `FrameGraph`; every object gets
  a `FrameView` on that graph; `station_for(raw_id)` backs the standalone
  constructors; the plotting frames (`StationNvPhi`, `StationNvEta`, `SectorRef`,
  `SL13Center`) are virtual edges on the station frame.
- `super_layer.py`, `layer.py`, `drift_cell.py`: views over their node and the
  source record; the per-object `TransformManager` copies and the hand-written
  SL2 rotation are gone.
- `test/geometry/test_legacy.py` (8 tests): one-graph invariant, the standalone
  forms, the frame names, the plotting frames, a headless patch build, `dt_info`
  and the missing-chamber error.

## Results

- `pytest -q`: 100 passed, 2 skipped, 2 deselected.
- `pytest -q -m slow`: both 250-chamber sweeps green (152 s on a loaded
  machine), SL2 included.
- Same code, old vs new, on three chambers: the patch vertices are identical
  and so is every value the `.tg` generator reads (station/SL bounds,
  `local_cords_at_min`, cell `local_center`, the SL2 rotation).
- Station build: 1009 ms -> 64 ms per station (five chambers).
- `.tg` output is therefore unchanged; the generator pin in T-005 stays valid.

## Progress

- 2026-11-06: started.
- 2026-11-06: done.