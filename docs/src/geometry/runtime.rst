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

The CMS-only frames (`SectorRef` and `SL13Center`) live in
:mod:`mpldts.geometry.presets.cms` and are added to CMS chambers only; a
station built from a spec gets `StationNvPhi` and `StationNvEta` and
nothing else. The face factor that orients the natural views comes from the
station pose, so a custom chamber inverts its views like a CMS one.

.. automodule:: mpldts.geometry.presets.cms
    :members:

.. literalinclude:: ../../examples/custom_station.py
    :language: python
    :lines: 1-66

Authoring: short constructors and JSON
------------------------------------------------------------

Four constructors fill the defaults that a hand-written spec should not repeat
(identity pose, no envelope, air in the chamber, vacuum in the world). They do
not validate eagerly: :func:`validate <mpldts.geometry.specs.validate>` stays the
single gate, so a spec built with them fails where a hand-built one fails.

.. autofunction:: mpldts.geometry.builders.make_layer

.. autofunction:: mpldts.geometry.builders.make_superlayer

.. autofunction:: mpldts.geometry.builders.make_station

.. autofunction:: mpldts.geometry.builders.make_detector

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

.. autoclass:: mpldts.export.tg.TgSink

.. autoexception:: mpldts.export.tg.TgFormatError

The example below is the whole path: build the spec with the short
constructors, write the JSON document, read it back, build the node tree from
the document, plot the chamber with the legacy patches and export the volumes.

.. literalinclude:: ../../examples/export_tg.py
    :language: python

The CMS source
--------------

``CMSXMLSource`` is the only reader of ``DTGeometry_v3.xml``. It parses the
file once and answers with specs, or with the verbatim XML values the legacy
classes expose.

.. autoclass:: mpldts.geometry.sources.cms_xml.CMSXMLSource
    :members: chamber_keys, number_of_chambers, station, detector, cell_centres

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
scoped aliases (``Station``, ``SuperLayer``, ``SL2``, ``L1``, ``Cell``, ``CMS``,
plus the plotting virtual frames) and transforms points between them.

.. autoclass:: mpldts.geometry.frames.FrameGraph
    :members: add_nodes, add_edge, add_virtual, transform, matrix, frames

.. autoclass:: mpldts.geometry.frames.FrameView
    :members: transform, get_transformation, add, remove

Immutability and per-event data
-------------------------------

A chamber is built once and every :class:`~mpldts.geometry.station.Station` is
a view over that build, so the same object is shared by every caller. Per-event
data therefore never goes on the shared geometry: use
:meth:`Station.overlay <mpldts.geometry.station.Station.overlay>`, which clones
the view, keeps the node tree and the graph, and applies the drift-cell
attributes to the clone.

.. code-block:: python

    from mpldts.geometry import STATION_CACHE

    station = STATION_CACHE.get(-2, 1, 2)              # shared geometry
    event = STATION_CACHE.get(-2, 1, 2, dt_info=[{"sl": 1, "l": 1, "w": 1, "t": 12.5}])
    station.super_layer(1).layer(1).cell(1).t          # unchanged
    event.super_layer(1).layer(1).cell(1).t            # 12.5

Cost on a warm process: importing ``mpldts.geometry`` does not touch the XML,
the first build of a chamber is tens of milliseconds, and later stations are a
few milliseconds each.

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

Behaviour that did change, deliberately:

- the SL2 transform is correct (``BUG-01``): super layer 2 cells used to be off
  by ``√2 . |SL_local_x|``;
- a phi/eta view picks its super layer by orientation, not by ``number == 2``,
  so a custom chamber with a turned layer draws it where it is;
- ``DTGEOMETRY`` parses the XML on first use, never at import;
- per-event data goes through
  :meth:`Station.overlay <mpldts.geometry.station.Station.overlay>` (or the
  cache with ``dt_info``), which never mutates the shared chamber;
- a cell that is exported needs a material: ``CellGrid.material`` carries it,
  and a physical node without one is an error rather than ``G4_AIR``.
