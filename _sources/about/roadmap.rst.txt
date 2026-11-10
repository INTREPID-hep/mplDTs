=======
Roadmap
=======

mplDTs is at 3.0.1: the model, the plotting, the authoring path and the ``.tg``
exporter are done. Nothing below is committed work or a branch in progress —
this page records the ideas that are worth keeping, the one open item that touches the C++ contract
(the volume names), and what was considered and rejected. A reader should
not expect any of it in the next release unless an issue says otherwise.

GDML through pyg4ometry
-----------------------

**Today.** ``docs/examples/export_tg.py`` builds a station, walks its solid
placements and writes a ``.tg`` text file through ``mpldts.export.TgSink``. That
is the format the Geant4 simulation reads with ``G4tgbVolumeMgr``: it holds the
solids, the volumes and the placements, and the world volume and identity
rotation stay in the document that includes it.

Every exporter implements the same three-method seam, so a new format is a new
module and nothing else:

.. code-block:: python

    from mpldts.export import RecordingSink, export_volumes
    from mpldts.geometry import build_station
    from mpldts.geometry.sources import CMSXMLSource

    node = build_station(CMSXMLSource().station(0, 1, 1))
    sink = RecordingSink()
    export_volumes(node, sink)

    print(len(sink.placements), "placements")
    print(sorted({placement.node.kind for placement in sink.placements}))

.. code-block:: text

    622 placements
    ['attachment', 'cell', 'station']

The same walk could feed a second sink. **The idea** is
``PyG4ometrySink(VolumeSink)`` in ``mpldts/export/pyg4ometry.py``: on
``begin`` it creates a pyg4ometry registry and the world logical volume, on
``place`` it maps each node's shape, material and pose to a solid, a logical
volume and a physical volume, and on ``end`` it writes GDML. Geant4 would then
read the detector through the normal GDML loader instead of the ASCII format,
which brings overlap checks, a standard file format and the rest of the
pyg4ometry tooling for free. It is an idea, not work in progress: there is no
module, no extra and no branch for it.

**The open question** is packaging: should the import be an optional extra
(``mplDTs[g4]``, lazily imported, never installed by CI or by the core) or a
hard dependency of the library? The current design assumes the optional extra,
because the core must import and plot without pyg4ometry, VTK or CGAL; whether
users would rather have one install is a decision for whoever writes the
backend. The other open points are smaller: the material map (node material
name to pyg4ometry material, including the gas mixture), the yoke (boolean
solids in the backend, or an explicit refusal), and the validation list — pose
round-trip, solid AABB, zero overlaps, GDML written and read back, and an
optional dependency that is absent from ``mpldts.geometry``.

The original planning notes kept this deliberately small: the seam, the
backend-neutral shape and the placement walk were built first, the backend was
deferred so it could be additive, and the acceptance list was written down
before the code so that adding it later would be a new module rather than a
refactor. The invariants in those notes still hold: no backend import in the
core, grouping nodes folded, poses as 4×4 matrices, the yoke either built with
booleans or rejected, and pyg4ometry never mandatory.

Volume renaming
---------------

The ``.tg`` volume names are a live contract with the Geant4 simulation, not
cosmetics. ``Station_W<w>_Sec<s>_St<n>`` carries the wheel, the sector and the
station; ``StationSD`` reads the wheel and the sign of a negative wheel from
it. Cell volumes carry ``DriftCell_..._SL<n>_<encoding>``, and the layer and
wire are decoded from the copy number of the cell inside its super layer. Every
hit written by the simulation decodes through exactly that scheme.

A rename is therefore an open item, not a cleanup: it breaks the C++ reader and
makes every existing ntuple incomparable with new files unless the decode is
proved identical. Historical evidence: a name sanitiser that turned
``Station_W-1_Sec1_St1`` into ``Station_W_1_Sec1_St1`` silently broke every
negative-wheel chamber and the yoke that looks for its solids; 2.9.1 fixed it by
keeping the dash.

The condition to reopen it is a golden identity table first: one row per
(volume name, copy number) giving the ``(wheel, sector, station, sl, layer,
wire)`` it decodes to — 171,732 rows for the 250 CMS chambers — produced by the
old decoder and re-checked against the new one, plus one seeded Geant4 run that
matches the old geometry hit for hit. The rename also has to ship alone, not
inside an API release, and the downstream package that writes the tuples has to
move in the same window. It is not scheduled.

Considered and rejected
-----------------------

- **An event model in mplDTs** (``Event``, ``Track``, ``Jet``, collections, an
  event JSON). The pattern-recognition package already owns a richer,
  configuration-declared model; a second one would be a duplicate source of
  truth that both packages have to keep in agreement. mplDTs ships geometry,
  frames, patches and exporters, and the contract is a ``(sl, l, w)`` data table
  with value columns.
- **A YAML-driven CLI and configuration system.** It adds a dependency and a
  framework for a user nobody could name, when JSON documents, four constructors
  and a thin ``argparse`` CLI cover the same cases. The CLI that exists is a
  wrapper over library calls, not a configuration layer.
- **Boolean solids in the core** (the yoke as a CSG model inside mplDTs). It
  would turn a geometry description library into a CAD kernel and pull a solid
  modelling stack into every install. The yoke stays a data structure
  (``StructureSpec``) and the simulator's own path, until a backend can build
  booleans outside the core.
- **A separate wire object.** The XML ``<Wire>`` entry is the cell: a number and
  a centre. A second entity with its own radius, material and volume was tried
  in the design and deleted, because the detector has no separate wire solid and
  the duplicate concept leaked into specs, JSON and exporters.
