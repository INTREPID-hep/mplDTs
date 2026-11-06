# Prototype: parametric DT geometry

`parametric_poc.py` is a standalone (numpy-only) proof of concept for the
design in [`../docs/design/generalization-plan.md`](../docs/design/generalization-plan.md).

It demonstrates:

- a node tree (`Station -> SuperLayer -> Layer -> Cell`) where a node may or
  may not own a solid (grouping frames);
- `Box` and `Tube` cell solids — the "cell is a cylinder, not a box" case;
- `CellGrid` with pitch, count, half-cell stagger and first id;
- one `Pose` per node, composed top-down;
- a shared `FrameGraph` with scoped aliases (`"Cell"`, `"Layer"`, `"Station"`,
  `"CMS"`) and virtual frames, preserving the old `transformer` API;
- JSON round-trip and an exporter placement walk that folds grouping nodes;
- a backend seam (`VolumeSink` / `RecordingSink`) that a future pyg4ometry,
  GDML or `.tg` backend can implement without touching the core.

pyg4ometry is **not** a dependency and is not implemented here; the seam is
what makes it additive later.

**Note on the wire:** the XML `<Wire>` element is the cell entry (number +
position); there is no separate wire object (ADR-019). The prototype uses
`Cell` only.

Run:

```bash
python prototype/parametric_poc.py
python prototype/parametric_poc.py --plot prototype/custom_station.png
```

