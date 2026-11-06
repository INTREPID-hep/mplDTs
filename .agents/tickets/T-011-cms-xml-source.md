# T-011 — CMS XML source

- **Status:** done
- **Phase:** 1
- **Epic:** E1 Specs + source
- **Depends on:** T-010
- **Branch:** `feature/phase-1-specs`
- **PR:** —
- **Owner:** unassigned
- **Labels:** source, xml, performance

## Context

The old model reads the XML through `DTGEOMETRY` query strings and resolves
frames by subtraction. This ticket moves the CMS-specific knowledge into one
source module that emits `StationSpec`.

## What the XML actually contains

- Chamber, super-layer and layer `LocalPosition` are **station frame**.
- Layer-in-super-layer is a pure `(0, 0, 1.95)` translation for every SL.
- The **SL2 cell locals are not station frame**: they carry the 90° rotation
  mixed in. That mixture is `BUG-01`: the old chain rotates a station-frame
  difference, which is why SL2 was off by 0.5 cm.
- SL2 layers hold **57** cells, not the 49/50/49/48 of SL1 and SL3.

## Scope

- `mpldts/geometry/sources/cms_xml.py`: one parse, indexes for chambers, super
  layers, layers and cell centres; explicit attribute names (no
  `attrib.values()`, which is `BUG-03`).
- Poses derived from the XML **globals** plus the CMS orientation table
  (`SUPER_LAYER_ROTATION_Z = {1: 0, 2: -90, 3: 0}`), so the mixed locals are
  never trusted.
- `CellGrid` from `WiresSize`/`WiresRange`; `offset` from the first cell,
  `shape = Box(width, length, thickness)`.
- `cell_centres()` keeps the XML globals available as the oracle reference.
- This is the only new module allowed to import `ElementTree`.

## Out of scope

- The builder and `FrameGraph` (Phase 2).
- JSON serialization (T-051).

## Acceptance criteria

- [x] 250 chambers indexed; unknown chamber raises `KeyError`.
- [x] Every emitted spec validates.
- [x] Cell centres derived from the specs match the XML globals.
- [x] No XML import outside `sources/` (asserted by a test).

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_cms_source.py
```

## Progress

- 2026-11-06: done on `feature/phase-1-specs`. Parsed once (~1.1 s); pose
  derivation validated by the T-012 oracle over all 250 chambers.
