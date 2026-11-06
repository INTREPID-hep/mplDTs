# T-023 — Immutable cache + per-event overlay

- **Status:** done
- **Phase:** 2
- **Epic:** E2 Runtime model
- **Depends on:** T-022
- **Branch:** `feature/phase-2-runtime`
- **PR:** —
- **Owner:** unassigned
- **Labels:** compatibility, model

## Context

`StationsCache.get(..., dt_info=...)` returned the cached station and wrote the
event's attributes onto its `DriftCell`s (`station.py:382-395`), so event A's
values leaked into event B: `BUG-02`. The station is expensive, so the cache
must stay; what changes is that a cached station is never written to.

## Scope

- `Station.overlay(dt_info=None)`: a per-event view that shares the node tree,
  the frame graph and the raw-id index, and rebuilds only the super-layer,
  layer and cell view objects. Its cell attributes are its own.
- `StationsCache.get(...)`: the cached station is never mutated; with
  `dt_info` it returns `station.overlay(dt_info)`, otherwise the cached
  instance.
- `set_cell_attrs` keeps working on a station the caller owns, and says so.
- `test/geometry/test_legacy.py`: cache isolation and shared geometry.

## Decisions

- The overlay is a *view*, not a copy of the geometry: `view._node`,
  `view._graph` and `view._parts` are the station's. Only the legacy view
  objects (3 super layers, 12 layers, ~700 cells) are rebuilt; nothing parses,
  derives poses or registers frames again.
- No proxy classes: the overlay reuses `SuperLayer` / `Layer` / `DriftCell`,
  so callers keep seeing the legacy objects.
- `Station(..., dt_info=...)` still applies the attributes to the station's own
  cells: that instance is not shared, so it is not a leak.

## Out of scope

- `DTGEOMETRY` shim and the performance pass (T-024).
- Triaging the visual scripts in `test/` (T-025).

## Acceptance criteria

- [x] Two overlays of the same chamber do not see each other's cell attributes.
- [x] The cached station keeps no event attributes, and repeated `get()` returns
      the same instance.
- [x] An overlay shares the graph and the node objects with its station.
- [x] `Station(..., dt_info=...)` and the plotting patches keep working.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
PYTHONPATH=/home/destrada/mplDTs pytest -q -m slow
```

## What changed

- `mpldts/geometry/station.py`: `Station.overlay()`; `StationsCache.get()`
  returns the cached instance or an overlay; the `set_cell_attrs` docstring
  points at the overlay.
- `test/geometry/test_legacy.py`: +2 tests (cache isolation, shared geometry).
- `docs/src/geometry/station.rst`: the autoclass no longer lists the removed
  private methods and the example block points at the current lines.

## Results

- `pytest -q`: 102 passed, 2 skipped, 2 deselected (28 s).
- `pytest -q -m slow`: both 250-chamber sweeps green.
- Overlay: 7 ms per event plus 5 ms to set 704 cell attributes, against 32 ms
  for a full `Station` (warm source, this machine).

## Progress

- 2026-11-06: started.
- 2026-11-06: done.
