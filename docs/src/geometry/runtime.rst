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

.. autoclass:: mpldts.geometry.specs.DetectorSpec

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

.. literalinclude:: ../../examples/custom_station.py
    :language: python
    :lines: 1-66

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
