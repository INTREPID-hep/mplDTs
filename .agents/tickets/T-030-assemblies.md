# T-030 — `DetectorSpec` assemblies and custom stations

- **Status:** done
- **Phase:** 3
- **Epic:** E3 Assemblies and extras
- **Depends on:** T-020, T-021, T-022, T-026
- **Branch:** `feature/phase-3-assemblies`
- **PR:** — (branch pushed; the maintainer merges)
- **Owner:** —
- **Labels:** model, assemblies
- **Completed:** 2026-11-07

## Context

`DetectorSpec` existed in `specs.py` and validated, but nothing built it.
`build_station` accepted an optional parent and nothing else, `Station` was
hardwired to `(wheel, sector, station)` and the chamber cache was keyed by those
CMS coordinates. A custom chamber could not be built or plotted, and an
assembly of stations had no API.

## What was delivered

- `model.build_detector(spec, parent=None)`: the detector is the root node and
  every `DetectorSpec.stations` entry hangs under it at its own pose, so one
  `FrameGraph` holds the assembly. No second builder: it calls
  `build_station` per station. Exported from `mpldts.geometry`.
- `Station.from_spec(spec, dt_info=None)`: the public path from a spec to the
  legacy views without the CMS cache. `Station.__init__` was split into
  `_bind(record, node, graph)`, which both constructors share.
- `_record_for(node)` derives the record shape the legacy classes read (local
  centres, globals, direction, bounds, raw ids) from the node tree. Cell centres
  use the XML cell convention (super layer plane, station z), so a turned super
  layer plots correctly and a CMS chamber through `from_spec` reproduces the
  XML values.
- `_add_natural_views` holds the `StationNvPhi`/`StationNvEta` poses now,
  shared by the CMS chamber and a station built from a spec.
- The specs validator no longer caps super layer and layer numbers at the CMS
  counts (3 and 4); the source keeps its own counts. `SuperLayer` accepts any
  positive number.
- Plotting chooses the super layers of the phi and eta views by orientation
  (`dt_station_patch._is_turned`) instead of `super_layer.number == 2`. That is
  identical for all 250 CMS chambers and correct for custom geometry; it is the
  patch half of T-031.
- `test/geometry/test_assemblies.py` (23 tests) and
  `docs/examples/custom_station.py` (runs in `test_examples.py`).

## Out of scope

- JSON authoring (T-051), exporters (T-052), honeycomb (T-032), yoke (T-033).
- A new plotting class: the existing patches accept the new stations.
- Moving the CMS virtual frames into a preset: that is the rest of T-031.

## Acceptance criteria

- [x] Two stations with different poses build into one detector; a point taken
      through `FrameGraph` matches the composed `world_pose` (0.0 cm).
- [x] A custom 1-SL and a 5-SL station build and plot in phi and eta.
- [x] The 250-chamber oracle and the current suite stay green.
- [x] Station cost stays below 20 ms on a warm process.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q                     # 134 passed, 2 skipped
PYTHONPATH=/home/destrada/mplDTs pytest -q -m slow             # 2 passed (250 chambers)
```

The docs build (Sphinx 9.1.1) is warning-free with the new section.
CI run 42314584878 (`tests`) succeeded on `feature/phase-3-assemblies`.

## Risks / notes

- The record is derived, not parsed: `direction` is the station z axis of the
  composed pose, and grouping nodes without a shape report zero bounds (give a
  super layer a `shape` if its frame must be visible).
- A station built from a spec is not in the chamber cache; it is rebuilt per
  `from_spec` call (a few milliseconds) and carries its own node tree and graph.
- `Station.from_spec` does not accept a parent node yet; the assembly is
  inspected through `build_detector` and the graph.
