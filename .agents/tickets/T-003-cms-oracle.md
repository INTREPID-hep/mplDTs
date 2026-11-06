# T-003 — Transform invariant + oracle harness (includes the node snapshot)

- **Status:** done
- **Phase:** 0
- **Epic:** E0 Safety net
- **Depends on:** T-001
- **Branch:** `feature/T-003-oracle-harness`
- **PR:** —
- **Owner:** unassigned
- **Labels:** tests, correctness, transforms, regression

## Context

The XML contains a `GlobalPosition` for every cell, independent of the model's
pose code. That makes it a ground truth ("oracle") for the whole refactor.

Before Phase 1 there are no specs, so the oracle cannot yet be applied to a
spec-derived path. Phase 0 builds the **harness** and applies it to the current
transform path (`Cell → CMS`); Phase 1's T-012 reuses the harness against the
spec path. This is the same comparison, not two tests.

The current SL2 transform is wrong (`BUG-01`); the harness must record that
failure as `xfail(strict=True)` and print the expected magnitude
`√2·|SL_local_x|`.

**T-002 was folded into this ticket.** Instead of a second checked-in golden
JSON, the representative-chamber snapshot is the XML itself: the same test
compares node fields (id, number, bounds, direction, local pose) and cell
centres against the XML. One file to maintain, no `--update-golden` path.

## Scope

- `test/geometry/reference.py` (test helper, not library code): read the XML
  once and expose `(wh, sec, st, sl, layer, cell) → xyz` plus the node fields,
  using the library's own `DTGEOMETRY` accessors so the test never re-implements
  XML parsing.
- `test/geometry/test_oracle.py`:
  - compare `cell.transformer.transform((0,0,0), "Cell", "CMS")` with the
    reference; tolerance `1e-3` cm (max norm); report chamber/SL/layer/cell
    and the vector;
  - assert the cell count per layer matches the XML `WiresRange`;
  - node snapshot: station id/local/global/direction/bounds, each super layer
    and layer local/global centre, against the XML (`1e-6` cm, ids exact);
  - run six representative chambers by default; all 250 behind `-m slow`;
  - mark SL2 `xfail(strict=True)` with `BUG-01` and the expected magnitude.
- Expose the comparison as a reusable function
  (`compare_cell_centres(pairs, tol)`) so T-012 can feed spec-derived centres
  into it.
- A negative test: perturb one reference by `1e-2` cm and assert the comparison
  fails with a useful message.
- Document which package (checkout vs installed) was used.

## Out of scope

- Fixing `BUG-01` (T-022).
- The specs/source (T-010/T-011).
- Performance (T-006).
- A golden-file mechanism; the XML is the reference.

## Acceptance criteria

- [x] The harness passes for the representative set, except the documented SL2
      `xfail`.
- [x] `pytest -q -m slow test/geometry/test_oracle.py` covers all 250.
- [x] A deliberately perturbed reference fails with a useful message.
- [x] The test asserts the cell count and the node fields.
- [x] `compare_cell_centres` is importable by T-012 without copying.

## Verification

~~~bash
cd /home/destrada/mplDTs
source /home/destrada/Geant4/DTG4Simulator/env/bin/activate
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_oracle.py
PYTHONPATH=/home/destrada/mplDTs pytest -q -m slow test/geometry/test_oracle.py
~~~

## Risks / notes

- The installed package and the checkout differ; run against the checkout.
- Do not loosen the tolerance to make a broken pose pass.
- The current baseline is ~0.7–1.0 s/station on the checkout, so the full run
  is minutes, not seconds; keep it behind the marker.

## Progress

- 2026-11-05: proposed (as CMS oracle), awaiting review.
- 2026-11-06: merged with T-004; now the Phase 0 harness, reused by T-012.
- 2026-11-06: T-002 folded in; status `doing`.
- 2026-11-06: done. `test/geometry/reference.py` (XML extractor) and
  `test_oracle.py`: cell centres, node fields, perturbed-reference negative
  test, all-250 run behind `-m slow`. Tolerance is `2e-3` cm because the XML
  stores 3 decimals; SL2 (0.5 cm) is far outside it and stays `xfail`.
