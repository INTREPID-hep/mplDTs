# T-033 — Yoke `StructureSpec` data hook

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

The yoke is detector structure, not a chamber: it stays in the simulator until
the pyg4ometry phase (ADR-011, O-04). Phase 3 needed a data placeholder so a
detector description can state it without dragging CSG into the core.

## What was delivered

- `specs.StructureSpec` (name, pose, optional shape, material `G4_Fe`)
  and an optional `structure` list on `DetectorSpec`.
- Validation: one entry type, non-empty unique names, a Pose and an optional
  positive shape.
- No node, no exporter, no backend import: `build_detector` ignores the list.
- `test/geometry/test_structure.py` (4 tests): a structure entry validates and
  builds no node, an entry may have no shape, duplicates and bad poses raise, a
  detector without structure is unchanged.

## Out of scope

- CSG operations, boolean solids, GDML or `.tg` output.
- Moving the simulator's yoke.

## Acceptance criteria

- [x] A `DetectorSpec` with structure entries validates and a detector with
      stations still builds unchanged.
- [x] No node is created for structure data and no exporter sees it.
- [x] `mpldts` imports without any backend dependency.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
```

## Risks / notes

- The hook is data only: a shape here is a description, not a solid. The yoke
  export is T-052/T-060 territory.
