# PROGRESS — checkpoints and session log

**Last updated:** 2026-11-08
**Current checkpoint:** `CP-014 — the 2.9.0 deprecation release`
**Implementation status:** every delivery ticket closed, `main` at `v2.9.0` and
pushed; the 3.0 removal is planned and 2.9.0 already warns about it; Phase 6
(pyg4ometry) and the removal itself are deferred
**Board:** [`TICKETS.md`](TICKETS.md) · **Plan:** [`plan.md`](plan.md) Rev 5

---

## 1. Current status

| Item | Value |
|---|---|
| Phase | 0-5 complete (M0-M5 met); 6 and 7 planned, deferred |
| Current milestone | `CP-014`: the deprecation release (2.9.0); the removal itself is planned |
| Last completed | T-074 (the 2.9.0 deprecation release) |
| Integration branch | `main`, tagged `v2.9.0` and pushed; the simulator lives on `feature/T-005-tg-exporter` |
| Next | nothing scheduled; the removal is gated in `migration-3.0.md` (ADR-026) and waits for the window |
| Downstream | dtpr on `v2.6.0` (T-055); `DTG4Simulator` on `v2.7.0` (T-005) |
| Code changes | `super_layer.py` alias (T-005); `specs.py`, `sources/cms_xml.py` (T-010/T-011/T-022); `model.py` (T-020); `frames.py` (T-021); the legacy classes as views (T-022); `Station.overlay` + cache isolation (T-023); one build per chamber + lazy `DTGEOMETRY` (T-024); `build_detector` +
`Station.from_spec` (T-030); `serialize.py`, `constructors.py` and `export/` (T-050...T-052); tests, benchmark, CI; `mpldts/_deprecation.py` and the 2.9.0 warnings (T-074) |
| Library tests | `pytest -q`: 219 passed, 2 skipped, 3 deselected |
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
| CP-008 | M3 assemblies + extras | 2026-11-08 | done | custom 1-SL/5-SL stations plot; two-station assembly builds; CMS rectangles 0.0 vs `v2.3.0`; honeycomb pinned to W-2/S1/MB2; yoke hook data only |
| CP-009 | M4 downstream contract | 2026-11-08 | done | `test/downstream` 7 tests; dtpr pinned to `v2.6.0` and drawing through `DTObjectsPatch`; dtpr suite 22 passed / 2 pre-existing failures; 2.6.0 tagged |
| CP-010 | M5 authoring + `.tg` | 2026-11-08 | done | builders + JSON round trip; `.tg` parity: the same 621 placements, solids and rotations as the generator (0.0 cm); docs warning-free; 183 passed / 2 skipped |
| CP-011 | M6 GDML (future) | — | deferred | T-060 |
| CP-013 | The 3.0 removal plan recorded | 2026-11-08 | done | `migration-3.0.md` + ADR-026 + T-070...T-073; the inventory (~1.2-1.5k lines), the sequence, gates G1-G5 (the cell identity table included) and the anti-patterns |
| CP-012 | Close-out: simulator, naming seam, baseline, CLI | 2026-11-08 | done | `T-005`: 621 placements and 25896 cells unchanged, all 250 chambers in 11.6 s; `T-057`: `.tg` 2.7.0; `T-006`: 2-8 ms per station; `T-053`: CLI + 7 tests; 212 passed / 2 skipped; docs warning-free |
| CP-014 | The 2.9.0 deprecation release | 2026-11-08 | done | `T-074`: 9 legacy entry points warn and name their replacement, `Station.from_spec` and the `CMSXMLSource` pipeline stay silent; "Migrating to 3.0" in `runtime.rst`; 219 passed / 2 skipped; dtpr 22 + the 2 known failures; simulator smoke 621 placements; docs 0 warnings |

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
| 2026-11-08 | release | Phase 3 ships as 2.4.0: `mpldts.__version__` and `pyproject.toml` bumped, `docs/conf.py` reads the package version, tag `v2.4.0` on the branch tip (ADR-022); `main` untouched | `pytest -q` 154 passed / 2 skipped; `import mpldts` reports 2.4.0 | **M5 next** |
| 2026-11-08 | T-032, T-033 | M3 closes: `AttachmentSpec` + `StationSpec.attachments` + `Node.attachments` (separate from `children`), the CMS preset derives the honeycomb panel from the super layer records (1 cm clear, `G4_Al`, SL3 for MB4); `StructureSpec` + `DetectorSpec.structure` stay data (no node, no exporter); tests + docs | `pytest` 154 passed / 2 skipped; slow 3 passed (250 chambers); Sphinx warning-free | **M3 gate met**, tag `v2.4.0` |
| 2026-11-08 | T-031 | CMS preset: `presets/cms.py` owns `face_factor` + `add_frames` (`SectorRef`, `SL13Center`); `_face_from_pose` gives any station its face factor, so a mirrored custom chamber inverts right and all 250 CMS chambers keep the wheel/sector value; docs and `test_presets.py` | `pytest` 143 passed / 2 skipped; slow 3 passed (250 chambers); CMS rectangles 0.0 deviation vs `v2.3.0` (60 collections); Sphinx warning-free | `T-032` |
| 2026-11-07 | T-030 | Phase 3 starts: `build_detector` (the detector is the root node), `Station.from_spec` (the record is derived from the node tree, no CMS cache), shared `_add_natural_views`, specs no longer capped at the CMS counts, the patches pick the phi/eta super layers by orientation (`_is_turned`) instead of `number == 2`; custom 1-SL/5-SL tests and `docs/examples/custom_station.py` | `pytest` 134 passed / 2 skipped; slow 250-chamber oracle green; Sphinx warning-free | `T-031` |
| 2026-11-07 | T-026 | Release prep: 2.3.0 in `pyproject.toml` and `mpldts.__version__`, `docs/conf.py` reads the package version, new `docs/src/geometry/runtime.rst` documenting XML -> specs -> nodes -> frames, the legacy pages point at it; the untracked printer script is deleted; `refactor/v2-integration` cut from T-025 (`main` untouched) | `pytest` 111 passed / 2 skipped; Sphinx build succeeded with no warnings; both metadata sources report 2.3.0 | **Phase 3 planning** |
| 2026-11-08 | plan | read `DTPatternRecognition`: `Event` is a typed bag of config-declared `Particle` records (branches/expr/src, filters, sorters, cross-refs); the plotting bridge is a `(sl, l, w)` DataFrame into `StationsCache.get(dt_info=)`; artists are declared in YAML and composed by the PyQt visualizer. Phase 4 rescoped to the downstream contract (ADR-024/025); T-041/T-042 retired; T-053 back in scope | dtpr imports load against the `2.5.0` checkout; `AMDTSegments(reference_frame=...)` regression found (T-056) | `T-056` |
| 2026-11-08 | merge | the maintainer merged 2.3.0 -> 2.4.0 -> 2.5.0 into `main` (`2eac105`); the three feature branches are ancestors of `main` and tag `v2.5.0` sits on its tip; `enhancement-segments` untouched | `git merge-base --is-ancestor` on the three branches; `git describe` = `v2.5.0`; `origin/main` still `c341e65` | `T-005` |
| 2026-11-08 | T-055 | dtpr on `feature/T-055-dtpr-migration`: pin `v2.6.0`, `embed_simhits2axes_loc` and `embed_shower2axes_loc` build `DTObjectsPatch` objects instead of `scatter`/`plot`, env reinstalled from the tag | dtpr `pytest -q tests` 22 passed / 2 pre-existing failures (config include, particle hash); visualizer smoke green offscreen | `CP-009` (M4) met; `T-005` |
| 2026-11-08 | T-043 | `DTObjectsPatch`: points and polylines in any frame the station graph resolves, projected on the cell grid, so the local/global and inverted views come from `DTRelatedPatch`; `DTRelatedPatch` adds `Line2D` artists; `length` on the segment mark | `pytest -q` 204 passed / 2 skipped; objects on the cell centres (0.0 in both views, three SLs); segment paths pinned to 2.5.x | 2.6.0 tagged; `T-055` |
| 2026-11-08 | T-005, T-057 | the simulator generates stations through the exporter: `build_station` + `TgSink` with a `name_of` hook that keeps the names `StationSD`/`DriftCellSD` parse, and copy numbers that restart per volume; the yoke keeps the exporter's solid name and defines its own rotation; pin `v2.7.0` | smoke 621 placements against the installed tag; the 36 station files of the previous build match cell for cell (25896); all 250 chambers in 11.6 s; pytest 205 passed | `T-006`, `T-053` |
| 2026-11-08 | T-006, T-053 | the benchmark measures the model path too, and the baseline is recorded on merged code; `mpldts/cli.py` (info / convert / plot) with a console script, 7 tests and a docs section; 2.8.0 | 2-8 ms per station (< 20 ms target); the CLI converts and plots headless; pytest 212 passed / 2 skipped | maintainer: 3.0 or 2.x |
| 2026-11-08 | CP-013 | the 3.0 removal is planned instead of left as "someday": `migration-3.0.md` (inventory ~1.2-1.5k lines, sequence S1-S5, gates G1-G5 with the cell identity table, anti-patterns), ADR-026, and T-070...T-073 as deferred tickets | documentation only; the suite is untouched (212 passed) | the maintainer opens the 3.0 window |
| 2026-11-08 | T-040 | `test/downstream/test_dtpr_contract.py`: the surface dtpr imports (geometry + patches) exercised without ROOT or Qt, plus the cell-data contract documented on the runtime page | 7 tests, 2.1 s; `pytest -q` green; docs warning-free | `T-043` |
| 2026-11-08 | T-056 | `FrameView.available_frames` is the graph ids plus every name `_alias` accepts, derived from the frame basenames (0.13 ms per call); the legacy `AMDTSegments` reference frames resolve again; release 2.5.1 | `pytest -q` 185 passed / 2 skipped; the dtpr check that raised on 2.5.0 prints `Station`, `SL13Center` and `SL1` centres; dtpr plotting imports against the checkout | 2.5.1 tagged; `T-040` |
| 2026-11-08 | T-043 | opened the object-renderer ticket: `DTObjectsPatch` draws points and polylines given in any graph frame, projecting them like the cells, so dtpr drops its ad-hoc `scatter`/`plot`; `AMDTSegment.length` removes the fixed 20/40 mark; the dtpr side lands in T-055 | ticket + board only, no code yet | `T-056` |
| 2026-11-08 | T-050...T-054 | M5: `constructors.py` (four short constructors), `serialize.py` (JSON documents, strict reader), `export/` (`VolumeSink`, placement walk, `RecordingSink`, `TgSink`), cell material on the `CellGrid`, the tutorial example and the migration note; 2.5.0 | `pytest` 183 passed / 2 skipped; slow 3 passed; `.tg` parity 621 placements / 0.0 cm; Sphinx warning-free | **M5 gate met**, tag `v2.5.0` |

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
| 2026-11-07 | `pytest -q` (after T-030) | 134 passed, 2 skipped, 2 deselected, 27 s |
| 2026-11-07 | `pytest -q -m slow` (250 chambers, after T-030) | 2 passed, 136 deselected, 77 s |
| 2026-11-07 | `sphinx-build -b html docs` (after T-030) | build succeeded, no warnings; the runtime page carries `build_detector` and `Station.from_spec` |
| 2026-11-07 | `_is_turned` vs `super_layer.number == 2` on 3 chambers | same super layer in all of them |
| 2026-11-07 | GitHub Actions `tests` on `feature/phase-3-assemblies` (T-030) | success (run 42314584878) |
| 2026-11-08 | `git tag v2.3.0` on `refactor/v2-integration` (`8997ad7`) | annotated tag created and pushed (ADR-022) |
| 2026-11-08 | `pytest -q` (after T-031) | 143 passed, 2 skipped, 3 deselected, 62 s |
| 2026-11-08 | `pytest -q -m slow` (after T-031) | 3 passed, 145 deselected, 145 s |
| 2026-11-08 | patch rectangles, `v2.3.0` vs T-031 (60 collections) | worst vertex deviation 0.0 in display coordinates |
| 2026-11-08 | `sphinx-build -b html docs` (after T-031) | build succeeded, no warnings; `presets.cms` documented |
| 2026-11-08 | `pytest -q` (after T-033) | 154 passed, 2 skipped, 3 deselected, 59 s |
| 2026-11-08 | `pytest -q -m slow` (after T-033) | 3 passed, 156 deselected, 157 s |
| 2026-11-08 | honeycomb panel, W-2/S1/MB2 | 265.8 x 250.1 x 11.8 cm at z 2.675, `G4_Al` (simulator formula) |
| 2026-11-08 | `sphinx-build -b html docs` (after T-033) | build succeeded, no warnings |
| 2026-11-08 | `pytest -q` (after T-054) | 183 passed, 2 skipped, 3 deselected, 28-41 s |
| 2026-11-08 | `pytest -q -m slow` (after T-054) | 3 passed, 184 deselected, 110 s |
| 2026-11-08 | `.tg` parity, `station_W0_Sec1_St1.tg` vs `TgSink` | the same 621 placements, solids, materials and rotations; worst position 0.0 cm at 1e-4 cm |
| 2026-11-08 | JSON round trip, CMS chamber -2/1/MB2 with honeycomb | `to_dict(from_dict(document)) == document`; 13 kB per chamber |
| 2026-11-08 | `sphinx-build -E -b html docs` (after T-054) | build succeeded, no warnings |
| 2026-11-08 | `python -c "import mpldts; print(mpldts.__version__)"` | 2.5.0 |
| 2026-11-08 | `pytest -q` (after T-074) | 219 passed, 2 skipped, 3 deselected, 57 s |
| 2026-11-08 | `sphinx-build -E -b html docs` (after T-074) | build succeeded, no warnings |
| 2026-11-08 | `python -c "import mpldts; print(mpldts.__version__)"` (after T-074) | 2.9.0 |
| 2026-11-08 | dtpr `pytest -q tests` on the 2.9.0 checkout | 22 passed / 2 pre-existing failures (config include, particle hash) |
| 2026-11-08 | simulator `smoke_tg.py` against the working tree | 621 placements, 3 cell volumes, 620 cells; the `name_of` hook warns and the run is unchanged |
| 2026-11-08 | GitHub Actions `tests` on `feature/phase-5-authoring` | success (run 42487358163) |
| 2026-11-08 | merge state (`git log`, `git describe`, `--is-ancestor`) | `main` `2eac105`; the three feature branches all ancestors; `origin/main` `c341e65` (not pushed) |
| 2026-11-08 | dtpr imports against the `2.5.0` checkout | `mpldts 2.5.0`; `dt_plot_functions`, `artist_gui_manager`, `local_plotter`, `base` all import |
| 2026-11-08 | dtpr contract smoke (`StationsCache`, overlay, `DTStationPatch`, `MultiDTSegmentsPatch`) | station `W0/S1/MB1`; cell ids 1..50; `dt_info` time 400 reached the cell; patches for phi and eta with `.station` |
| 2026-11-08 | `AMDTSegments(reference_frame="Station"/"SL13Center")` | 2.5.0 raises `ValueError: ... not available in the parent transformer`; 2.2.0-beta works -> T-056 |

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
