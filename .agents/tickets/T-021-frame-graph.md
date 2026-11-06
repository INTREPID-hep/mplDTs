# T-021 — `FrameGraph` + `FrameView`

- **Status:** done
- **Phase:** 2
- **Epic:** E2 Runtime model
- **Depends on:** T-020
- **Branch:** `feature/phase-2-runtime`
- **PR:** —
- **Owner:** unassigned
- **Labels:** model, compatibility

## Context

The legacy objects each carry a `TransformManager` copied from their parent,
which is how the SL2 frame mixing survived. The replacement is one shared
graph with one edge per parent/child pose, plus a per-object view that
resolves the legacy names in scope.

## Scope

- `mpldts/geometry/frames.py`:
  - `FrameGraph`: `add_edge`, `remove_edge`, `add_virtual`, `add_nodes`,
    `matrix`, `get_transformation`, `transform`, `frames`, cache keyed by
    `(from, to)` and cleared on any edge change.
  - `FrameView(graph, node)`: scoped aliases `Station`, `SuperLayer`,
    `SL{n}`, `Layer`, `Cell`, `CMS`/`World`; `add`/`remove` keep the legacy
    signature and create a frame scoped under the resolved partner.
- Export both from `mpldts.geometry`.
- `test/geometry/test_frames.py`: conventions against the node tree and the
  legacy `TransformManager`, round-trip, point/vector, aliases, ambiguity,
  scoped `add`/`remove`, virtual frames, cache invalidation.

## Conventions kept

- `graph.matrix(from, to)` returns a `Pose` with `p_to = M.apply(p_from)`,
  the same convention as `TransformManager.get_transformation(from, to)`.
- `get_transformation` warns and returns `None` when there is no path
  (legacy contract); `transform` raises `ValueError`.
- `type="point"` gets the translation, `type="vector"` does not.

## Out of scope

- Wiring the legacy constructors to the graph (T-022).
- The CMS preset virtual frames `StationNvPhi`, `StationNvEta`, `SectorRef`,
  `SL13Center` (Phase 3); T-021 only provides `add_virtual`.

## Acceptance criteria

- [x] `graph.matrix(cell, root)` equals `cell.world_pose` for every node.
- [x] Cell centres through the view match the XML `GlobalPosition`.
- [x] `matrix(a, b)` composed with `matrix(b, a)` is the identity.
- [x] `SuperLayer` and `SL{n}` both resolve from a super-layer view.
- [x] Ambiguous or unknown names raise `KeyError` listing the aliases.
- [x] No pytransform3d, XML or backend import in `frames.py`.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_frames.py
```

## Progress

- 2026-11-06: done. 257 lines: `FrameGraph` (BFS with a per-pair cache),
  `FrameView` (scoped aliases, `add`/`remove` with the legacy signature)
  and `add_virtual`. 15 tests; the graph matches the node tree, the XML
  cell centres and the legacy station chain.
