# T-012 — Spec oracle over all 250 chambers

- **Status:** done
- **Phase:** 1
- **Epic:** E1 Specs + source
- **Depends on:** T-011, T-003
- **Branch:** `feature/phase-1-specs`
- **PR:** —
- **Owner:** unassigned
- **Labels:** tests, correctness

## Context

The Phase 1 gate: rebuild every CMS chamber from specs and compare each cell
centre with the XML `GlobalPosition`. This is the same comparison as T-003,
fed from the spec path instead of the runtime classes.

## Scope

- `test/geometry/spec_centres.py`: compose station → super layer → layer →
  cell poses (a test helper; the builder owns it in Phase 2).
- `test/geometry/test_spec_oracle.py`: all 250 chambers by default (the spec
  path is fast — no `Station` builds), plus a cell-count check on the six
  representative chambers.

## Acceptance criteria

- [x] All 250 chambers within `2e-3` cm.
- [x] Cell counts match the XML per chamber.
- [x] Reuses `reference.compare_cell_centres`; no copied comparison code.
- [x] Runs in seconds, so it stays out of the `slow` marker.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_spec_oracle.py
```

## Progress

- 2026-11-06: done. 250 chambers, worst deviation `1.25e-3` cm (XML rounding),
  ~1.1 s for the whole file. SL2 now matches: `BUG-01` does not exist on the
  spec path.
