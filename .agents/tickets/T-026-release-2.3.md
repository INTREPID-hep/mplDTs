# T-026 — Release 2.3: version metadata and runtime docs

- **Status:** done
- **Phase:** 2
- **Epic:** E2 Runtime model
- **Depends on:** T-022, T-023, T-024, T-025
- **Branch:** `refactor/v2-integration`
- **PR:** —
- **Owner:** unassigned
- **Labels:** docs, release

## Context

M2 closed with the geometry rebuilt behind the legacy API, but the published
Sphinx pages still described the pre-refactor design and three version strings
disagreed: `pyproject.toml` said 2.1.0, `mpldts.__version__` said
2.2.0-beta and `docs/conf.py` hardcoded 2.0.0 (`BUG-06`). Nothing in the new
pipeline (specs, source, builder, frames) was documented, so a user could not
find it.

## Scope

- One version everywhere: **2.3.0** in `pyproject.toml` and
  `mpldts/__init__.py`; `docs/conf.py` derives the release from
  `mpldts.__version__` instead of hardcoding it.
- New page `docs/src/geometry/runtime.rst`: XML -> specs -> node tree ->
  frames, with autodoc for the new public API and an overlay example.
- `docs/src/geometry/main.rst`: the intro points at the new page;
  `DTGeometry` / `DTGEOMETRY` are documented as compatibility shims and
  `TransformManager` as the legacy path.
- `test/cms_dts_phi_zoomed_printer.py` deleted (untracked experiment; the
  maintainer approved the deletion).

## Out of scope

- Any API or geometry change: 2.3.0 is a drop-in replacement for 2.2.0-beta, as
  agreed with the maintainer (2.x while backward compatible, 3.x only when the
  legacy API is removed).
- Rewriting the legacy class pages (`station`, `super_layer`, `layer`,
  `drift_cell`); that API is still supported.
- Merging into `main`: the work lands on `refactor/v2-integration`.

## Acceptance criteria

- [x] `pyproject.toml`, `mpldts.__version__` and the Sphinx release all
      read 2.3.0.
- [x] Sphinx builds with no warnings and the new page renders with its classes.
- [x] `pytest -q` unchanged: 111 passed, 2 skipped, 2 deselected.
- [x] `main` and `enhancement-segments` untouched; the work is on a new
      branch.

## Verification

| Command | Result |
|---|---|
| `python -c "import mpldts; print(mpldts.__version__)"` | 2.3.0 |
| `sphinx-build -b html docs` (Sphinx 9.1.1) | build succeeded, no warnings |
| `pytest -q` | 111 passed, 2 skipped, 2 deselected |
| `grep -rn "2\.1\.0\|2\.2\.0-beta" pyproject.toml mpldts docs/conf.py` | no match |

## Progress

- 2026-11-07: created and closed in one session. The architecture page is new;
  the legacy pages only gained a pointer and a compatibility note, so the
  2.2.0-beta API description stays correct.
