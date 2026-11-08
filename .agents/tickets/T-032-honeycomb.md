# T-032 — Honeycomb as a station attachment

- **Status:** done
- **Phase:** 3
- **Epic:** E3 Assemblies and extras
- **Depends on:** T-030 (done)
- **Branch:** `feature/phase-3-assemblies`
- **PR:** — (branch pushed; the maintainer merges)
- **Owner:** —
- **Labels:** model, physical-extras
- **Completed:** 2026-11-08

## Context

Honeycomb panels were not in the model at all. The patches draw station and
super-layer bounds and cells; the simulator keeps its own panel geometry
(`geometry/generate_geometry_data.py`, `create_honeycomb`).
ADR-011 makes honeycomb a physical volume and ADR-017 says it is data: no CSG in
the core.

## What was delivered

- `specs.AttachmentSpec` (name, pose, shape, material) and an optional
  `attachments` list on `StationSpec`, validated like the rest (name,
  pose, shape, no duplicates).
- `model.build_station` emits one `attachment` node per attachment in
  `Node.attachments`, beside the geometry children, so nothing that walks the
  geometry sees it; `FrameGraph.add_nodes` registers the frames, so
  `Honeycomb` resolves in the station scope.
- `presets.cms.with_attachments(spec, record)` derives the panel the way the
  simulator does: a box filling the gap between super layer 1 and super layer 2
  (super layer 3 for an MB4), 1 cm clear of the chamber bounds,
  `G4_Al`. The XML still carries no honeycomb.
- `test/geometry/test_attachments.py` (7 tests) pins the reference chamber
  (W-2/S1/MB2: 265.8 x 250.1 x 11.8 cm at z 2.675), the MB4 fallback to SL3, the
  frame, the custom-station path and the validation.

## Out of scope

- CSG, GDML, exporting honeycomb to `.tg` (T-052).
- Changing the simulator's own honeycomb.
- Plotting: the panels are not drawn unless an exporter asks for them.

## Acceptance criteria

- [x] A CMS station carries its panels with the expected count, pose and volume;
      the numbers match the simulator's formula on the reference chamber.
- [x] A custom station without attachments builds exactly as before.
- [x] No exporter or plotting change is required for the suite to stay green.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
```

## Risks / notes

- The panel pose comes from the XML super-layer records, so the CMS source keeps
  carrying no honeycomb and a custom station states its own panels explicitly.
- `Node.attachments` is a separate list on purpose: injecting panels into
  `children` would break every walker that expects super layers there.
