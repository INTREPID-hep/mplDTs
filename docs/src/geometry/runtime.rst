Runtime model
=============

Version 2.3 rebuilt the geometry core around four small layers. The classes
documented in :doc:`station`, :doc:`super_layer`, :doc:`layer` and
:doc:`drift_cell` are still there and keep their API; internally they are thin
views over the pipeline below.

.. code-block:: text

    DTGeometry_v3.xml
          |  CMSXMLSource              one indexed parse per process
          v
    StationSpec / DetectorSpec         frozen dataclasses: Pose, Shape, CellGrid
          |  build_station             one node tree per chamber (cached)
          v
    Node tree                          parent-relative Pose, cached world_pose
          |  FrameGraph / FrameView    scoped aliases: Station, SL2, L1, Cell, CMS
          v
    legacy views                       Station, SuperLayer, Layer, DriftCell

Nothing below the XML layer imports ``xml.etree``: the specs are plain
dataclasses, the builder is numpy only, and the graph composes 4x4 matrices.
A *cell* is the XML ``<Wire>`` entry; there is no separate wire object.

Poses and units
---------------

Every node stores **one** pose relative to its parent
(``p_parent = R . p_child + t``), in cm, and the builder composes and caches
its world pose once, top-down. Rotations are intrinsic and orthonormal; the
spec validator rejects non-finite values, non-orthonormal rotations and shapes
that are not positive.

.. autoclass:: mpldts.geometry.specs.Pose
    :members: compose, inverse, apply, matrix

Specs
-----

The specs are frozen dataclasses. They are the only geometry the model layer
knows about: no XML, no raw ids, no plotting.

.. autoclass:: mpldts.geometry.specs.Box
    :members: volume

.. autoclass:: mpldts.geometry.specs.Tube
    :members: volume

.. autoclass:: mpldts.geometry.specs.CellGrid
    :members: x_positions, ids

.. autoclass:: mpldts.geometry.specs.StationSpec

.. autoclass:: mpldts.geometry.specs.AttachmentSpec

A station may carry attachments: passive panels bolted to it, such as the
aluminium honeycomb spacer. The builder emits one node per attachment beside the
geometry children, so an exporter can turn it into a volume while plotting and
the frame queries ignore it. The CMS preset derives the honeycomb panel from the
super layer records, because the XML carries none.

.. autoclass:: mpldts.geometry.specs.DetectorSpec

.. autoclass:: mpldts.geometry.specs.StructureSpec

Detector structure (the yoke) is a spec-level list and stays data: the builder
creates no node for it and no exporter sees it until a backend can do the boolean
solids.

Building the node tree
----------------------

.. autofunction:: mpldts.geometry.model.build_station

.. autoclass:: mpldts.geometry.model.Node

Assemblies and custom stations
------------------------------

A detector is the root of the same node tree:
:func:`build_detector <mpldts.geometry.model.build_detector>` hangs every
station of a :class:`~mpldts.geometry.specs.DetectorSpec` under it at its
own pose, so one graph holds the whole assembly. A chamber that is not in the CMS
XML gets the legacy views with
:meth:`Station.from_spec <mpldts.geometry.station.Station.from_spec>`: the
values those classes read (local centres, bounds, direction, raw ids) are
derived from the node tree, so the same plotting patches draw it. A super layer
is chosen for the phi or the eta view by its orientation, not by its number.

.. autofunction:: mpldts.geometry.model.build_detector

.. automethod:: mpldts.geometry.station.Station.from_spec
    :no-index:

A station view registers `StationNvPhi`, `StationNvEta` and `SL13Center`
from its own node tree: the first two are the views the patches invert through,
the third is the centre of the outermost super layers that `AMDTSegments`
measures from by default. The face factor that orients them comes from the
station pose, so a custom chamber inverts its views like a CMS one.
`SectorRef` was a CMS-sector frame and is gone (3.0).

.. literalinclude:: ../../examples/custom_station.py
    :language: python
    :lines: 1-66

Authoring: short constructors and JSON
------------------------------------------------------------

Four constructors fill the defaults that a hand-written spec should not repeat
(identity pose, no envelope, air in the chamber, vacuum in the world). They do
not validate eagerly: :func:`validate <mpldts.geometry.specs.validate>` stays the
single gate, so a spec built with them fails where a hand-built one fails.

.. autofunction:: mpldts.geometry.constructors.make_layer

.. autofunction:: mpldts.geometry.constructors.make_superlayer

.. autofunction:: mpldts.geometry.constructors.make_station

.. autofunction:: mpldts.geometry.constructors.make_detector

A spec saves to a JSON document and loads back into the same spec
(`mpldts.station/2` for a chamber, `mpldts.detector/2` for an assembly). The
document holds poses, shapes and names and nothing derived: cell centres and
world poses are rebuilt from it, so a file cannot disagree with the model. It is
strict on the way in, because a typo in a detector description is a detector
that is silently wrong.

.. autofunction:: mpldts.geometry.serialize.to_dict

.. autofunction:: mpldts.geometry.serialize.from_dict

.. autofunction:: mpldts.geometry.serialize.to_json

.. autofunction:: mpldts.geometry.serialize.from_json

.. code-block:: json

    {
      "schema": "mpldts.station/2",
      "name": "TB-1",
      "pose": {"rotation": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "translation": [0, 0, 0]},
      "shape": {"kind": "box", "dx": 160.0, "dy": 100.0, "dz": 37.3},
      "material": "G4_AIR",
      "super_layers": [{
        "number": 1,
        "pose": {"rotation": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "translation": [0, 0, -9.5]},
        "layers": [{
          "number": 1,
          "pose": {"rotation": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "translation": [0, 0, -3.0]},
          "cells": {
            "pitch": 20.0, "count": 8, "first_id": 1, "offset": 0.0,
            "shape": {"kind": "box", "dx": 20.0, "dy": 100.0, "dz": 1.3},
            "material": "GasMixture"
          }
        }]
      }]
    }

The rotation is a 3x3 matrix in rows and the translation is a triple, both in the
parent frame; a box carries its full dimensions and a tube its radius, length and
axis. Unknown keys are errors, and so are a missing field, a wrong type, an
unknown shape kind, a rotation that is not orthonormal and a grid that does not
fit its layer.

Exporting to Geant4 (.tg)
-------------------------

An exporter never walks the tree itself: it implements a sink and receives the
placements. Only nodes with a solid become volumes; the grouping frames (super
layer, layer) are folded into the pose of the placement, and a station's
attachments (the honeycomb) are visited after the cells.

.. autoclass:: mpldts.export.base.VolumePlacement

.. autoclass:: mpldts.export.base.VolumeSink

.. autofunction:: mpldts.export.base.iter_volume_placements

.. autofunction:: mpldts.export.base.export_volumes

.. autoclass:: mpldts.export.base.RecordingSink

:class:`mpldts.export.tg.TgSink` writes that walk as a Geant4 ASCII geometry file,
the `.tg` format `DTG4Simulator` reads with `G4tgbVolumeMgr`. It writes the
solids, the volumes and the placements only: the world volume and the identity
rotation `R0` belong to the document that includes the file. Volume and
rotation names are qualified by the exported root, so several station files can
be included in one document without redefining anything.

The names are part of the contract with the reader: a consumer whose Geant4 code
parses the volume names passes ``name_of`` to :class:`~mpldts.export.tg.TgSink`
and keeps its own scheme. ``DTG4Simulator`` does exactly that, because its
sensitive detectors decode the chamber from ``Station_W<w>_Sec<s>_St<n>``, the
super layer and the cells per layer from
``DriftCell_W<w>_Sec<s>_St<n>_SL<n>_<encoding>``, and the layer and wire from
the copy number of the cell volume (T-005, T-057).

.. autoclass:: mpldts.export.tg.TgSink

.. autoexception:: mpldts.export.tg.TgFormatError

The example below is the whole path: build the spec with the short
constructors, write the JSON document, read it back, build the node tree from
the document, plot the chamber with the legacy patches and export the volumes.

.. literalinclude:: ../../examples/export_tg.py
    :language: python

The command line
----------------

The three conversions that are not worth a script of their own (T-053):

.. code-block:: bash

    mpldts info    station.json          # counts, bounds, materials, cells
    mpldts convert station.json out.tg   # the .tg through TgSink
    mpldts plot    station.json out.svg  # one phi and one eta figure

``--station N`` picks one station out of a detector document; without it
``convert`` writes the whole detector and ``plot`` needs a single station. A bad path
or a bad document is one line on stderr and exit code 2, never a traceback.

The CMS source
--------------

``CMSXMLSource`` is the only reader of ``DTGeometry_v3.xml``. It parses the
file once and answers with specs: one ``StationSpec`` per chamber, its honeycomb
panel included.

.. autoclass:: mpldts.geometry.sources.cms_xml.CMSXMLSource
    :members: chamber_keys, number_of_chambers, station, record, detector, cell_centres

.. code-block:: python

    from mpldts.geometry import build_station
    from mpldts.geometry.sources import CMSXMLSource

    source = CMSXMLSource()                  # the XML is parsed once
    station = build_station(source.station(-2, 1, 2))
    cell = station.children[0].children[0].children[0]
    print(cell.frame_id, cell.world_pose.translation)

Frames
------

``FrameGraph`` holds one edge per parent/child pose; ``FrameView`` exposes the
scoped aliases (``Station``, ``SL2``, ``L1``, ``Cell``, ``CMS``, plus the
plotting virtual frames ``StationNvPhi``, ``StationNvEta`` and ``SL13Center``)
and transforms points between them. The ``SuperLayer`` alias was a 2.x
convenience and no longer exists: name the super layer, or use ``Layer``.

.. autoclass:: mpldts.geometry.frames.FrameGraph
    :members: add_nodes, add_edge, add_virtual, transform, matrix, frames

.. autoclass:: mpldts.geometry.frames.FrameView
    :members: transform, get_transformation, add, remove

Per-event data
--------------

A station is geometry and nothing else. The values a patch colours are the
``(sl, l, w)`` cell-data table of ADR-024, handed to
:class:`~mpldts.patches.dt_station_patch.DTStationPatch` as ``data``: a
``DataFrame``, a ``list[dict]`` or one ``dict``, with ``sl``, ``l`` and ``w``
in every row plus any number of value columns. A row with no matching cell is
ignored, a cell with no row is drawn at 0, and the geometry is never written.

.. code-block:: python

    from mpldts.geometry import Station
    from mpldts.geometry.sources import CMSXMLSource
    from mpldts.patches import DTStationPatch

    chamber = (-2, 1, 2)
    source = CMSXMLSource()                       # the XML is parsed once
    station = Station.from_spec(source.station(*chamber), *chamber)

    rows = [{"sl": 1, "l": 1, "w": 1, "time": 12.5}]
    DTStationPatch(station, ax, local=True, vmap="time", data=rows)

The same station draws event after event and two patches built from it never see
each other's data, so nothing is copied per event and nothing has to be cached.
The identifiers are cast to ``int``: a column read from a ROOT branch arrives
as a float and still finds its cell.

Cost on a warm process: importing ``mpldts.geometry`` reads no XML, parsing it
is a few seconds once, and a station view is tens of milliseconds.

The downstream contract
-----------------------

``DTPatternRecognition`` (dtpr) plots one event on top of these classes, so
the names it imports are a contract: renaming any of them is a breaking change
until 3.0 (ADR-025). ``test/downstream`` imports exactly this surface, with no
ROOT and no Qt:

- geometry: ``Station`` and ``AMDTSegments``;
- patches: ``DTStationPatch``, ``MultiDTSegmentsPatch``, ``DTRelatedPatch``;
- on the station: ``name``/``wheel``/``sector``/``number``,
  ``super_layer(sl).layer(l).cell(w)``, ``Cell.local_center`` and
  ``global_center``, ``Layer._first_cell_id``/``_last_cell_id`` and
  ``layer.cell(id)``;
- on a patch: ``.station``, ``._collections`` and ``.cells_collection`` (the
  visualizer iterates the collections to toggle its artists).

dtpr builds the chamber itself, caches the views, and hands the event to the
patch:

.. code-block:: python

    from functools import lru_cache

    from mpldts.geometry import Station
    from mpldts.geometry.sources import CMSXMLSource

    @lru_cache(maxsize=1)
    def source():
        return CMSXMLSource()

    @lru_cache(maxsize=None)
    def chamber(wheel, sector, station):
        spec = source().station(wheel, sector, station)
        return Station.from_spec(spec, wheel, sector, station)

    rows = [{"sl": 1, "l": 1, "w": 2, "time": 400.0}, ...]
    DTStationPatch(chamber(0, 1, 1), ax, local=True, vmap="time", data=rows)

``Station.from_spec`` takes the chamber numbers because the plotter labels its
window with them; a station that is not a CMS chamber passes none and they read
``None``.

What 3.0 removed
----------------

2.9 carried the pre-refactor API and warned on every call that would go. 3.0
deletes it; ``.agents/migration-3.0.md`` (ADR-026) is the plan, this table is
the result.

.. list-table::
   :header-rows: 1
   :widths: 42 58

   * - Gone in 3.0
     - What to use instead
   * - ``Station(wheel, sector, station)``
     - ``CMSXMLSource().station(wheel, sector, station)`` and
       ``Station.from_spec(spec, wheel, sector, number)``
   * - ``Station.set_cell_attrs(dt_info)``, ``Station.overlay(dt_info)``,
       ``StationsCache.get(..., dt_info=...)``, ``STATION_CACHE``
     - the ``(sl, l, w)`` cell-data table passed to the patch (ADR-024); the
       event model stays in ``DTPatternRecognition``
   * - ``DTGeometry(xml_file)``, ``DTGEOMETRY``
     - ``CMSXMLSource()``: one parse per process, specs instead of XML elements
   * - ``SuperLayer(rawId=...)``, ``Layer(rawId=...)``,
       ``DriftCell(number=...)`` standalone
     - the node tree of ``build_station(spec)``: ``node.children`` is the same
       hierarchy and every pose is on the node
   * - the frame alias ``SuperLayer``
     - ``SL2``, or ``Layer`` for the nearest layer
   * - ``mpldts.geometry.presets.cms`` (``face_factor``, ``add_frames``,
       ``with_attachments``)
     - the pose states the face orientation, the honeycomb panel is part of
       ``CMSXMLSource.station``, and ``SectorRef`` is gone
   * - ``test/geometry/test_legacy.py`` and the 2.9 deprecation warnings
     - nothing: the removed calls are gone, so there is nothing to warn about

``TgSink(target, name_of=...)`` stays: it is not compatibility but the live
seam between the exporter and the simulator's C++ decoders, so the volume names
are unchanged and 3.0 needs no Geant4 rebuild (T-057, T-072).

Migrating from 2.2
------------------

Nothing a user of 2.2 had to change, and nothing is deprecated yet (ADR-018:
the legacy API stays until 3.0). What arrived, in order:

- **2.3:** the geometry is built once per process from ``DTGeometry_v3.xml``
  into specs, a node tree and a frame graph. The constructors, the data
  attributes (``local_center``, ``global_center``, ``direction``, ``bounds``,
  ``rawId``) and the plotting patches behave as before.
- **2.4:** a chamber that is not in the XML: ``StationSpec``/``DetectorSpec``,
  :func:`build_detector <mpldts.geometry.model.build_detector>`,
  :meth:`Station.from_spec <mpldts.geometry.station.Station.from_spec>`, the
  honeycomb as a station attachment, the yoke as detector structure data.
- **2.5:** authoring and export: the short constructors, the JSON documents and
  ``.tg`` output through :class:`~mpldts.export.tg.TgSink`.
- **2.5.1:** ``FrameView.available_frames`` lists the legacy names again
  (``Station``, ``CMS``, ``SL{n}``, the plotting virtual frames) next to the
  frame ids, so a reference frame given by name keeps resolving; the names are
  API until 3.0 (ADR-025).

Behaviour that did change, deliberately:

- the SL2 transform is correct (``BUG-01``): super layer 2 cells used to be off
  by ``√2 . |SL_local_x|``;
- a phi/eta view picks its super layer by orientation, not by ``number == 2``,
  so a custom chamber with a turned layer draws it where it is;
- ``import mpldts.geometry`` reads no XML at all; the source parses when it is
  constructed, once per process;
- per-event data is a table handed to the patch, so the geometry is never
  mutated (ADR-024);
- a cell that is exported needs a material: ``CellGrid.material`` carries it,
  and a physical node without one is an error rather than ``G4_AIR``.
