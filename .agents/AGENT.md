# AGENT.md — mplDTs geometry generalization

**Status:** active
**Last updated:** 2026-11-05
**Audience:** any agent (human or AI) continuing this work.
**Entry point:** read this file first, then follow the reading order in §3.
**Technical source of truth:** [`../docs/design/generalization-plan.md`](../docs/design/generalization-plan.md) (Rev 4).
**Delivery plan:** [`plan.md`](plan.md) (Rev 4).
**Prototype:** [`../prototype/parametric_poc.py`](../prototype/parametric_poc.py) (runnable, numpy-only).

> **HOLD — planning stage.** The maintainer must review the plan and the
> tickets before any implementation. All tickets are `proposed`; do not create
> branches or edit `mpldts/` until they are `ready`.

---

## 1. Mission

Turn the `mplDTs` geometry layer from a **CMS-XML reader** into a
**declarative, XML-free DT detector model**, without changing what the CMS
geometry produces and without breaking the public API used by
`DTG4Simulator` and the plotting code.

The model must support:

- arbitrary numbers of super layers, layers and cells;
- box **and** tube (cylindrical) cells, with more primitive shapes addable;
- cells and cell grids; the XML `<Wire>` element is a cell centre, not a
  separate object;
- explicit poses and assemblies, so a station can be placed anywhere;
- one unambiguous coordinate convention and a named-frame transformation
  service compatible with the current `transformer` API;
- the physical extras (honeycomb, yoke) as data, even when only a CSG-capable
  backend can build the yoke;
- an **optional** event-object layer for segments, muon tracks and jets/cones,
  reusing the same frames but never entering the detector geometry.

A **pyg4ometry backend is explicitly deferred**. The current job is to leave a
clean seam (`VolumeSink`, backend-neutral shapes, 4×4 poses, stable specs) so
the bridge can be added later as a new module, not a refactor.

**Non-goal:** building a CAD/CSG kernel, or moving Geant4 concepts into the
core.

---

## 2. Current snapshot (details in `state.md`)

- The design document (Rev 4) and a working prototype exist.
- The ticket system (`TICKETS.md`, `tickets/`, `PROGRESS.md`) is ready for
  review; **no library code has changed**.
- **Phase 0 has not started.** There is no pytest suite for geometry.
- pyg4ometry is not installed and must not become a dependency.
- Known correctness issues are documented in `state.md` (SL2 transform error,
  shared-cache mutation, frame-name divergence, attribute-order parsing).

If this snapshot disagrees with the repository, trust the repository and update
`state.md` as part of your change.

---

## 3. Reading order

1. `state.md` — what is true right now.
2. `context.md` — why the project exists, current architecture, findings.
3. `plan.md` — phases and exit criteria.
4. `TICKETS.md` — the board; then `tickets/` for the refined tickets.
5. `PROGRESS.md` — the current checkpoint and session log.
6. `conventions.md` — pose/units/naming/test/style rules.
7. `decisions.md` — decisions already taken; do not reopen them silently.
8. `../docs/design/generalization-plan.md` — the full technical design.
9. `../prototype/parametric_poc.py` — the executable reference for the model.

Do not start coding from the design document alone; the prototype is the
closest thing to a specification of the data model.

---

## 4. Non-negotiables

1. **One pose per node.** Every node stores a single parent-relative transform
   `p_parent = R · p_child + t`. Global poses are derived top-down. Never mix
   coordinates from different frames in one subtraction.
2. **Cell = XML `<Wire>`; there is no separate wire object.**
   - a *cell* is the drift/gas volume (box or tube) and its centre;
   - the XML `<Wire>` element is the cell entry (number + local/global
     position); the source maps it to a cell once;
   - a *cell grid* is how cells repeat (pitch, count, stagger, first id).
3. **Shapes are primitives.** `Box`, `Tube`, then extension shapes. CSG
   (union/subtraction/intersection) is out of scope; a future pyg4ometry
   backend can accept pre-built solids.
4. **No I/O in the model.** XML/JSON/YAML parsing lives in `sources/`; the
   model classes never import `DTGEOMETRY` or `ElementTree`.
5. **Preserve CMS behaviour.** The builder must reproduce the XML
   `GlobalPosition` of every cell within `1e-3` cm. That is the oracle.
6. **Preserve the public API until 3.0.** `Station(wheel=..., sector=...,
   station=...)`, `rawId` constructors, `obj.transformer`,
   `get_transformation`, `transform`, `available_frames`, and the
   `phi`/`eta` plotting API must keep working (aliases are allowed).
7. **No backend imports in the core.** `mpldts.geometry` must not import
   pyg4ometry, Geant4, VTK or `pytransform3d`-specific backend code. The
   exporter seam is `VolumeSink`; a future bridge implements it.
8. **Tests before the refactor.** The oracle and golden snapshots come before
   the rewrite. A refactor without a failing/passing test is not accepted.
9. **Units are centimetres** everywhere in specs and the model. Geant4/pyg4ometry
   conversion happens only at the backend boundary.
10. **Physical volumes are explicit.** Station, cells, honeycomb and yoke are
    solids; super layers and layers are grouping frames. There is no separate
    wire solid. A backend may reject a CSG-only structure (yoke) explicitly.
11. **Event objects are a separate layer.** Segments, tracks and jets reuse
    the frame graph but never enter `StationSpec` or the geometry exporter.
12. **One ticket = one branch = one PR.** Commit as `T-0xx: ...`; never commit
    directly to `main`. See [`workflow.md`](workflow.md).
13. **Update `.agents` as part of the change.** At minimum `state.md`,
    `TICKETS.md` and `PROGRESS.md`; add an ADR to `decisions.md` for any design
    choice.

---

## 5. Current phase and next action

**Current phase:** Phase 0 — safety net. Plan Rev 4 and `TICKETS.md` were
approved on 2026-11-06; implementation is authorized, Phase 1 is not.

**Do this first:** `T-001` (pytest scaffolding), `T-003` (transform invariant
+ oracle harness, including the node snapshot), `T-005` (downstream pin +
`.tg` smoke), `T-006` (benchmark), `T-007` (branch baseline + CI). Do not
start Phase 1 before M0 is green.

**Do not start:** the `mpldts/` rewrite, JSON authoring, event objects, or the
pyg4ometry bridge.

---

## 6. Workflow

1. **Pick one ticket** from `TICKETS.md` that is `ready` (not `proposed`).
   Mark it `doing` in the ticket and the board.
2. **Create a branch** `feature/T-0xx-<slug>` from `main` (see
   [`workflow.md`](workflow.md)).
3. **Write the failing test** (or the smallest reproducible script) before the
   implementation. For geometry changes, use the oracle.
4. **Implement** in the smallest vertical slice; keep the old path working.
5. **Verify**: tests, prototype, benchmark, and the downstream `.tg` smoke test
   when the library changes.
6. **Update** `state.md`, `TICKETS.md`, `PROGRESS.md`, and `decisions.md` if a
   decision was made.
7. **Commit** as `T-0xx: <imperative summary>`; open a PR with the template.
8. If the ticket reveals a design problem, stop, write an ADR proposal in
   `decisions.md`, and ask before expanding scope.

---

## 7. Definition of done

A task is done only when:

- [ ] The relevant tests exist and pass (`pytest`).
- [ ] The CMS oracle still passes (or the new failure is explicitly recorded).
- [ ] Public constructors and `transformer` queries are unchanged in behaviour.
- [ ] No new mandatory dependency; pyg4ometry remains optional/absent.
- [ ] Performance is not worse than the budget in `plan.md`.
- [ ] `state.md`, `TICKETS.md` and `PROGRESS.md` are updated.
- [ ] Any non-obvious choice has an ADR in `decisions.md`.
- [ ] The design document is updated if the model/API changed.

---

## 8. Boundaries and things not to do

- **Do not implement pyg4ometry or GDML now.** The `VolumeSink` seam and the
  pose-folding planner are implemented with `TgSink` in Phase 5, not before.
  The future contract is in [`pyg4ometry-readiness.md`](pyg4ometry-readiness.md).
- **Do not create a wire object.** The XML `<Wire>` is the cell entry; use
  `Cell` (and its centre) for analysis.
- **Do not put segments/tracks/jets into the detector spec.** They are event
  annotations (Phase 4).
- **Do not implement CSG for the yoke.** Provide the data hook; the simulator
  keeps the current `.tg` boolean path until a backend can take it.
- **Do not implement CSG.** If a shape is missing, add a primitive or defer.
- **Do not move CMS rules into the core.** Wheel/sector/face orientation,
  SectorRef, MB4 13/14 and SL13Center belong in `presets/cms.py`.
- **Do not break the plotting API** (`faceview`, `local`, `inverted`,
  `vmap`, patch classes) without an ADR and a deprecation path.
- **Do not add heavy dependencies** to `pyproject.toml`. Optional extras only.
- **Do not edit `DTGeometry_v3.xml`**; it is the reference oracle.
- **Do not commit secrets, local paths, or generated `.tg`/GDML files.**

---

## 9. Key paths

| Path | Purpose |
|---|---|
| `mpldts/geometry/` | runtime model (to be refactored) |
| `mpldts/geometry/_geometry.py` | current XML singleton (`DTGEOMETRY`) |
| `mpldts/patches/` | matplotlib consumers; keep working |
| `test/` | current visual scripts (to be converted to pytest) |
| `docs/design/generalization-plan.md` | technical design (Rev 4) |
| `prototype/parametric_poc.py` | executable reference model |
| `prototype/custom_station.png` | box + tube station preview |
| `.agents/TICKETS.md` | ticket board and status |
| `.agents/tickets/` | refined ticket files (`T-0xx`) |
| `.agents/PROGRESS.md` | checkpoints and session log |
| `.agents/workflow.md` | branch/commit/PR rules |
| `.agents/pyg4ometry-readiness.md` | contract for the deferred backend |
| `../Geant4/DTG4Simulator/geometry/generate_geometry_data.py` | downstream consumer |
| `../Geant4/DTG4Simulator/env/` | Python env used for runs |

Absolute paths and commands are in [`commands.md`](commands.md).

---

## 10. If you are blocked

- Re-read `state.md` and the relevant ADR; most questions are already answered.
- If the blocker is a design choice, write a short ADR proposal and ask the
  maintainer (Daniel Estrada) before changing the model.
- If the blocker is an environment/dependency issue, record it in `state.md`
  and continue with a numpy-only test.
- Do not "work around" the oracle by loosening its tolerance without an ADR.
