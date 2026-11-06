# TICKETS — internal issue tracker

**Project:** mplDTs geometry refactor
**Last updated:** 2026-11-06
**Plan:** [`plan.md`](plan.md) Rev 4
**State:** Phase 2 implementing — T-020, T-021 done 2026-11-06
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

**M2 — Runtime parity.** Gate: public-API oracle green, `< 20 ms/station`,
no XML in the model, `test/` triaged. T-020 (topology + `build_station`),
T-021 (`FrameGraph`/`FrameView`) and T-022 (legacy delegation, `BUG-01`) are
done; T-023...T-025 remain.

**Current checkpoint:** `CP-006 — M1 specs + source` complete; CP-007 (M2)
in progress.

---

## 3. Review queue (refined tickets)

| ID | Title | Phase | Status | Depends | File |
|---|---|---|---|---|---|
| T-001 | pytest scaffolding | 0 | done | — | [T-001](tickets/T-001-pytest-scaffolding.md) |
| T-003 | Transform invariant + oracle harness + node snapshot | 0 | done | T-001 | [T-003](tickets/T-003-cms-oracle.md) |
| T-005 | Downstream pin + `.tg` smoke | 0 | proposed | T-001 | [T-005](tickets/T-005-downstream-pin-tg-smoke.md) |
| T-006 | Benchmark harness | 0 | proposed | T-001 | [T-006](tickets/T-006-benchmark-harness.md) |
| T-007 | Branch baseline + CI | 0 | done | — | [T-007](tickets/T-007-branch-baseline-ci.md) |
| T-010 | Geometry specs | 1 | done | T-003 | [T-010](tickets/T-010-geometry-specs.md) |
| T-011 | CMS XML source | 1 | done | T-010 | [T-011](tickets/T-011-cms-xml-source.md) |
| T-012 | Spec oracle over 250 chambers | 1 | done | T-011 | [T-012](tickets/T-012-spec-oracle.md) |
| T-020 | Runtime topology + `build_station` | 2 | done | T-010, T-011 | [T-020](tickets/T-020-runtime-topology.md) |
| T-021 | `FrameGraph` + `FrameView` | 2 | done | T-020 | [T-021](tickets/T-021-frame-graph.md) |
| T-022 | Legacy constructors delegate; `BUG-01` fixed | 2 | done | T-020, T-021 | [T-022](tickets/T-022-legacy-delegation.md) |
| T-025 | Triage the visual scripts in `test/` | 2 | proposed | T-022 | [T-025](tickets/T-025-visual-scripts.md) |
| T-060 | pyg4ometry backend + GDML | 6 | deferred | T-052 | [T-060](tickets/T-060-pyg4ometry-backend.md) |

**Retired:** T-002 and T-004 (folded into T-003), T-008 and T-009 (covered by design
doc §14–§15), and the old T-010 protocol (rewritten as the specs ticket).

**M0 complete on `feature/phase-0-safety-net` (2026-11-06).** All six Phase 0
tickets are `done`; the branch is not merged into `main` and waits for the
maintainer. T-002 was folded into T-003.

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
| M4 Event annotations (optional) | segments/tracks/jets; legacy API | T-040…T-042 |
| M5 Authoring + `.tg` | JSON → build → plot → `.tg`; parity | T-050, T-051, T-052, T-054 |
| M6 (future) GDML | pyg4ometry optional extra | T-060 |

---

## 6. Backlog (unrefined; one line each)

These are placeholders. Refine into a ticket file only when the phase is ready
and the maintainer approves.

| ID | Phase | Summary |
|---|---|---|

| T-023 | 2 | Immutable cache + per-event overlay |
| T-024 | 2 | Performance pass + `DTGEOMETRY` shim + remove XML imports |
| T-030 | 3 | `DetectorSpec` assemblies + custom 1-SL/5-SL stations |
| T-031 | 3 | CMS preset remainder (virtual frames, MB4) + plotting orientation |
| T-032 | 3 | Honeycomb as station attachment (`SolidSpec`) |
| T-033 | 3 | Yoke `StructureSpec` data hook (no CSG, no export) |
| T-040 | 4 | Annotation base + `Segment` refactor |
| T-041 | 4 | `Track` + `Jet`/`Cone` + collections |
| T-042 | 4 | Event plotting adapters + event JSON |
| T-050 | 5 | Convenience builders |
| T-051 | 5 | JSON schema + validation (JSON only) |
| T-052 | 5 | `VolumeSink` + `TgSink` + `.tg` parity |
| T-054 | 5 | Docs, tutorial, migration note |

**Deferred:** T-053 (CLI) — no user yet; add only on request. T-060
(pyg4ometry + GDML) — deferred until M5.

---

## 7. Resolved defaults (2026-11-06)

The previous open questions are closed with defaults. Changing one requires an
ADR, not a silent edit.

1. **Order:** `0 → 1 → 2 → {3, 4, 5} → 6`. Phase 4 (events) is optional and
   off the critical path.
2. **Yoke:** stays in `DTG4Simulator` until the pyg4ometry phase; the model
   only carries a data hook.
3. **Events:** Segment/Track/Jet only; no hits/digis until asked.
4. **Compatibility:** keep the old constructors and plotting API until 3.0.
5. **Phase 0 granularity:** five tickets; T-004 and T-002 are folded into T-003.
6. **CLI/YAML:** out of scope. JSON + Python builders only.

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
| T-053 | CLI | JSON + Python builders are enough for now |
| T-060 | pyg4ometry backend + GDML | Deferred by ADR-008/ADR-014 |

---

## 10. ID allocation

- `T-001…T-009`: Phase 0 (T-002, T-004, T-008, T-009 retired).
- `T-010…T-019`: Phase 1 (T-010 rewritten as specs; T-011/T-012 source/oracle).
- `T-020…T-029`: Phase 2.
- `T-030…T-039`: Phase 3.
- `T-040…T-049`: Phase 4 (optional).
- `T-050…T-059`: Phase 5 (T-053 deferred).
- `T-060…`: Phase 6 (future).
- `D-0xx`: planning artefacts, not implementation.

Do not reuse an id. If a ticket is split, create `T-0xxa`, `T-0xxb`.
