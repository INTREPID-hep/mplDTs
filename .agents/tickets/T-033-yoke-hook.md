# T-033 — Yoke `StructureSpec` data hook

- **Status:** proposed
- **Phase:** 3
- **Epic:** E3 Assemblies and extras
- **Depends on:** T-030
- **Branch:** `feature/phase-3-assemblies`
- **PR:** —
- **Owner:** unassigned
- **Labels:** model, physical-extras

## Context

The yoke is detector structure, not a chamber: it stays in the simulator until
the pyg4ometry phase (ADR-011, O-04). Phase 3 needs a data placeholder so a
detector description can state it without dragging CSG into the core.

## Scope

- `StructureSpec` in `specs.py`: name, pose, material and an optional shape,
  validated like the rest.
- An optional `structure` list on `DetectorSpec`.
- No nodes, no exporter, no backend import.

## Out of scope

- CSG operations, boolean solids, GDML or `.tg` output.
- Moving the simulator's yoke.

## Acceptance criteria

- [ ] A `DetectorSpec` with structure entries validates and a detector with
      stations still builds unchanged.
- [ ] No node is created for structure data and no exporter sees it.
- [ ] `mpldts` imports without any backend dependency.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
```

## Risks / notes

- The hook must stay data-only: a shape here is a description, not a solid.
