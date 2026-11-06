# Handoff — start here if you are new

**Last updated:** 2026-11-06 (Europe/Madrid)
**Previous session:** Phase 0 implementation (tests, alias, benchmark, CI).
**Current state:** **M0 done on `feature/phase-0-safety-net` (not merged).**
**Current checkpoint:** `CP-005` (M0) in progress.
**Next action:** T-011 (`CMSXMLSource`) on `feature/phase-1-specs`.

---

## 1. The 10-minute orientation

1. Read [`AGENT.md`](AGENT.md) — the contract and the HOLD gate.
2. Read [`state.md`](state.md) — what is true now.
3. Read [`TICKETS.md`](TICKETS.md) — the board; all tickets are `proposed`.
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

## 2. Where Phase 0 stands

Done (2026-11-06): T-001 pytest scaffolding, T-003 oracle harness + node
snapshot (T-002 folded in), T-005 `SuperLayer` alias + `.tg` smoke,
T-006 benchmark, T-007 CI workflow file.

Open: **T-007** — first remote CI run and the integration-base decision
(`enhancement-cacheObjects` vs `main`); see `PROGRESS.md` §4.

Commands:

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs \
  /home/destrada/Geant4/DTG4Simulator/env/bin/python -m pytest -q
```

Full oracle: add `-m slow` (250 chambers, minutes).

Do not start Phase 1 before M0 is green. Do not start Phase 2 before M1.

---

## 3. What not to touch yet

- `mpldts/` runtime classes — the refactor starts in Phase 2.
- `mpldts/patches/` — plotting must keep working; changes need an ADR.
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
