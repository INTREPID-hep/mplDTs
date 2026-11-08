# TICKETS — internal issue tracker

**Project:** mplDTs geometry refactor
**Last updated:** 2026-11-08
**Plan:** [`plan.md`](plan.md) Rev 5
**State:** Phases 0-3 and 5 merged into `main` and pushed; the downstream packages, the simulator and the CLI are on `v2.7.0`/`v2.8.0` (`T-005`, `T-053`, `T-055`, `T-057`); all tickets closed except `T-060` (deferred)
**Canonical backlog:** this file + `tickets/T-0xx-*.md` for refined tickets
**Checkpoints:** [`PROGRESS.md`](PROGRESS.md)
**Workflow:** [`workflow.md`](workflow.md)

---

## 1. How this works

- A **ticket** is the unit of work (`T-0xx`). Refined tickets have a file in
  `tickets/`; unrefined future work lives only as a row in §6.
- A ticket moves: `proposed` → `ready` → `doing` → `review` → `done`.
  `blocked`, `deferred` and `retired` are terminal-until-reopened states.
- Every ticket maps to **one branch** `feature/T-0xx-<slug>` and **one PR**.
- Every commit starts with the ticket id: `T-001: add pytest scaffolding`.
- `PROGRESS.md` records checkpoints and the session log; it is the file to read
  to know "where are we?".
- **The maintainer approves the plan and tickets before any implementation.**
  Approved 2026-11-06: Phase 0 tickets are `ready` or `doing`.

Status legend:

| Status | Meaning |
|---|---|
| `proposed` | written, awaiting maintainer review |
| `ready` | approved, can be started |
| `doing` | branch exists, work in progress |
| `review` | PR open, awaiting review |
| `done` | merged and verified |
| `blocked` | cannot proceed; reason recorded |
| `deferred` | intentionally out of the current delivery |
| `retired` | folded into another ticket; do not implement |
| `backlog` | one-line placeholder, not refined |

---

## 2. Current milestone

**M5 — Authoring, JSON and the `.tg` sink.** Gate: JSON -> validate -> build
-> plot -> `.tg` works end to end; one CMS station `.tg` matches the current
generator; no pyg4ometry dependency. M2 is done (`CP-007`, tag `v2.3.0` on
`refactor/v2-integration`), M3 is done (`CP-008`, tag `v2.4.0` on
`feature/phase-3-assemblies`), and M5 is done (`CP-010`, tag `v2.5.0` on
`feature/phase-5-authoring`): T-050...T-054 landed. All three are merged into
`main` (`2eac105`, 2026-11-08). Phase 4 is no longer an event layer: it is
the downstream contract with `DTPatternRecognition` (ADR-024), `CP-009`.
Phase 6 (`CP-011`) is deferred.

**Current checkpoint:** `CP-014 — the deprecation release` (2026-11-08):
`T-074` (2.9.0) on top of `T-005` (the simulator on the exporter), `T-057` (the
`.tg` naming seam, 2.7.0), `T-006` (the baseline on merged code) and `T-053` (the
thin CLI, 2.8.0). Every delivery ticket in §3 is closed: the removal is now
visible in a consumer's test run, one warning at a time. Two things stay planned and deferred: `T-060`
(pyg4ometry + GDML) and the removal itself, which has content, a sequence and
gates in `migration-3.0.md` (ADR-026, `T-070`, `T-072`, `T-073`). Nothing runs
until the maintainer opens that window.

---

## 3. Review queue (refined tickets)

| ID | Title | Phase | Status | Depends | File |
|---|---|---|---|---|---|
| T-001 | pytest scaffolding | 0 | done | — | [T-001](tickets/T-001-pytest-scaffolding.md) |
| T-003 | Transform invariant + oracle harness + node snapshot | 0 | done | T-001 | [T-003](tickets/T-003-cms-oracle.md) |
| T-005 | Downstream migration + `.tg` smoke | 0 | done | T-001, T-052, T-057 | [T-005](tickets/T-005-downstream-pin-tg-smoke.md) |
| T-006 | Benchmark harness + merged-code baseline | 0 | done | T-001 | [T-006](tickets/T-006-benchmark-harness.md) |
| T-007 | Branch baseline + CI | 0 | done | — | [T-007](tickets/T-007-branch-baseline-ci.md) |
| T-010 | Geometry specs | 1 | done | T-003 | [T-010](tickets/T-010-geometry-specs.md) |
| T-011 | CMS XML source | 1 | done | T-010 | [T-011](tickets/T-011-cms-xml-source.md) |
| T-012 | Spec oracle over 250 chambers | 1 | done | T-011 | [T-012](tickets/T-012-spec-oracle.md) |
| T-020 | Runtime topology + `build_station` | 2 | done | T-010, T-011 | [T-020](tickets/T-020-runtime-topology.md) |
| T-021 | `FrameGraph` + `FrameView` | 2 | done | T-020 | [T-021](tickets/T-021-frame-graph.md) |
| T-022 | Legacy constructors delegate; `BUG-01` fixed | 2 | done | T-020, T-021 | [T-022](tickets/T-022-legacy-delegation.md) |
| T-023 | Immutable cache + per-event overlay; `BUG-02` fixed | 2 | done | T-022 | [T-023](tickets/T-023-immutable-overlay.md) |
| T-024 | Performance pass + lazy `DTGEOMETRY` shim; `BUG-03` fixed | 2 | done | T-022, T-023 | [T-024](tickets/T-024-performance-shim.md) |
| T-025 | Triage the visual scripts in `test/` | 2 | done | T-022 | [T-025](tickets/T-025-visual-scripts.md) |
| T-026 | Release 2.3: version metadata + runtime docs | 2 | done | T-022...T-025 | [T-026](tickets/T-026-release-2.3.md) |
| T-030 | `DetectorSpec` assemblies + custom 1-SL/5-SL stations | 3 | done | T-020, T-021, T-022, T-026 | [T-030](tickets/T-030-assemblies.md) |
| T-031 | CMS preset remainder + custom-station plotting | 3 | done | T-030 | [T-031](tickets/T-031-cms-preset-plotting.md) |
| T-032 | Honeycomb as a station attachment | 3 | done | T-030 | [T-032](tickets/T-032-honeycomb.md) |
| T-033 | Yoke `StructureSpec` data hook | 3 | done | T-030 | [T-033](tickets/T-033-yoke-hook.md) |
| T-050 | Short constructors for specs | 5 | done | T-030 | [T-050](tickets/T-050-constructors.md) |
| T-051 | JSON documents + strict validation | 5 | done | T-030 | [T-051](tickets/T-051-json-schema.md) |
| T-052 | `VolumeSink` + `TgSink` + `.tg` parity | 5 | done | T-030 | [T-052](tickets/T-052-tg-sink.md) |
| T-054 | Docs, tutorial, migration note, 2.5.0 | 5 | done | T-050...T-052 | [T-054](tickets/T-054-docs-tutorial.md) |
| T-040 | Downstream cell-data contract + `test/downstream` | 4 | done | T-022, T-052 | [T-040](tickets/T-040-downstream-contract.md) |
| T-043 | Object renderers (`DTObjectsPatch`) | 4 | done | T-022, T-023 | [T-043](tickets/T-043-object-renderers.md) |
| T-053 | Thin CLI (`convert`, `info`, `plot`) | 5 | done | T-051, T-052 | [T-053](tickets/T-053-cli.md) |
| T-055 | `DTPatternRecognition` migration to 2.6.0 | 4 | done | T-040, T-043, T-056 | [T-055](tickets/T-055-dtpr-migration.md) |
| T-056 | `FrameView.available_frames` accepts legacy aliases | 4 | done | T-021 | [T-056](tickets/T-056-frame-aliases.md) |
| T-057 | The `.tg` naming seam (`TgSink.name_of`, copy numbers) | 5 | done | T-052 | [T-057](tickets/T-057-tg-names.md) |
| T-060 | pyg4ometry backend + GDML | 6 | deferred | T-052 | [T-060](tickets/T-060-pyg4ometry-backend.md) |
| T-070 | Remove the legacy view layer | 7 | deferred | T-071, T-073 | [T-070](tickets/T-070-legacy-layer-removal.md) |
| T-071 | The per-event contract replaces `StationsCache.get(dt_info=...)` | 7 | deferred | T-040 | [T-071](tickets/T-071-event-contract.md) |
| T-072 | The volume names stop being the C++ API | 7 | deferred | T-005, T-073 | [T-072](tickets/T-072-volume-names.md) |
| T-073 | The 3.0.0 release and the downstream lockstep | 7 | deferred | T-070...T-072 | [T-073](tickets/T-073-release-3.0.md) |
| T-074 | The 2.9.0 deprecation release | 7 | done | — | [T-074](tickets/T-074-deprecations-2.9.md) |

**Retired:** T-002 and T-004 (folded into T-003), T-008 and T-009 (covered by design
doc §14–§15), and the old T-010 protocol (rewritten as the specs ticket).

**M0 complete on `feature/phase-0-safety-net` (2026-11-06)** and merged into
`main` with the rest. T-002 was folded into T-003. T-005 and T-006 closed
on 2026-11-08 on merged code (2.7.0 / 2.8.0), so M0 is fully closed: pytest,
the oracle, an invariant, the `.tg` smoke in the downstream repository and
a benchmark that reproduces.

---

## 4. Phase 0 — Safety net (M0)

| ID | Ticket | Exit |
|---|---|---|
| T-001 | pytest scaffolding | `pytest` collects; env works |
| T-003 | Transform invariant + oracle harness | `Cell→CMS` + node snapshot; SL2 `xfail(BUG-01)` |
| T-005 | Downstream pin + `.tg` smoke | version pinned; one station `.tg` |
| T-006 | Benchmark harness | baseline reproducible |
| T-007 | Branch baseline + CI | `main` reconciled; Actions runs tests |

M0 is reached when T-001, T-003, T-005, T-006 and T-007 are `done`.

---

## 5. Milestones

| Milestone | Gate | Tickets |
|---|---|---|
| M0 Safety net | tests + invariant + `.tg` smoke + CI | T-001, T-003, T-005, T-006, T-007 |
| M1 Specs + source | spec oracle green for all 250 chambers | T-010, T-011, T-012 |
| M2 Runtime parity | public API oracle green; `< 20 ms`; no XML in model; `test/` triaged | T-020…T-025 |
| M3 Assemblies + extras | custom stations; honeycomb; yoke data hook | T-030…T-033 |
| M4 Downstream contract | dtpr contract test green; dtpr pinned to a tag; objects drawn by mplDTs patches | T-040, T-043, T-055, T-056 |
| M5 Authoring + `.tg` | JSON → build → plot → `.tg`; parity | T-050, T-051, T-052, T-054 |
| M6 (future) GDML | pyg4ometry optional extra | T-060 |
| M7 (planned) 3.0 removal | no legacy API left; both downstream packages on 3.0; the cell identity table matches | T-070...T-073 ([plan](migration-3.0.md)) |

---

## 6. Backlog (unrefined; one line each)

These are placeholders. Refine into a ticket file only when the phase is ready
and the maintainer approves.

| ID | Phase | Summary |
|---|---|---|

*(empty — every remaining item is a refined ticket above, or retired below.)*

**Deferred:** T-060 (pyg4ometry + GDML) — deferred until ADR-008/ADR-014 are
revisited, and kept as an idea only; T-070...T-073 — the 3.0 removal, fully
planned in `migration-3.0.md` (ADR-026) and started only when both downstream
packages can move in the same window. **Retired:** T-041 and T-042 — the event
model lives in `DTPatternRecognition` (ADR-024).

---

## 7. Resolved defaults (2026-11-06)

The previous open questions are closed with defaults. Changing one requires an
ADR, not a silent edit.

1. **Order:** `0 → 1 → 2 → {3, 4, 5} → 6`. Phase 4 is the downstream contract
   (ADR-024) and is off the critical path.
2. **Yoke:** stays in `DTG4Simulator` until the pyg4ometry phase; the model
   only carries a data hook.
3. **Events:** none in mplDTs; `DTPatternRecognition` owns the event model
   (ADR-024).
4. **Compatibility:** keep the old constructors and plotting API until 3.0.
5. **Phase 0 granularity:** five tickets; T-004 and T-002 are folded into T-003.
6. **CLI/YAML:** YAML stays out; a thin JSON CLI is in scope (T-053).

---

## 8. Done (planning artefacts)

| ID | Output | Status |
|---|---|---|
| D-01 | Design review Rev 3 | done |
| D-02 | Parametric prototype v2 (box + tube) | done |
| D-03 | Backend seam in the prototype (`VolumeSink`/`RecordingSink`) | done |
| D-04 | `.agents` workspace | done |
| D-05 | Ticket system + progress checkpoints | done |
| D-06 | Plan Rev 4 review/cleanup | done (this revision) |
| D-07 | Wire/cell terminology correction (ADR-019) | done |

---

## 9. Deferred / retired

| ID | Ticket | Why |
|---|---|---|
| T-002 | Public-API snapshot | Folded into T-003; the XML is the reference |
| T-004 | Transform invariant (separate) | Folded into T-003 |
| T-008 | Event object design spike | Design doc §15 covers it |
| T-009 | Physical extras design spike | Design doc §14 covers it |
| T-041 | `Track`/`Jet`/`Cone` + collections | The event model lives in `DTPatternRecognition` (ADR-024) |
| T-042 | Event plotting adapters + event JSON | Same; dtpr already has both |
| T-060 | pyg4ometry backend + GDML | Deferred by ADR-008/ADR-014; kept as an idea (2026-11-08) |

---

## 10. ID allocation

- `T-001…T-009`: Phase 0 (T-002, T-004, T-008, T-009 retired).
- `T-010…T-019`: Phase 1 (T-010 rewritten as specs; T-011/T-012 source/oracle).
- `T-020…T-029`: Phase 2.
- `T-030…T-039`: Phase 3.
- `T-040…T-049`: Phase 4 (downstream contract; T-041/T-042 retired).
- `T-050…T-059`: Phase 5 (T-053 CLI, in scope).
- `T-060…`: Phase 6 (future).
- `D-0xx`: planning artefacts, not implementation.

Do not reuse an id. If a ticket is split, create `T-0xxa`, `T-0xxb`.
