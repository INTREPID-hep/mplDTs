# Handoff — start here if you are new

**Last updated:** 2026-11-07 (Europe/Madrid)
**Previous session:** T-031 (CMS preset, face factor from the pose) on
`feature/phase-3-assemblies`.
**Current state:** **Phases 0-2 done on `refactor/v2-integration` (2.3.0, not
merged); Phase 3 in progress on `feature/phase-3-assemblies` (T-030, T-031 done).**
**Current checkpoint:** `CP-007` (M2) complete.
**Next action:** `T-032` — honeycomb as a station attachment, then `T-033` (yoke hook).

---

## 1. The 10-minute orientation

1. Read [`AGENT.md`](AGENT.md) — the contract and the HOLD gate.
2. Read [`state.md`](state.md) — what is true now.
3. Read [`TICKETS.md`](TICKETS.md) — the board; T-020...T-024 are `done`.
4. Read [`PROGRESS.md`](PROGRESS.md) — checkpoints and the session log.
5. Skim [`context.md`](context.md) §2–§5 — architecture, findings, target model.
6. Open [`../docs/design/generalization-plan.md`](../docs/design/generalization-plan.md)
   §3–§5, §8.0, §10, §14–§17.
7. Run the prototype (below); if it passes, the reference model is healthy.

```bash
cd /home/destrada/mplDTs
source /home/destrada/Geant4/DTG4Simulator/env/bin/activate
python prototype/parametric_poc.py
```

Expected: all checks `0.000e+00`; 193 placements; box/tube alignments.

---

## 2. Where Phase 2 stands

Done: Phase 0 (tests, oracle, alias, benchmark, CI), Phase 1 (`specs.py`,
`sources/cms_xml.py`, spec oracle over 250 chambers), T-020 (`Node` +
`build_station`, exported from `mpldts.geometry`), T-021 (`FrameGraph` + `FrameView`,
scoped aliases, legacy `add`/`remove`), T-022 (the legacy classes are views
over the source, the tree and the graph; `BUG-01` gone, plotting bit-identical),
T-023 (`Station.overlay` and a cache that never writes on the shared station;
`BUG-02` gone), T-024 (one build per chamber, lazy `DTGEOMETRY`, explicit
XML attribute names; `BUG-03` gone).

T-025 closed the `test/` triage: the documented examples live in
`docs/examples/` and run headless in `test/geometry/test_examples.py`.
T-026 released 2.3.0 (one version string, new `docs/src/geometry/runtime.rst`)
on `refactor/v2-integration`. T-030 is done on `feature/phase-3-assemblies`:
`build_detector`, `Station.from_spec`, a custom 1-SL/5-SL test and example,
and the phi/eta choice in the patches follows the super layer orientation.
T-031 moved the CMS-only frames (`SectorRef`, `SL13Center`) into
`mpldts/geometry/presets/cms.py` and takes the face factor from the pose.
Remaining in Phase 3: `T-032` honeycomb, `T-033` yoke hook.

Branch policy: `feature/phase-2-runtime` is frozen; the review branch is
`refactor/v2-integration` (2.3.0) and Phase 3 works on
`feature/phase-3-assemblies`. **Nothing merges into `main` until the maintainer
approves it.**

Commands:

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs \
  /home/destrada/Geant4/DTG4Simulator/env/bin/python -m pytest -q
```

Full oracle and the builder sweep: add `-m slow` (250 chambers, seconds).

Phase 3 does not start before the maintainer reviews M2; M2 has been green since 2026-11-06.

---

## 3. What not to touch yet

- `mpldts/` legacy runtime classes — T-022 wired them to the source and
  the graph; T-023 added `Station.overlay`, so per-event data goes there and
  never on a cached station.
- `mpldts/patches/` — plotting must keep working; the phi/eta choice follows
  the super layer orientation since T-030, any further change needs an ADR.
- `DTGeometry_v3.xml` — it is the oracle.
- `DTG4Simulator/geometry/generate_geometry_data.py` — wait for the model and
  the `VolumeSink`/`.tg` parity.
- `pyproject.toml` runtime dependencies — no pyg4ometry, no heavy extras.
- No separate wire object: the XML `<Wire>` is the cell entry.
- No CSG for the yoke in the core.

---

## 4. Decisions already made (do not reopen silently)

- Specs + sources + builder (ADR-001).
- One pose per node, child→parent, cm (ADR-002).
- Cell = XML `<Wire>`; no separate wire object (ADR-019).
- Primitive shapes; Box now, generic protocol (ADR-004, ADR-013).
- Shared `FrameGraph` + scoped `FrameView` (ADR-005).
- CMS as source/preset (ADR-006).
- Immutable geometry + event overlay (ADR-007).
- pyg4ometry deferred; optional extra `mplDTs[g4]` (ADR-008, ADR-014).
- XML globals are the oracle (ADR-009).
- Backward compatibility until 3.0 (ADR-010).
- Physical policy: station, cells, honeycomb, yoke (ADR-011).
- `.tg` first, GDML later (ADR-015).
- Event objects are annotations (ADR-016).
- Honeycomb/yoke are data; CSG in a backend (ADR-017).
- phi/eta follows the super layer orientation; `faceview` is kept (ADR-021).
- Releases are tagged on the integration branch; `main` moves on approval
  (ADR-022, `v2.3.0` at `8997ad7`).

If you need to change one, write a superseding ADR and ask the maintainer.

---

## 5. Resolved defaults (2026-11-06)

- Compatibility horizon: until 3.0.
- Plotting: orientation-based with `faceview` kept.
- Events: Segment/Track/Jet only; optional Phase 4.
- Yoke: stays in the simulator until T-060.
- Phase 0: six tickets (T-004 folded into T-003).
- CLI/YAML: out of scope.

Record answers in `decisions.md` and update `TICKETS.md`/`PROGRESS.md`.

---

## 6. Where to record progress

- Every session: `PROGRESS.md` (log row; checkpoint if a gate is met).
- Ticket state: the ticket file + `TICKETS.md`.
- Design choice: `decisions.md` (ADR).
- Command/tool: `commands.md`.
- Term: `glossary.md`.

---

## 7. Escalation

If blocked for more than a day:

1. Record the exact blocker in `PROGRESS.md` §4 (what, why, what you tried).
2. Mark the ticket `blocked`.
3. If it is a design question, write an ADR proposal and ask; do not guess.
4. If it is an environment issue, keep a numpy-only path so work can continue.
