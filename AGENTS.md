# mplDTs - map for an agent or a new maintainer

Geometry toolkit for Drift Tube detectors: the CMS DT chambers from
`DTGeometry_v3.xml`, and any DT-like detector written by hand. Read this page,
then the one file named in the row you need. The prose lives in `docs/`, the
truth lives in `mpldts/`.

## The model in one picture

```
  specs.py             model.py              frames.py             views + export
  frozen data    -->   build_station()  -->  FrameGraph       -->  Station.from_spec()
  StationSpec          Node tree             FrameView            DTStationPatch
  DetectorSpec         one parent-relative   slash frame_id       TgSink -> .tg
  validate()           pose per node         transform()          iter_volume_placements()
```

`Node.kind` is one of `station`, `superlayer`, `layer`, `cell`, `attachment`.
A grouping node has no shape and no material: its bounds are the union of its
children. Only a cell carries the gas and a solid.

## Five rules

1. **Specs are data.** Frozen dataclasses, parent-relative poses, no derived
   value stored. If you need a world position, compose it (`Pose.compose`) or
   build the tree - never cache it in the spec.
2. **One pose per node, composed downwards.** `node.world_pose` is
   `parent.world_pose.compose(node.pose)`; nothing else writes a transform.
3. **An event never mutates geometry.** Per-event values are a table keyed by
   `(sl, l, w)` handed to the patch (`data=`, `vmap=`). Copying a station per
   event is the bug this rule forbids.
4. **Volume names belong to the sink.** `TgSink.name_of(node)` decides the name;
   the geometry never stores one. The C++ `StationSD` parses the CMS wheel out
   of `MB0_W-2_SE1_ST1`, so the minus sign is part of the contract.
5. **No module-level caches and no import-time parsing.** `mpldts.geometry`
   imports without reading a byte of XML; `CMSXMLSource()` is what parses.

## Recipes

### Add a field to a spec
1. `mpldts/geometry/specs.py` - the dataclass field and the check in `validate()`.
2. `mpldts/geometry/serialize.py` - `_<kind>_to_dict` and `_<kind>_from` (a field
   that may be absent from the document is declared optional there).
3. `mpldts/geometry/model.py` - only if the builder or the frame graph reads it.
4. `test/test_specs.py` - round trip through `to_json` / `from_json`.

### Add a detector that is not CMS
1. `mpldts/geometry/constructors.py` - `make_layer`, `make_superlayer`,
   `make_station`, `make_detector`, or the dataclasses directly.
2. `DetectorSpec(name, pose, stations=[...], structure=[...])`, then `validate()`.
3. Keep it as `to_json(detector)` in your repository; `from_json` validates on load.
4. Worked example: `docs/howto/custom_detector.rst`, `docs/examples/custom_station.py`.

### Add an exporter (GDML, STEP, ...)
1. Implement the `VolumeSink` protocol of `mpldts/export/base.py`
   (`solid()`, `place()`, `end()`); the tree arrives through
   `iter_volume_placements(root)`.
2. Copy the shape of `mpldts/export/tg.py`; export it from `mpldts/export/__init__.py`.
3. `test/test_export.py` - one test per sink, on a small hand-built detector.
4. A GDML/pyg4ometry sink is an idea only: `docs/about/roadmap.rst`.

### Colour the cells by a new quantity
1. The patch already accepts any column: `DTStationPatch(..., vmap="width", data=rows)`.
2. New drawing behaviour goes in `mpldts/patches/dt_station_patch.py`
   (`_draw_cells`, `_is_turned`), never in the geometry.
3. `test/test_views.py` and `docs/concepts/events.rst`.

### Change a volume name
1. `mpldts/export/tg.py`: `_clean()` and `TgSink.name_of()`.
2. Check the reader in the Geant4 simulation (`DTG4Simulator`, `StationSD.cxx`):
   it splits `_W` and `_SE` out of the name. A rename needs a golden identity
   table first; it is an open item in `docs/about/roadmap.rst`.

## API cheat sheet

```python
from mpldts.geometry import Station, DriftCell, SuperLayer, Layer, DTFrame
from mpldts.geometry import build_station, build_detector          # spec -> Node
from mpldts.geometry.sources import CMSXMLSource                    # .chamber_keys()
from mpldts.geometry.specs import (Pose, Box, Tube, CellGrid, LayerSpec,
    SuperLayerSpec, StationSpec, DetectorSpec, AttachmentSpec, StructureSpec, validate)
from mpldts.geometry.constructors import make_layer, make_superlayer, make_station, make_detector
from mpldts.geometry.serialize import to_dict, from_dict, to_json, from_json
from mpldts.geometry.frames import FrameGraph, FrameView
from mpldts.patches import DTStationPatch, DTObjectsPatch, DTSegmentsPatch
from mpldts.export import TgSink, export_volumes, iter_volume_placements
```

Key calls: `CMSXMLSource().station(wheel, sector, station)`,
`Station.from_spec(spec, wheel=None, sector=None, number=None)`,
`build_station(spec, parent=None)`, `station.transformer.transform(point, from_frame, to_frame)`,
`DTStationPatch(station, axes, faceview="phi"|"eta", local=True, inverted=False, vmap="time", data=rows)`,
`TgSink(target, world="world", name_of=None)`.

## Commands

```bash
# tests (the 250-chamber oracle is marked slow and skipped by default)
PYTHONPATH=$PWD MPLBACKEND=Agg python -m pytest -q          # -m slow for the oracle
# docs
pip install -e ".[docs]" && cd docs && sphinx-build -b html . _build/html
# cli
mpldts info detector.json ; mpldts convert detector.json out.tg ; mpldts plot detector.json
```

## Do not

- rename volumes, cells or super layers because a plot looked wrong;
- add a station cache, a `DTGEOMETRY` singleton, or an import-time parse;
- import `mpldts.geometry.sources.cms_xml` from `specs.py` or `model.py`;
- write per-event values into a spec, a node or a view;
- add ticket ids (`T-045`, `CP-012`) to code, commits or docs.

Where the detail is: `docs/concepts/model.rst` (the four layers),
`docs/concepts/frames.rst` (transforms), `docs/concepts/naming.rst` (volume
names), `docs/concepts/events.rst` (per-event data), `docs/reference/` (autodoc),
`docs/about/decisions.rst` (why it is like this).
