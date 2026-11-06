# T-020 — Runtime topology + `build_station`

- **Status:** done
- **Phase:** 2
- **Epic:** E2 Runtime model
- **Depends on:** T-010, T-011
- **Branch:** `feature/phase-2-runtime`
- **PR:** —
- **Owner:** unassigned
- **Labels:** model, correctness

## Context

Phase 1 produced the specs; nothing builds runtime nodes from them yet. This
ticket adds the runtime tree the rest of Phase 2 hangs off:

```
station
└── super layer      (grouping frame, shape=None)
    └── layer        (grouping frame, shape=None)
        └── cell     (Box or Tube)
```

Every node stores its parent-relative `pose`; `world_pose` is composed once,
top-down, at build time. Cells are expanded from the layer's `CellGrid`.

## Scope

- `mpldts/geometry/model.py`: `Node` (name, kind, pose, world_pose, frame_id,
  shape, material, parent, children) and `build_station(spec, parent=None)`.
- `build_station` validates the spec first (`specs.validate`).
- `frame_id` is the slash path from the root, e.g.
  `/W0_S5_MB1/SL2/L1/C7`; names are `SL{n}`, `L{n}`, `C{id}`.
- Export `Node` and `build_station` from `mpldts.geometry`.
- `test/geometry/test_nodes.py`: structure, frame ids, pose composition,
  parent handling, and the cell-centre oracle through the builder.

## Out of scope

- `FrameGraph`/`FrameView` and aliases (T-021).
- Legacy constructors delegating (T-022).
- Detector assemblies (`build_detector` is T-030).
- Immutability/overlay (T-023) and performance work (T-024).

## Acceptance criteria

- [x] One node per station, super layer, layer and cell; grouping nodes have
      `shape=None`.
- [x] `world_pose` equals the composition of the poses down the tree;
      an optional parent node shifts the whole station.
- [x] Cell centres from `world_pose` reproduce the XML `GlobalPosition` for
      every chamber within the `2e-3` cm tolerance.
- [x] `frame_id` is unique and prefixed by its parent's id.
- [x] No XML, matplotlib or backend import in `model.py`.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_nodes.py
```

## Progress

- 2026-11-06: done. ~50 lines in model.py. 18 tests, plus a `slow`
  all-250-chamber sweep through the builder (4.9 s). Builder cost measured
  at 7.46 ms/station for 250 stations (already under the 20 ms budget).
