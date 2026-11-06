# T-032 — Honeycomb as a station attachment

- **Status:** proposed
- **Phase:** 3
- **Epic:** E3 Assemblies and extras
- **Depends on:** T-030
- **Branch:** `feature/phase-3-assemblies`
- **PR:** —
- **Owner:** unassigned
- **Labels:** model, physical-extras

## Context

Honeycomb panels are not in the model at all. The patches draw station and
super-layer bounds and cells; the simulator keeps its own panel geometry.
ADR-011 makes honeycomb a physical volume and ADR-017 says it is data: no CSG
in the core.

## Scope

- An optional attachment list on `StationSpec` (box panels with a pose and a
  material, aluminium); no new shape type unless the panels need one.
- `build_station` emits one node per attachment at its pose.
- The CMS preset computes the panels from the super-layer poses, so the CMS
  XML keeps carrying no honeycomb information.
- Plotting ignores attachments unless asked for them.

## Out of scope

- CSG, GDML, exporting honeycomb to `.tg` (T-052).
- Changing the simulator's own honeycomb.

## Acceptance criteria

- [ ] A CMS station carries its panels with the expected count, poses and
      volumes; the data matches the reference chamber used in the simulator.
- [ ] A custom station without attachments builds exactly as before.
- [ ] No exporter or plotting change is required for the suite to stay green.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
```

## Risks / notes

- Panel alignment is easy to get subtly wrong; pin one chamber's panel poses
  against the simulator values in the ticket, not against a drawing.
