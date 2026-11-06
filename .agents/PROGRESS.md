# PROGRESS — checkpoints and session log

**Last updated:** 2026-11-06
**Current checkpoint:** `CP-005 — M0 safety net`
**Implementation status:** Phase 0 complete on `feature/phase-0-safety-net`
**Board:** [`TICKETS.md`](TICKETS.md) · **Plan:** [`plan.md`](plan.md)

---

## 1. Current status

| Item | Value |
|---|---|
| Phase | 2 in progress (T-020, T-021 done) |
| Current milestone | M2 — Runtime model + compatibility |
| Last completed | CP-006 (M1: specs + CMS source) |
| Next | T-022 (legacy delegation + `BUG-01`) |
| Code changes | `super_layer.py` alias (T-005); `specs.py`, `sources/cms_xml.py` (T-010/T-011); `model.py` (T-020); `frames.py` (T-021); tests, benchmark, CI |
| Library tests | `pytest -q`: 88 passed, 4 xfailed (SL2), 2 skipped, 2 deselected |
| Builder cost | 7.46 ms/station (250 stations, spec -> `Node` tree) |
| pyg4ometry | deferred, not installed |
| Open blocker | none — plan Rev 4 approved 2026-11-06 |

---

## 2. Checkpoints

| ID | Checkpoint | Date | Status | Evidence |
|---|---|---|---|---|
| CP-000 | Initial review of the geometry code | 2026-11-05 | done | analysis + findings |
| CP-001 | Design Rev 2 + prototype v2 | 2026-11-05 | done | `docs/design/generalization-plan.md`, `prototype/parametric_poc.py` |
| CP-002 | `.agents` operating workspace | 2026-11-05 | done | `AGENT.md`, `context.md`, `state.md`, ... |
| CP-003 | Plan Rev 3 + ticket system | 2026-11-05 | done | `TICKETS.md`, `tickets/`, this file |
| CP-004 | Plan Rev 4 review + cleanup | 2026-11-06 | done | `plan.md`, `TICKETS.md`, design Rev 4 |
| CP-005 | M0 safety net | 2026-11-06 | done | `feature/phase-0-safety-net`: pytest 15/4xfail/2skip, all-250 oracle, 621-placement `.tg`, benchmark, CI |
| CP-006 | M1 specs + source | 2026-11-06 | done | spec oracle: 250/250, worst 1.25e-3 cm |
| CP-007 | M2 runtime parity | — | pending | T-020…T-024 |
| CP-008 | M3 assemblies + extras | — | pending | T-030…T-033 |
| CP-009 | M4 event annotations (optional) | — | pending | T-040…T-042 |
| CP-010 | M5 authoring + `.tg` | — | pending | T-050, T-051, T-052, T-054 |
| CP-011 | M6 GDML (future) | — | deferred | T-060 |

A checkpoint is complete only when its gate (in `TICKETS.md` §5) is met and
the evidence is linked here.

---

## 3. Session log

| Date | Tickets | What happened | Verification | Next |
|---|---|---|---|---|
| 2026-11-05 | D-01…D-04 | design review, prototype v1/v2, `.agents` workspace | `parametric_poc.py` all checks 0.0 | tickets/plan |
| 2026-11-05 | D-05 | converted the backlog to tickets; recorded maintainer decisions; extended the design to physical extras and event objects | links/fences checked; no code run | **await review** |
| 2026-11-06 | D-06 | plan Rev 4: specs-first, optional events, `VolumeSink` at first exporter, CLI/YAML out; removed stale v1/plan-v2; refreshed baselines; resolved open questions | station timings + SL2 measured on the checkout; links checked | **await approval** |
| 2026-11-06 | D-07 | corrected the wire/cell terminology: the XML `<Wire>` is the cell entry; removed the separate wire object from the design, plan, tickets, prototype and docs | prototype rerun: all checks 0.0, 193 placements | **await approval** |
| 2026-11-06 | T-001, T-003, T-005, T-006, T-007 | Phase 0: pytest + oracle harness with the XML node snapshot (T-002 folded in); `SuperLayer` alias + one-station `.tg` smoke; benchmark; CI workflow | 15 passed / 4 xfailed (SL2) / 2 skipped; all-250 oracle; 621 placements; 0.65-0.57 s/station | Phase 1 |
| 2026-11-06 | T-010, T-011, T-012 | Phase 1: immutable specs, `CMSXMLSource` with parse-time indexes, spec oracle over all 250 chambers; poses derived from the XML globals (SL2 locals are mixed-frame, which is `BUG-01`) | `pytest` 55 passed / 4 xfailed; spec oracle worst 1.25e-3 cm in 1.1 s | Phase 2 (T-020) |
| 2026-11-06 | T-020 | Phase 2 starts: `Node` + `build_station` (top-down `world_pose`, grouping nodes with `shape=None`, cells from the `CellGrid`); exported from `mpldts.geometry` | `pytest` 73 passed / 4 xfailed / 2 skipped; builder oracle 250/250 at 2e-3 cm (slow); 7.46 ms/station | T-021 |
| 2026-11-06 | T-021 | Phase 2 frames: `FrameGraph` (one edge per parent/child pose, BFS with a per-pair cache) and `FrameView` (scoped `Station`/`SuperLayer`/`SL{n}`/`Layer`/`Cell`/`CMS` aliases, legacy `add`/`remove` signatures, virtual frames) | `pytest` 88 passed / 4 xfailed / 2 skipped; the graph matches the node tree, the XML cell centres and the legacy station chain | T-022 |

Add a row for every session. Keep it short; details belong in the ticket file.

---

## 4. Approval and open decisions

The plan Rev 4 defaults are recorded in `TICKETS.md` §7 and ADR-018:

1. Order `0 → 1 → 2 → {3, 4, 5} → 6`; events optional.
2. Yoke stays in `DTG4Simulator` until the pyg4ometry phase.
3. Events: Segment/Track/Jet only.
4. Compatibility until 3.0.
5. Phase 0 is five tickets (T-002 and T-004 folded into T-003).
6. CLI/YAML out of scope.

**Approved 2026-11-06.** Plan Rev 4 and the tickets were accepted, with
T-002 folded into T-003.

**Decided 2026-11-06 (T-007):** the refactor lives on
`feature/phase-0-safety-net`, branched from `enhancement-cacheObjects`.
Nothing merges into `main` until the maintainer approves; CI runs on every
branch push. The simulator side is `feature/T-005-tg-smoke`.
No history was rewritten.

---

## 5. Verification ledger

| Date | Command | Result |
|---|---|---|
| 2026-11-05 | `python prototype/parametric_poc.py` | all checks `0.000e+00`; 193 placements; box/tube alignment |
| 2026-11-05 | `python -m py_compile prototype/parametric_poc.py` | OK |
| 2026-11-06 | station build + `Cell→CMS` check on the checkout | 1.00 / 0.71 / 0.87 s; SL2 2.4749 cm and 0.7071 cm |
| 2026-11-06 | `python prototype/parametric_poc.py` after wire removal | all checks `0.000e+00`; 193 placements |
| 2026-11-06 | station build on the installed package | 1.25 / 2.26 / 1.66 s |
| 2026-11-06 | `pytest -q` (checkout) | 15 passed, 4 xfailed, 2 skipped, 8 s |
| 2026-11-06 | `pytest -q -m slow` (250 chambers) | all chambers green; only SL2 disagrees |
| 2026-11-06 | `test/benchmarks/bench_station.py` | import 1.32 s, parse 0.53 s, stations 0.65 / 0.46 / 0.57 s |
| 2026-11-06 | `geometry/smoke_tg.py` (checkout) | 621 placements, SL2 rotation present |
| 2026-11-06 | GitHub Actions `tests` on `feature/phase-0-safety-net` | success (run 42215563781) |
| 2026-11-06 | `pytest -q test/geometry/test_specs.py` | 22 passed |
| 2026-11-06 | `pytest -q` (37 tests) | 37 passed, 4 xfailed, 2 skipped |
| 2026-11-06 | `pytest -q` (55 tests, after T-011/T-012) | 55 passed, 4 xfailed, 2 skipped |
| 2026-11-06 | spec oracle, 250 chambers | worst 1.25e-3 cm, 1.1 s |

Update this ledger after each verification; do not claim a run that did not
happen.

---

## 6. How to update this file

1. At the start of a session: read §1, §4 and the last log row.
2. When a ticket changes state: add a log row and update the checkpoint table
   if a gate was met.
3. When blocked: add the reason and the unblock condition to §4.
4. At the end: set `Last updated`, the current checkpoint and the next action.
5. Keep it factual and dated; link files/tickets instead of repeating details.
