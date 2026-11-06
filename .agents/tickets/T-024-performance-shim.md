# T-024 — Performance pass, `DTGEOMETRY` shim, no XML in the model

- **Status:** done
- **Phase:** 2
- **Epic:** E2 Runtime model
- **Depends on:** T-020, T-021, T-022, T-023
- **Branch:** `feature/phase-2-runtime`
- **PR:** —
- **Owner:** unassigned
- **Labels:** performance, compatibility

## Context

Three things were left from the legacy path:

- `mpldts/geometry/_geometry.py` parsed `DTGeometry_v3.xml` (20.8 MB) at import,
  so `import mpldts.geometry` cost ~2.8 s although nothing in the model reads
  that tree any more (T-022).
- `Station()` rebuilt the node tree, the frame graph and the 700-odd legacy
  views for every instance; a second station of the same chamber cost 25 ms and
  re-parsed every wire local position.
- `_geometry.py` read `Bounds` / `Wires` with `element.attrib.values()`, so
  reordering legal XML attributes changes the result (`BUG-03`).

## Scope

- `DTGEOMETRY` becomes a lazy proxy: the XML is parsed on the first attribute
  access, so importing the package no longer reads the file.
- `BUG-03`: explicit `width` / `thickness` / `length` / `first` / `last`.
- One build per chamber: `station._BUILT[key]` holds the record, the node tree
  and the graph; every `Station` is a view over it. The plotting virtual frames
  move into that build.
- Wire local positions are parsed once per chamber and stored in the layer
  record, so overlays and later stations do not parse them again.

## Decisions

- The cache is per **chamber**, not per station instance: the geometry is
  immutable (ADR-007) and `Station.overlay()` (T-023) owns the mutable cell
  attributes.
- `_geometry.py` stays as the legacy XML reader (public API, compatibility
  until 3.0); it is only off the import path now.
- `pandas` is still imported with the package (~0.5 s); the DataFrame branch of
  `set_cell_attrs` uses it and the import is not on the geometry path.

## Out of scope

- Triaging the visual scripts in `test/` (T-025).
- Phase 3 assemblies and presets.

## Acceptance criteria

- [x] Importing `mpldts.geometry` does not parse the geometry XML.
- [x] `Bounds`, `WiresSize` and `WiresRange` do not depend on attribute order.
- [x] Two stations of one chamber share the node tree and the graph; another
      chamber does not.
- [x] `pytest` and the slow sweeps are green; a station costs < 10 ms.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
PYTHONPATH=/home/destrada/mplDTs pytest -q -m slow
PYTHONPATH=/home/destrada/mplDTs python test/benchmarks/bench_station.py
```

## What changed

- `mpldts/geometry/_geometry.py`: `_LazyDTGeometry` proxy; explicit attribute
  names for `Bounds` and `Wires`.
- `mpldts/geometry/station.py`: `_BUILT` + `_built()`; `_face_factor` and
  `_add_plotting_frames` are module functions over the shared build.
- `mpldts/geometry/layer.py` / `drift_cell.py`: cell locals parsed once per
  chamber and cached in the layer record.
- `test/geometry/test_runtime.py` (3 tests): lazy import, attribute order, one
  build per chamber.
- Docs: `main.rst` (lazy `DTGEOMETRY`, caching note), `station.rst`,
  `super_layer.rst`, `layer.rst` literalinclude ranges.

## Results

- `pytest -q`: 105 passed, 2 skipped, 2 deselected.
- `pytest -q -m slow`: both 250-chamber sweeps green.
- `bench_station.py`: import 2.83 -> 0.96 s; station 25.4 -> 6.1 ms (MB2),
  7.1 -> 2.1 ms (MB4), 6.5 -> 3.0 ms (MB1); the first build of a chamber costs
  22-63 ms and is cached.
- Source parse unchanged (~2.5-2.9 s once per process).

## Progress

- 2026-11-06: started.
- 2026-11-06: done.
