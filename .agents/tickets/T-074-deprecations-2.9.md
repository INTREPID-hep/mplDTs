# T-074 — The 2.9.0 deprecation release

- **Status:** done (2.9.0, 2026-11-08)
- **Phase:** 7
- **Epic:** E7 Removal
- **Depends on:** —
- **Branch:** `feature/2.9.0-deprecations`
- **PR:** —
- **Labels:** release, deprecation, 2.9

## Context

`migration-3.0.md` section 3 opens with a deprecation release (S1). It is the
only step of the removal that needs no window from the other packages: it adds no
behaviour, deletes nothing, and turns the plan into something a consumer meets in
its own test run instead of in a changelog.

## Scope

- `mpldts/_deprecation.py`: `deprecated(old, new)` emits one
  `DeprecationWarning` whose stacklevel is the caller's line, with the text
  "X goes away in mplDTs 3.0; use Y".
- Warned: `Station(wheel, sector, station)`, `Station.set_cell_attrs`,
  `Station.overlay`, `StationsCache.get`, the standalone
  `SuperLayer`/`Layer`/`DriftCell` constructors,
  `DTGeometry(xml_file)`, `DTGEOMETRY` and `TgSink(name_of=...)`.
- Silent on purpose: the pipeline that survives (`CMSXMLSource` -> spec ->
  `build_station` -> export), `Station.from_spec` and every internal use of
  the views (they warn only when a consumer builds them standalone).
- The frame alias `"SuperLayer"` is in the migration table but not in a
  warning: a dictionary lookup has no call site to report.
- `docs/src/geometry/runtime.rst` grows "Migrating to 3.0" (what goes ->
  what replaces it), the page a consumer reads before moving.
- 2.9.0 in `pyproject.toml` and `mpldts/__init__.py`.

## Acceptance criteria

- [x] `test/geometry/test_deprecations.py`: each entry point warns once and names
      its replacement; the surviving pipeline is silent (the guard).
- [x] Full suite green; dtpr and the simulator unaffected; docs 0 warnings.
- [x] The table and the tests agree: 9 warned calls, one table-only row.

## Progress

- 2026-11-08: done, tag `v2.9.0`. The removal itself stays deferred (T-070, T-072,
  T-073).
