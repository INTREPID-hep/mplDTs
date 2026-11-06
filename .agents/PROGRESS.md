# PROGRESS — checkpoints and session log

**Last updated:** 2026-11-07
**Current checkpoint:** `CP-007 — M2 runtime parity`
**Implementation status:** Phases 0-2 complete on `refactor/v2-integration`
(release 2.3.0); Phase 3 planned
**Board:** [`TICKETS.md`](TICKETS.md) · **Plan:** [`plan.md`](plan.md)

---

## 1. Current status

| Item | Value |
|---|---|
| Phase | 2 complete (T-020...T-025 done) |
| Current milestone | M2 — Runtime parity (gate met 2026-11-06) |
| Last completed | T-026 (release 2.3.0: one version string, runtime docs page) |
| Integration branch | `refactor/v2-integration` (T-025 + T-026); `main` untouched |
| Next | Phase 3: `T-030` on `feature/phase-3-assemblies` |
| Code changes | `super_layer.py` alias (T-005); `specs.py`, `sources/cms_xml.py` (T-010/T-011/T-022); `model.py` (T-020); `frames.py` (T-021); the legacy classes as views (T-022); `Station.overlay` + cache isolation (T-023); one build per chamber + lazy `DTGEOMETRY` (T-024); tests, benchmark, CI |
| Library tests | `pytest -q`: 111 passed, 2 skipped, 2 deselected |
| Builder cost | 7.5 ms/station (spec -> `Node` tree); a legacy `Station` is 2-6 ms/station (first build per chamber 22-63 ms, then cached) |
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
| CP-007 | M2 runtime parity | 2026-11-06 | done | public API oracle green; 6.1 / 2.1 / 3.0 ms per station (< 20 ms); no XML in the model; `test/` triaged (`docs/examples/` + headless smoke test) |
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
| 2026-11-06 | T-022 | Phase 2 compatibility: the four legacy classes are views over `CMSXMLSource` + `build_station` + `FrameView`; the plotting frames live on the station graph; standalone `SuperLayer(rawId)`/`Layer(rawId)` kept; data attributes stay verbatim XML | `pytest` 100 passed / 2 skipped; slow 250-chamber sweeps green; `DTStationPatch` rectangles and the .tg inputs bit-identical to the old code; 1009 -> 64 ms per station | T-023 |
| 2026-11-06 | T-023 | Phase 2 immutability: `Station.overlay()` shares the node tree, the graph and the raw-id index and rebuilds only the legacy view objects; `StationsCache.get` returns an overlay instead of writing on the cached station (`BUG-02`); stale docs anchors fixed | `pytest` 102 passed / 2 skipped; slow sweeps green; overlay 7 ms + 5 ms for 704 attributes vs 32 ms for a full station | T-024 |
| 2026-11-06 | T-024 | Phase 2 performance: `DTGEOMETRY` is a lazy proxy (no XML parse at import); one build per chamber shared by every `Station`; wire locals parsed once per chamber; `Bounds`/`Wires` read explicit attribute names (`BUG-03`); docs anchors refreshed | `pytest` 105 passed / 2 skipped; slow sweeps green; import 2.83 -> 0.96 s; station 6.1 / 2.1 / 3.0 ms | T-025 |
| 2026-11-06 | T-025 | Phase 2 cleanup: six documented examples moved to `docs/examples/` (five patch demos plus the `TransformManager` one), seven demos + the debug script + a generated SVG deleted, both `test/`-relative `literalinclude` path sets updated, one headless smoke test for every example | `pytest` 111 passed / 2 skipped; `test_examples.py` 6 passed; Sphinx build succeeded | **M2 gate met**; Phase 3 |
| 2026-11-07 | T-026 | Release prep: 2.3.0 in `pyproject.toml` and `mpldts.__version__`, `docs/conf.py` reads the package version, new `docs/src/geometry/runtime.rst` documenting XML -> specs -> nodes -> frames, the legacy pages point at it; the untracked printer script is deleted; `refactor/v2-integration` cut from T-025 (`main` untouched) | `pytest` 111 passed / 2 skipped; Sphinx build succeeded with no warnings; both metadata sources report 2.3.0 | **Phase 3 planning** |

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
| 2026-11-06 | `pytest -q` (100 tests, after T-022) | 100 passed, 2 skipped, 2 deselected, 31 s |
| 2026-11-06 | `pytest -q` (102 tests, after T-023) | 102 passed, 2 skipped, 2 deselected, 28 s |
| 2026-11-06 | `pytest -q` (105 tests, after T-024) | 105 passed, 2 skipped, 2 deselected, 41 s |
| 2026-11-06 | `bench_station.py` (after T-024) | import 0.96 s; 6.1 / 2.1 / 3.0 ms per station |
| 2026-11-06 | `pytest -q -m slow` (250 chambers, after T-024) | 2 passed, 107 deselected, 140 s |
| 2026-11-06 | `pytest -q -m slow` (250 chambers, after T-023) | 2 passed, 104 deselected, 160 s |
| 2026-11-06 | overlay vs full station build | 7 ms + 5 ms (704 cell attrs) vs 32 ms |
| 2026-11-06 | `pytest -q -m slow` (250 chambers) | 2 passed, 152 s; SL2 matches the XML |
| 2026-11-06 | patch rectangles, old vs new code (18 cases) | worst vertex deviation 0.0 cm |
| 2026-11-06 | station build, old vs new code | 1009.3 -> 63.8 ms/station |
| 2026-11-06 | `pytest -q` (111 tests, after T-025) | 111 passed, 2 skipped, 2 deselected, 25-33 s |
| 2026-11-06 | `pytest -q test/geometry/test_examples.py` | 6 passed, 9-20 s |
| 2026-11-06 | `sphinx-build -b html docs` (Sphinx 9.1.1) | build succeeded; examples and images render |
| 2026-11-07 | `pytest -q` (after T-026) | 111 passed, 2 skipped, 2 deselected |
| 2026-11-07 | `sphinx-build -b html docs` (after T-026) | build succeeded, no warnings; `runtime.html` carries all 10 new autodoc objects |
| 2026-11-07 | `python -c "import mpldts; print(mpldts.__version__)"` | 2.3.0 |

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
