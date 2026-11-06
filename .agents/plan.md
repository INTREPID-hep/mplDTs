# Plan — phased delivery (revision 4)

**Last updated:** 2026-11-06
**Design:** [`../docs/design/generalization-plan.md`](../docs/design/generalization-plan.md) Rev 4
**Board:** [`TICKETS.md`](TICKETS.md) · **Checkpoints:** [`PROGRESS.md`](PROGRESS.md)
**Status:** **M0 (Phase 0) done on `feature/phase-0-safety-net` — not merged; Phase 1 next**

Guiding rule: **each phase is shippable and ends with a green test suite.** Do
not start a phase before the previous one meets its exit criteria.

```
Phase 0  safety net                        1–2 days
      │
      ▼
Phase 1  specs + CMS source                4–6 days
      │
      ▼
Phase 2  runtime model + compatibility     7–10 days
      │
      ├──────────────► Phase 3  assemblies + custom stations + extras
      ├──────────────► Phase 4  event annotations (optional)
      └──────────────► Phase 5  authoring + JSON + .tg sink
                             │
                             ▼
                     Phase 6  FUTURE: pyg4ometry + GDML (deferred)
```

Phases 3, 4 and 5 can run in parallel **after Phase 2**. Phase 4 is optional
and may be dropped without affecting the geometry delivery.

---

## What changed in revision 4

Revision 3 was internally inconsistent and larger than the problem. This
revision fixes the plan, not the design:

1. **Phase 1 was a half-refactor.** It removed XML from classes without having
   specs, then Phase 2 rewrote the classes again. Phase 1 now builds the
   **specs + CMS source** and validates them with the oracle; the runtime
   classes are untouched until Phase 2. No double work, same safety.
2. **The CMS adapter was in Phase 2 and the CMS preset in Phase 3.** One CMS
   source/preset is built in Phase 1 and extended in Phase 3 (virtual frames,
   MB4 13/14 only).
3. **The oracle cannot run in Phase 0.** There are no specs yet. Phase 0 keeps
   the current transform invariant (`Cell → CMS`) and the oracle harness; the
   same harness is reused against the spec path in Phase 1.
4. **`VolumeSink` had no consumer until Phase 5.** Building a backend seam
   before the first backend is speculative. The seam is introduced with
   `TgSink` in Phase 5; ADR-008 is amended.
5. **CLI and YAML are dropped.** JSON authoring is enough; a CLI can be a thin
   wrapper later if anyone asks. YAML adds a dependency for no current user.
6. **Event objects are optional and off the critical path.** They reuse the
   frame graph but are not needed for the detector refactor.
7. **Baselines were stale.** The branch already caches XML indexes: measured
   0.7–1.0 s/station on the checkout, versus 1.3–2.3 s for the installed
   package. The old 2.3–4.1 s and the profile numbers are retired.
8. **Wire is not a separate object.** The XML `<Wire>` is the cell entry
   (number + position); separate wire objects are removed from specs, JSON, tests
   and docs (ADR-019).
9. **Stale artefacts are removed:** `generalization-plan-v1.md`,
   `.agents/log/plan-v2.md`, `prototype/parametric_poc_v1.py`,
   `.agents/tasks.md`, and the design-only tickets T-008/T-009. One plan, one
   design, one board.
10. **T-002 is folded into T-003.** The XML already carries `GlobalPosition`,
    `Bounds` and `NormalVector` for every node, so the representative-chamber
    snapshot is checked against the XML instead of a second golden JSON. One
    file to maintain, no `--update-golden` path.

---

## Phase 0 — Safety net (1–2 days) · M0

**Goal:** make the refactor measurable and reversible.

**Tickets:** T-001, T-003, T-005, T-006, T-007.

**Deliverables**

- pytest scaffolding and `test/geometry/`.
- Transform invariant `Cell → CMS` vs the XML `GlobalPosition`, with
  `BUG-01` (SL2) `xfail(strict=True)`. This test is the oracle harness; the
  spec path will reuse it in Phase 1. It also pins the node fields
  (id, number, bounds, direction, local pose) of representative chambers to
  the XML, so no separate golden file is needed.
- Downstream version pin + one-station `.tg` smoke test.
- Benchmark script with reproducible median timings.
- Branch baseline + CI + PR template.

**Exit criteria (M0)**

- `pytest` green except the documented `xfail`.
- The invariant and the node fields run against the checkout, not the
  installed package.
- One CMS station `.tg` is generated and asserted.
- CI runs the tests; the baseline is reproducible.

**Do not start Phase 1 before M0.**

---

## Phase 1 — Specs + CMS source (4–6 days) · M1

**Goal:** the declarative description exists and reproduces CMS, while the old
runtime classes stay untouched.

**Tickets:** T-010, T-011, T-012.

**Deliverables**

- `mpldts/geometry/specs.py`: `Pose`, `Shape`/`Box`/`Tube`, `CellGrid`,
  `LayerSpec`, `SuperLayerSpec`, `StationSpec`,
  `DetectorSpec`, validation.
- `mpldts/geometry/sources/cms_xml.py`: parse-time indexes for chambers, SLs,
  layers and cell centres; explicit attribute names (no `attrib.values()`);
  parent-relative poses derived from the XML local positions + orientation;
  cell `GlobalPosition` kept only as `metadata["reference"]`.
- The oracle test over all 250 chambers, comparing **spec-derived** cell
  centres with the XML globals at `1e-3` cm.
- No new XML/ElementTree import outside `sources/`; the old model classes
  keep theirs until Phase 2.
- No changes to `Station`, `SuperLayer`, `Layer`, `DriftCell`, the patches or
  the generator.

**Exit criteria (M1)**

- Spec oracle green for all 250 chambers.
- The SL2 pose is correct in the specs (the XML values agree).
- Unknown chamber/layer/cell raises a clear `KeyError`/`ValueError`.
- No runtime dependency added; no backend import.

---

## Phase 2 — Runtime model + compatibility (7–10 days) · M2

**Goal:** the new model is the runtime model, reproduces CMS through the public
API, and the old classes delegate to it.

**Tickets:** T-020, T-021, T-022, T-023, T-024, T-025.

**Deliverables**

- `Node`/topology with optional solids; `build_station`; top-down
  `world_pose`. Detector assemblies are Phase 3.
- `FrameGraph` + `FrameView`, scoped aliases, virtual frames; the old
  `transformer` API keeps working.
- Legacy constructors delegate to the source + builder; `"SuperLayer"` and
  `"SL{n}"` both resolve.
- `BUG-01` fixed by construction (no frame subtraction); the xfail is removed.
- Immutable geometry + per-event data overlay (no shared-cache mutation).
- No XML imports in the model classes; `DTGEOMETRY` becomes a deprecated shim
  over `CMSXMLSource`.
- `test/` stops mixing suites and demos: the doc examples move to
  `docs/examples/`, the rest is deleted, and one smoke test runs them headless
  (T-025).
- Performance: no per-cell `TransformManager`; **< 20 ms/station**.
- No `VolumeSink` yet; exporters are Phase 5.

**Exit criteria (M2)**

- All 250 chambers within `1e-3` cm through the public API.
- Transform invariant green, including SL2.
- Plotting scripts and the existing constructors still work.
- No XML outside `sources/` (and the shim).
- No backend import in the core; performance budget met.
- `test/` holds only the pytest suite; the docs examples still build.

---

## Phase 3 — Assemblies, custom stations, physical extras (4–6 days) · M3

**Goal:** arbitrary placement without breaking CMS, plus the passive extras.

**Tickets:** T-030, T-031, T-032, T-033.

**Deliverables**

- Runtime `DetectorSpec`/assemblies; configurable world frame; `"CMS"` is the
  default for CMS geometries.
- Custom 1-SL and 5-SL stations build and plot.
- CMS preset remainder: `StationNvPhi`, `StationNvEta`, `SectorRef`,
  `SL13Center`, MB4 13/14 sector-phi correction.
- Plotting selects phi/eta by orientation or an explicit SL, not
  `number == 2`; `faceview` remains compatible.
- Honeycomb as a station attachment (`SolidSpec`, box, aluminium), computed by
  the CMS preset from SL poses.
- Yoke `StructureSpec` data hook only; **no CSG**, no export in this phase. The
  simulator keeps the current `.tg` boolean path.

**Exit criteria (M3)**

- Custom 1-SL/5-SL stations build and plot.
- A two-station assembly builds, transforms and plots.
- CMS plots unchanged.
- Honeycomb data round-trips; the yoke hook is documented as data-only.
- A non-CSG backend is not required yet.

---

## Phase 4 — Event annotations (3–5 days) · M4 · **optional**

**Goal:** generalize segments and add tracks/jets without touching geometry.

**Tickets:** T-040, T-041, T-042.

**Deliverables**

- `Annotation` base (frame reference, attributes, style).
- `Segment` refactor; current `AMDTSegment` behaviour preserved.
- `Track` (polyline + per-point attributes) and `Jet`/`Cone` (apex + axis +
  half-angle).
- Collections (`filter`, `groupby`, `to_dataframe`), plotting adapters, event
  JSON schema (`mpldts.event/1`).
- Annotations never enter `StationSpec` or the geometry exporter.

**Exit criteria (M4)**

- Legacy `Segment`/`Segments`/`AMDTSegment` API works.
- A muon track and a jet render in phi/eta.
- JSON round-trip.
- The geometry path is unaffected; this phase can be deferred.

**Dependency:** Phase 2 (frames). Can run in parallel with 3/5.

---

## Phase 5 — Authoring, JSON, `.tg` sink (4–6 days) · M5

**Goal:** a user can define and export a detector without touching internals.

**Tickets:** T-050, T-051, T-052, T-054. (T-053 CLI is deferred.)

**Deliverables**

- Convenience builders (`make_layer`, `make_superlayer`, `make_station`,
  `make_detector`).
- JSON schema `mpldts.detector/2`; `to_dict`/`from_dict`; JSON only.
- Validation (ids, fit, AABB, rotations, sizes).
- `VolumeSink` + `RecordingSink` + `TgSink`; grouping nodes folded; station,
  cell and honeycomb placements.
- `.tg` parity for one CMS station against the current generator.
- Docs/tutorial/migration note.

**Exit criteria (M5)**

- JSON → validate → build → plot → `.tg` works end to end.
- One CMS station `.tg` matches the current generator (content/geometry).
- No pyg4ometry dependency; no CLI required.
- The yoke is still handled by the simulator's `.tg` path.

---

## Phase 6 — Future: pyg4ometry + GDML (5–8 days) · M6 · **deferred**

**Ticket:** T-060. **Do not start** until Phases 0–5 are merged and ADR-008/014
are revisited.

**Deliverables when started**

- `mpldts/export/pyg4ometry.py` (optional extra `mplDTs[g4]`) implementing
  `VolumeSink`.
- `Box`/`Tubs` mapping, materials, `matrix2tbxyz` rotation.
- Yoke CSG via pyg4ometry.
- GDML writer; `G4GDMLParser` in `DTG4Simulator`.
- Rotation/AABB/overlap/GDML tests.

---

## Estimates

| Phase | Estimate (part-time) |
|---|---|
| 0 | 1–2 days |
| 1 | 4–6 days |
| 2 | 7–10 days |
| 3 | 4–6 days |
| 4 (optional) | 3–5 days |
| 5 | 4–6 days |
| **0–2 (critical path)** | **~2–3 weeks** |
| **0–5 total** | **~4–6 weeks** |
| 6 (deferred) | 5–8 days |

**Critical path:** 0 → 1 → 2. Phase 2 is the riskiest and should not be
rushed. Phases 3/4/5 are independent after Phase 2.

---

## Out of scope (current delivery)

- pyg4ometry/GDML implementation (T-060).
- CSG in mplDTs (the yoke stays in the simulator).
- A CLI and YAML (JSON + Python builders are enough).
- Materials beyond a name on the node.
- Sensitive detectors, digitization, fields (simulator concerns).
- A full event data model (ROOT-like); only segments/tracks/jets.
- Replacing the plotting layer's visual design.
- Rewriting the simulator's yoke/honeycomb logic before the `.tg` parity test.

---

## Gates

| Gate | Requirement |
|---|---|
| Start Phase 1 | M0: invariant + `.tg` smoke + CI |
| Start Phase 2 | M1: spec oracle green for all 250 chambers |
| Start Phase 3/4/5 | M2: all-chamber oracle via the public API + `< 20 ms` |
| Start Phase 6 | M5 + ADR-008/014 update + explicit approval |

No gate may be waived without an ADR and the maintainer's approval.
