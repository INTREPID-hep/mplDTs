=========
Changelog
=========

Newest first. This page is the single changelog of the project and the text of
the GitHub release notes, so it says what a user of the library gets, not which
branch did what. The current release is 3.0.1.

Version 3.0.1
-------------

- A station may be a passive solid. A ``StationSpec`` with a shape and no super
  layers now validates, builds and exports: a lead wall, a support panel, an
  absorber for a prototype detector.
- ``Station.from_spec`` and the ``.tg`` exporter read it as any other station:
  one volume with a pose, no cells and nothing sensitive in
  Geant4.
- A station with neither a solid nor super layers is still rejected, so the
  relaxed rule cannot produce an empty volume.

Version 3.0.0
-------------

- The compatibility layer is gone: ``DTGeometry`` and ``DTGEOMETRY``,
  ``StationsCache``/``STATION_CACHE``, ``Station.overlay``,
  ``set_cell_attrs``/``dt_info``, the XML-backed
  ``Station(wheel, sector, station)``, the standalone
  ``SuperLayer``/``Layer``/``DriftCell`` constructors, the ``"SuperLayer"``
  frame alias and the CMS preset module.
- One way to build a chamber: ``CMSXMLSource`` gives a ``StationSpec``,
  ``build_station`` gives the node tree, ``Station.from_spec`` gives the view
  the patches draw.
- Per-event cell values now go through the patch:
  ``DTStationPatch(..., vmap="time", data=rows)``, where ``rows`` is keyed by
  ``(sl, l, w)``. The old stateful overlay is gone, so two events drawn on one
  station never mutate it.
- The view layer (``dt_frame.py``, ``super_layer.py``, ``layer.py``,
  ``drift_cell.py``) stays on purpose: it is the surface the patches draw
  through, now without XML behind it. ``SL13Center`` is derived by the station
  view and the honeycomb panel is part of the CMS source.
- The ``.tg`` output is untouched: neither the file format nor the volume names
  change, so the Geant4 side needs no update.

.. note::

   Breaking change. Migration in one line: replace
   ``DTGeometry``/``DTGEOMETRY``/``StationsCache`` with ``CMSXMLSource`` and
   ``Station.from_spec()``, and replace ``dt_info``/``overlay`` with
   ``DTStationPatch(..., vmap="time", data=rows)``.

.. code-block:: python

    from mpldts.geometry import Station
    from mpldts.geometry.sources import CMSXMLSource

    source = CMSXMLSource()
    station = Station.from_spec(source.station(-2, 1, 2), -2, 1, 2)

    print(station.wheel, station.sector, station.number)
    print(len(station.super_layers), "super layers")
    print(tuple(round(float(value), 2) for value in station.bounds))

.. code-block:: text

    -2 1 2
    3 super layers
    (266.8, 36.2, 251.1)

Version 2.9.1
-------------

- A negative wheel keeps its minus in the ``.tg`` volume names:
  ``Station_W-1_Sec1_St1`` instead of ``Station_W_1_Sec1_St1``. The simulator
  decoders read that sign, so negative-wheel chambers and the yoke that looks
  for their solids resolve again.
- The name sanitiser accepts the dash, which is a legal Geant4 name. No API
  change and no other name changes.

Version 2.9.0
-------------

- The deprecation release: every legacy entry point that 3.0 removes now emits
  one ``DeprecationWarning`` naming its replacement — ``Station(wheel, sector,
  station)``, ``set_cell_attrs``, ``overlay``, ``StationsCache.get``, the
  standalone ``SuperLayer``/``Layer``/``DriftCell`` constructors,
  ``DTGeometry``/``DTGEOMETRY`` and ``TgSink(name_of=)``.
- No behaviour change: the pipeline that survives is silent, which is what the
  tests pin.
- The "Migrating to 3.0" table in the runtime chapter maps every old call to
  its new one.

.. note::

   This is a warning-only release, not a break. It is also the migration
   checklist: run your suite with ``-W error::DeprecationWarning`` and what
   fails is exactly what 3.0 removes.

Version 2.8.0
-------------

- A thin command line: ``mpldts info|convert|plot``, installed as a console
  script. ``info`` prints what a document holds, ``convert`` writes a ``.tg``
  file, ``plot`` writes an SVG, and ``--station`` picks one chamber out of a
  detector document.
- Errors are one line on stderr and exit code 2, never a traceback, and
  matplotlib is imported only by the plotting command.
- Package URLs moved to the ``INTREPID-hep`` organisation.

Version 2.7.0
-------------

- ``TgSink(name_of=...)`` lets the consumer own the volume names. The
  simulator supplies its CMS scheme, ``Station_W<w>_Sec<s>_St<n>`` and
  ``DriftCell_..._SL<n>_<encoding>``, because its C++ sensitive detectors
  parse those names.
- Copy numbers restart for every volume placed in a mother, as in the reference
  CMS generator, because the cell decoder maps the copy number to the layer and
  wire inside a super layer.
- Names and rotation matrices are qualified by the exported root, so several
  station files can be included in one Geant4 document without collisions.
- The naming contract between the exporter and the Geant4 reader is documented.

Version 2.6.0
-------------

- ``DTObjectsPatch`` draws points and polylines given in any frame the graph
  knows, projected exactly like the cells, so simhits, tracks and showers stop
  being ad-hoc ``scatter``/``plot`` calls.
- A segment that carries a ``length`` is drawn with its physical span; without
  one it keeps the old mark size.
- No new dependency.

Version 2.5.1
-------------

- ``FrameView.available_frames`` lists the legacy alias names as well as the
  path frame ids, which is what the segment views and the downstream packages
  resolve their reference frames through.
- Patch release: no other API change.

Version 2.5.0
-------------

- Authoring shortcuts: ``make_layer``, ``make_superlayer``, ``make_station``
  and ``make_detector`` fill the defaults that a hand-written spec should not
  repeat.
- Detector documents: JSON in and out (``mpldts.station/2`` and
  ``mpldts.detector/2``). The document holds poses, shapes and names only;
  centres and world poses are rebuilt, and the reader is strict because a typo
  in a detector description is a detector that is silently wrong.
- Export seam: ``VolumeSink``, ``RecordingSink`` and ``TgSink``. The walk folds
  the grouping frames into the placements and the ``.tg`` output matches the
  CMS generator (same placements, solids, materials and rotations).
- A tutorial and runnable examples for the whole authoring path.

Version 2.4.0
-------------

- Assemblies: a ``DetectorSpec`` is the root of the same node tree, stations
  hang under it at their own poses, and a custom one-super-layer or
  five-super-layer chamber builds and plots.
- ``Station.from_spec`` builds a station that is not in the CMS XML, and the
  phi/eta view follows the super layer orientation instead of the CMS
  convention that super layer 2 is the turned one.
- Honeycomb is a station attachment: an aluminium panel derived from the super
  layer records, exported as one volume beside the cells.
- The yoke is a ``StructureSpec`` data hook only; no boolean solids are built
  in the library.

Version 2.3.0
-------------

- The geometry core is rebuilt around four layers: the CMS XML becomes
  immutable specs, a builder turns them into a node tree with one
  parent-relative pose per node, a frame graph serves named frames, and the
  legacy classes become views over it.
- ``CMSXMLSource`` and the specs are public, and ``build_station`` is the one
  builder the CMS chambers and any custom station share.
- The plotting API and the old constructors keep working; the 250 CMS chambers
  draw the same rectangles as before, including the super layer 2 transform that could be off by up to
  2.47 cm.
- Per-event data no longer writes on a shared cached station: every event gets
  its own values.
- One XML parse and one build per chamber, instead of a parse per object.

Version 2.2.0
-------------

- Segments are refactored around an explicit reference frame, and the frame
  transformations are declared at the parent (the station) instead of being
  copied into every object.
- Local and global direction are separate attributes, so a segment can be
  placed in the frame it was measured in and still be drawn anywhere the graph
  knows.
- ``AMDTSegments`` defaults to the centre of the outermost super layers as its
  reference frame.

Version 2.2.0-beta
------------------

- Beta: a station cache builds each chamber once and returns it afterwards,
  and ``DTGEOMETRY.get`` is memoised, so repeated event plots stop reparsing
  the XML.

.. note::

   Beta pre-release tag, published as a prerelease and kept for the record.
   The downstream packages pinned it before 2.5.1.

Version 2.1.1-beta
------------------

- Beta: ``DTGEOMETRY.get`` is cached and some typos in the released code are
  fixed.

.. note::

   Beta pre-release tag, published as a prerelease and kept for the record.

Version 2.1.0
-------------

- DT segments enter the package: ``Segment``/``Segments`` the AM segment views and their patches.
- A transformation now distinguishes a point from a vector, so directions are
  no longer translated by mistake.
- Type fixes for the ``pytransform3d`` API.

Version 2.0.0
-------------

- ``DTGeometry.xml`` version 3 carries local and global coordinates for every
  cell, and the geometry classes read it.
- A transformation manager is a member of each frame, and the patches express
  their matplotlib ``Affine2D`` from it instead of hand-built matrices.
- The patches module is reworked around those frame transformations.
- The project gets its licence.

Version 1.1.0
-------------

- ``DTGeometry.xml`` version 2 adds local and global coordinates at cell level,
  and the package is restructured to read them.
- Theta and eta helpers are added to the transform module and exposed as cell
  attributes.

Version 1.0.0
-------------

- All the DT drawing options: local, global, phi and eta views, by drawing a
  local chamber and transforming it with matplotlib for each view.
- ``DTGeometry.xml`` version 1 names the first drift cell position per layer.
- Local cell positions in a layer are computed from the wire number.
- First release.
