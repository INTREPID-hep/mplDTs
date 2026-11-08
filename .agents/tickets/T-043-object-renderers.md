# T-043 — Object renderers (`DTObjectsPatch`)

- **Status:** ready
- **Phase:** 4
- **Epic:** E4 Downstream
- **Depends on:** T-022, T-023
- **Branch:** `feature/T-043-object-renderers`
- **PR:** —
- **Owner:** unassigned
- **Labels:** patches, plotting, downstream

## Context

ADR-024 draws the line: mplDTs draws, dtpr owns the objects. Today mplDTs can
draw a chamber (`DTStationPatch`) and `AMDTSegments` (`DTSegmentsPatch`); every
other object is drawn by dtpr with a raw matplotlib call:

- `embed_simhits2axes_loc` calls `ax_phi.scatter(center[0], center[2])` /
  `ax_eta.scatter(...)` once per simhit (`dtpr/utils/dt_plot_functions.py:566-585`).
- `embed_shower2axes_loc` calls `ax.plot(*seg.T)` on the two cell centres from
  `get_shower_segment(..., local=True)`; the `_glob` variant plots
  `global_center` with no station patch at all.
- both repeat the face rule by hand (`if sl == 2` -> eta axes, else phi).

So those artists ignore the projection the patches use. They are drawn in the
station face convention by hand, so `inverted=True` and `local=False` do not
move them; the eta rule (horizontal `= -y`) exists in three more places; and
every new object type costs dtpr another ad-hoc plot call.

`DTRelatedPatch` already owns the projection: subclasses draw in Station-local
coordinates, then the base applies the Station->CMS affine (`local=False`) and
`StationNvPhi`/`StationNvEta` (`inverted=True`). Only the primitives are missing.

## Scope

1. `mpldts/patches/objects_patch.py` — `DTObjectsPatch(DTRelatedPatch)`:

   ```python
   DTObjectsPatch(
       station, axes, objects,
       faceview="phi", local=True, inverted=False, frame="Station", **style,
   )
   # objects: iterable of (points, style); points is (N, 3) in "frame"
   #   N == 1 -> marker  (pass marker=..., linestyle="None")
   #   N >= 2 -> polyline
   ```

   - transform each object `frame` -> `Station` through
     `station.transformer` (any name the graph resolves, `CMS` included), then
     to the face: phi `(x, z)`, eta `(-y, z)` — the rule the cells and
     `DTSegmentsPatch` already follow;
   - one `matplotlib.lines.Line2D` per object, so per-object style (colour,
     marker, size) needs no array mapping and `DTRelatedPatch` moves/inverts
     them with the cells;
   - `DTRelatedPatch._add_collections_to_axes`: add a `Line2D` with
     `axes.add_line`, keep `add_collection` for collections (three lines, no
     behaviour change for the two existing patches).

2. `DTSegmentsPatch`: same class, same paths, same `vmap`; build its paths
   through the new projection and use `AMDTSegment.length` when present instead
   of the fixed `size = 20 if seg.sl != 0 else 40` (`length=None` keeps today's
   value, so dtpr's output does not move).

3. The dtpr side is T-055, which depends on this ticket:
   `embed_simhits2axes_loc` and `embed_shower2axes_loc` swap their
   `scatter`/`plot` calls for `DTObjectsPatch`; the YAML `src` names and
   signatures stay.

## Out of scope

- A `PathCollection`/array-colormap renderer, 3-D views, picking per object.
- Touching `DTStationPatch._create_frame`: its per-type swaps come from
  `bounds`/`local_cords_at_min` being frame-local (rotated for the turned
  super layer), which is a different operation from projecting a point.
- Any event model, `Track`/`Jet`/`Cone`, collections (ADR-024).

## Acceptance criteria

- [ ] A line given in `CMS` and the same line given in `Station` land on
      identical pixels (same display coordinates).
- [ ] A point at `cell.local_center` coincides with that cell's
      `DTStationPatch` outline in data coordinates (< 1e-9).
- [ ] `inverted=True` mirrors the objects together with the cells; `local=False`
      puts them in the CMS frame together with the chamber.
- [ ] `DTSegmentsPatch` paths are identical to 2.5.0 for a CMS chamber with no
      `length` set.
- [ ] `pytest -q` green; the new test file runs in < 1 s, no ROOT, no Qt.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs MPLBACKEND=Agg \
  /home/destrada/Geant4/DTG4Simulator/env/bin/python -m pytest -q test/patches
```

## Risks / notes

- One `Line2D` per object is O(N) artists: fine for one chamber per event;
  revisit only if a plot carries thousands of hits.
- The face rule here is for *points given in a frame*. `DTStationPatch` maps
  *extents in a rotated frame*, so do not merge the two.
- `DTSegmentsPatch` keeps its eta rule for now (it filters `sl == 2`); removing
  the filter is dtpr's call, not this ticket's.

## Progress

- 2026-11-08: opened from the dtpr review; Phase 4 rescope (ADR-024/025).
