# T-070 — Remove the legacy view layer

- **Status:** done (3.0.0, 2026-11-09)
- **Phase:** 7
- **Epic:** E7 Removal
- **Depends on:** T-071 (dtpr on the new surface), T-073 (the deprecation release)
- **Branch:** `feature/T-070-legacy-layer-removal`
- **PR:** —
- **Labels:** breaking, cleanup, 3.0

## Context

2.x keeps the pre-refactor classes alive so the downstream packages could
migrate one step at a time (ADR-025). They are views over the model, and the
model is what everything actually needs. Keeping both costs about 1.5k lines
and three ways to build a station.

## Scope

- Delete `station.py`'s XML-backed constructor, `transformer`, `bounds` and the
  raw-id plumbing; keep one station constructor for the plotting patches
  (`Station.from_spec`, no XML behind it).
- Delete `dt_frame.py`, `_geometry.py` (`DTGeometry`, the `DTGEOMETRY` proxy),
  `super_layer.py`, `layer.py`, `drift_cell.py`; fold `presets/cms.py` onto
  the spec path.
- Delete `StationsCache`, `dt_info`, `set_cell_attrs` and `Station.overlay`
  (see T-071 for the replacement).
- Delete the `"SuperLayer"` frame alias and the alias table in `frames.py`.
- Delete `test/geometry/test_legacy.py`; move what it guaranteed into
  `test/downstream`.

## Out of scope

- The volume names (T-072) and the release mechanics (T-073).
- Any redesign: this ticket deletes and re-points, nothing else.

## Out of scope / must not happen

- A private copy of the legacy classes kept around for the patches.

## Acceptance criteria

- [ ] `mpldts/geometry` exports no XML-backed constructor and no cache.
- [ ] `pytest -q` green with `test_legacy.py` deleted.
- [ ] `test/downstream` covers the constructor, the frames and one patch per
      view on the new surface.
- [ ] The "Migrating to 3.0" table in `docs/src/geometry/runtime.rst` lists
      every removed call with its replacement (G1).

## Progress

- 2026-11-08: planned; deferred until both downstream packages are on the new
  surface.
- 2026-11-09: **done in 3.0.0.** Deleted the XML-backed `Station`, the chamber
  cache, `_geometry.py`, `_deprecation.py`, `presets/`,
  `StationsCache`, `overlay`/`set_cell_attrs`/`dt_info`, the
  standalone child constructors and the `"SuperLayer"` alias. The four view
  modules stay as the patch surface (ADR-027). `test_legacy.py` and
  `test_deprecations.py` are gone; the constructor, the frames and one patch
  per view are pinned by `test/downstream` and
  `test/geometry/test_views.py`.
