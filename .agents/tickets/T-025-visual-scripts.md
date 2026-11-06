# T-025 — Triage the visual scripts in `test/`

- **Status:** proposed
- **Phase:** 2
- **Epic:** E2 Runtime model
- **Depends on:** T-022 (the runtime API changes first)
- **Branch:** `feature/T-025-visual-scripts`
- **PR:** —
- **Owner:** unassigned
- **Labels:** tests, docs, cleanup

## Context

`test/` today mixes two unrelated things: the pytest suite
(`test/geometry/`) and 16 matplotlib demo scripts from before the refactor.
The demos were never tests: they open figures, hard-code a chamber and have no
assertions. Five of them are included verbatim in the Sphinx docs, so deleting
blindly breaks the documentation.

After T-022 the runtime API changes (poses, frames, cell access). Every script
must then be kept, converted or deleted — "it still imports" is not a
criterion.

## Rule

A script survives only if one of these holds:

1. the docs include it (then it moves to `docs/examples/` and keeps rendering), or
2. it asserts something the pytest suite does not.

Everything else is deleted. No script stays in `test/`.

## Inventory and decision

| Script | Doc reference | Decision |
|---|---|---|
| `cms_dt_local_wb.py` | `dt_station_patch.rst:41` | move to `docs/examples/` |
| `cms_dt_local_c.py` | `dt_station_patch.rst:60` | move to `docs/examples/` |
| `cms_dts_phi_zoomed.py` | `dt_station_patch.rst:77` | move to `docs/examples/` |
| `cms_dts_eta_zoomed.py` | `dt_station_patch.rst:90` | move to `docs/examples/` |
| `cms_dt_local_inversion.py` | `dt_station_patch.rst:120` | move to `docs/examples/` |
| `transform_validation.py` | `transforms.py` docstring | delete: asserted in `test/geometry/test_oracle.py` |
| `cms_dt_global_segments_eta.py` | — | delete (duplicate demo) |
| `cms_dt_global_segments_phi.py` | — | delete (duplicate demo) |
| `cms_dt_local_segments_eta.py` | — | delete (duplicate demo) |
| `cms_dt_local_segments_phi.py` | — | delete (duplicate demo) |
| `cms_dts_segments_eta.py` | — | delete (duplicate demo) |
| `cms_dts_segments_phi.py` | — | delete (duplicate demo) |
| `cms_dts_etas.py` | — | delete (duplicate demo) |
| `cms_dts_phi_zoomed.svg` | — | delete (generated output) |
| `inpect_dts_geometry.py` | — | delete (debug tool; superseded by the oracle) |
| `cms_dts_phi_zoomed_printer.py` | — | untracked experiment; delete after the maintainer confirms |

## Scope

- Move the five doc-referenced examples to `docs/examples/` and update the
  `literalinclude` paths in `docs/src/patches/dt_station_patch.rst`.
- Delete the rest, including `test/__init__.py` if `test/` then only holds
  `geometry/`.
- Fix every example the T-022 API broke; they must run headless
  (`matplotlib.use("Agg")`) so a smoke test can execute them.
- Add one smoke test that runs each example with `Agg` and a fixed figure
  size (no image comparison).
- Update `docs/`, `.agents/conventions.md` and the README if a path changes.

## Out of scope

- Rewriting the plotting layer (`mpldts/patches/`).
- Image-comparison (golden figure) tests.
- Converting demos into geometry tests; the oracle already covers geometry.

## Acceptance criteria

- [ ] `test/` contains only the pytest suite (`test/geometry/`).
- [ ] The five doc examples live in `docs/examples/` and the docs still build.
- [ ] Each example runs headless and is exercised by one smoke test.
- [ ] `grep -rn "test/" docs README.md` returns only pytest paths.
- [ ] `pytest -q` is unchanged and green.

## Verification

``bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_examples.py
grep -rn "test/" docs README.md
``

## Risks / notes

- Do not delete a doc-referenced script before the `.rst` is updated; Sphinx
  fails hard on a missing `literalinclude`.
- Keep the examples small; they are documentation, not a second test suite.
- `cms_dts_phi_zoomed_printer.py` is untracked work; confirm before deleting.

## Progress

- 2026-11-06: created after the maintainer asked for the visual scripts to be
  part of the plan; the pytest suite replaces them as the regression net.
