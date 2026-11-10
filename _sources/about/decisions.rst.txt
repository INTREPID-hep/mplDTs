=========
Decisions
=========

This is the durable record of the architecture decisions behind mplDTs. The
entries were consolidated in 3.0.1 from the design notes that lived in the
repository's agent workspace until that release; the numbers below are the
durable ones, not the numbering those notes happened to use. Dates are the
dates the decision was taken.

An accepted decision is not reopened silently. To change one, write a new ADR
that supersedes it and says why.

ADR-001 — Declarative specs, sources and a builder
--------------------------------------------------
**Date:** 2026-11-05 · **Status:** accepted

**Context.** Every geometry class read the CMS XML singleton directly, so a
detector that was not CMS was impossible without editing the XML, and any
change to the model was entangled with parsing.

**Decision.** Geometry is described by immutable specs (``StationSpec``,
``DetectorSpec`` and their parts), produced by a source (``CMSXMLSource`` for
CMS, JSON or Python for anything else) and turned into runtime objects by one
builder. The model classes consume specs and never perform I/O. The resulting stack has four layers: the specs, the node tree built from them, the frame graph, and the views and exporters that read the graph.

**Consequences.** One extra layer, but the XML becomes replaceable and the spec
is the single source of truth for plotting, export and validation. The
pre-refactor constructors became compatibility wrappers until 3.0.

ADR-002 — One pose per node, child to parent, centimetres
---------------------------------------------------------
**Date:** 2026-11-05 · **Status:** accepted

**Context.** The old code mixed station-frame and super-layer-frame
coordinates, which produced a super layer 2 transform off by 2.47 cm, and the
meaning of ``local_center`` depended on the class.

**Decision.** Every node stores exactly one pose relative to its parent,
``p_parent = R · p_child + t``. Global poses are composed top-down and cached
on the node; nothing else writes a transform. Lengths are cm. Local axes are
x = pitch, y = cell length, z = drift, and sizes are full extents, not
half-lengths.

**Consequences.** The whole class of frame-mixing bugs disappears, and an
exporter is a pose walk. The XML globals stay outside the model as an oracle
only.

ADR-003 — One frame graph, a scoped view per object
---------------------------------------------------
**Date:** 2026-11-05 · **Status:** accepted

**Context.** Each object built its own transform manager and copied sub-chains,
so a copy could go stale and frame names were ambiguous across objects.

**Decision.** One ``FrameGraph`` per detector, with unique path frame ids. Each
object exposes a ``FrameView`` with scoped aliases (``Station``, ``SL2``,
``L1``, ``Cell``, ``CMS``...). Virtual frames are graph edges.
``get_transformation``, ``transform``, ``available_frames`` and ``add``/``remove``
keep working.

**Consequences.** Backward-compatible queries without stale copies; one edge
per node. Global poses are still composed by the builder, not by a graph
search.

ADR-004 — The CMS XML is a source and a preset, not the core
------------------------------------------------------------
**Date:** 2026-11-05 · **Status:** accepted

**Context.** Wheel and sector ranges, face orientation, sector-phi arithmetic,
the MB4 13/14 correction, the SL13 frame and the super layer 2 rotation were
baked into the core classes.

**Decision.** CMS semantics live in the CMS source and the CMS preset; the core
knows only nodes, shapes, poses and frames. CMS behaviour is preserved by the
preset and pinned by the oracle.

**Consequences.** A custom detector does not inherit CMS conventions, and the
core stays small. Plotting must choose the phi and eta views from the geometry
(the orientation decision below), not from a chamber number.

ADR-005 — The XML ``<Wire>`` is the cell; there is no wire object
-----------------------------------------------------------------
**Date:** 2026-11-05 · **Status:** accepted

**Context.** The XML ``<Wire>`` elements were treated as wires, and a separate
wire entity was invented with a radius and a material. The element is the cell
entry: a number and a position.

**Decision.** Model a ``Cell`` (the gas volume and its centre) and a
``CellGrid`` (pitch, count, stagger, first id). The CMS source maps
``<Wire>`` to the cell once. No wire solid is ever exported; analysis code that
needs the anode line uses the cell centre.

**Consequences.** One object instead of three, simpler JSON and no duplicate
concept. The XML vocabulary (``<Wire>``, ``WiresSize``, ``wireNumber``) survives
only inside the CMS source.

ADR-006 — Primitive shapes in the core; CSG out of scope
--------------------------------------------------------
**Date:** 2026-11-05 · **Status:** accepted

**Context.** The design first assumed boxes; tube cells, with a circular face,
are real in CMS, and other primitives may follow.

**Decision.** A ``Shape`` protocol with ``aabb()``, ``volume()`` and
``symmetry_axis()``; implement ``Box`` and ``Tube`` and add primitives when a
detector needs one. Do not implement boolean solids. A backend may accept a
pre-built solid, but the core never grows a CAD kernel.

**Consequences.** No CSG dependency, tubes work, and exotic solids are a
backend concern.

ADR-007 — Geometry is immutable; event data is a table, never a mutation
------------------------------------------------------------------------
**Date:** 2026-11-05 · **Status:** accepted (revised 2026-11-08)

**Context.** A station cache returned a shared mutable station and
``set_cell_attrs`` wrote on shared cells, so one event's data leaked into the
next. A first design put per-event values in an overlay attached to a clone.

**Decision.** Geometry is immutable after build. Per-event values are a table
keyed by ``(sl, l, w)`` handed to the patch
(``DTStationPatch(..., data=rows, vmap="time")``); the geometry is never copied
or written per event. mplDTs does not own an event model: ``Track``, ``Jet``,
``Cone`` and collections belong to the downstream pattern-recognition package,
and the contract between the two is data, not classes. ``AMDTSegments`` stays
as a thin view over that data.

**Consequences.** One station draws many events, and two events never disagree
because the cache changed under them. The overlay API of 2.x was deleted in
3.0, and the downstream package evolves its event model without an mplDTs
release.

ADR-008 — One exporter seam, ``.tg`` first, pyg4ometry optional and later
-------------------------------------------------------------------------
**Date:** 2026-11-05 · **Status:** accepted

**Context.** pyg4ometry is the natural Geant4 backend, but making it a
dependency would drag VTK and CGAL into the critical path, while the simulator
already reads the ASCII ``.tg`` format.

**Decision.** The backend seam is ``VolumeSink``: ``begin``, ``place`` and
``end``, fed by a walk that folds every grouping node into the pose of the next
placement. ``TgSink`` is the first backend. A future pyg4ometry backend is a
new module implementing the same three methods, behind an optional extra
(``mplDTs[g4]``), lazily imported; ``mpldts.geometry`` never imports it and the
core exposes only a 4×4 ``Pose.matrix`` and a backend-neutral shape.

**Consequences.** No dependency now, and the ``.tg`` output matches the CMS
generator. GDML is additive when it comes; the open questions are on the
roadmap page.

ADR-009 — The CMS XML globals are the oracle
--------------------------------------------
**Date:** 2026-11-05 · **Status:** accepted

**Context.** The model has to reproduce CMS, and the XML carries an
independent ``GlobalPosition`` for every cell.

**Decision.** For every chamber, rebuild the cell centres from the specs and
assert ``|computed − XML| < 1e-3 cm``, for all 250 chambers (the ``slow``
marker, plus a representative subset in the normal suite). Keep the XML values
in ``metadata["reference"]``; never read them in the model.

**Consequences.** A pose regression fails the suite instead of a plot. When the
oracle fails, the source is fixed, not the tolerance.

ADR-010 — Physical volume policy
--------------------------------
**Date:** 2026-11-05 · **Status:** accepted

**Context.** The maintainer confirmed which objects exist physically in the
simulation and which are logical grouping.

**Decision.** Physical: the station (air), the drift cells (gas), the honeycomb
(aluminium) and the yoke (iron). Non-physical: super layers and layers, which
are grouping frames. There is no separate wire object. The core carries the
data; the exporter decides how to build it.

**Consequences.** A shallow Geant4 hierarchy (station, cells, attachments), and
a super layer never becomes a volume unless a future detector gives it a shape.

ADR-011 — Honeycomb and yoke are data; CSG stays in a backend
-------------------------------------------------------------
**Date:** 2026-11-05 · **Status:** accepted

**Context.** Honeycomb is a passive box bolted to the station; the yoke is iron
with station-shaped holes. Building the yoke in mplDTs would turn the library
into a CAD kernel.

**Decision.** Honeycomb is a station attachment (``AttachmentSpec`` with shape,
pose and material), derived by the CMS source from the super layer records and
emitted as a node beside the geometry children, so an exporter places it after
the cells. The yoke is a ``StructureSpec`` (shape, subtractions, material) at
detector level and stays data: no node is built and no exporter sees it until a
backend can do booleans. A backend without CSG rejects the structure
explicitly.

**Consequences.** The data model is ready for GDML without a dependency now,
and the yoke keeps working through the simulator's own path in the meantime.
Attachments are invisible to plotting and frame queries.

ADR-012 — Order the work specs first; no speculative modules
------------------------------------------------------------
**Date:** 2026-11-06 · **Status:** accepted

**Context.** The first delivery plan half-refactored the classes before the
specs existed, duplicated the CMS work across phases, built the exporter seam
before any exporter, and planned a YAML-driven CLI nobody had asked for.

**Decision.** Delivery order: specs and the CMS source, then the runtime model
and compatibility, then assemblies and authoring in parallel. The exporter seam
arrives with its first backend, not before. JSON documents and Python
constructors are the authoring surface; a configuration format and a plugin
system are out of scope. Event annotations are optional and off the critical
path.

**Consequences.** One model rewrite instead of two, and the oracle validates a
layer before the next depends on it. A small argparse CLI was added later as a
wrapper over existing calls, not as a framework.

ADR-013 — The detector is the root of the same node tree
--------------------------------------------------------
**Date:** 2026-11-07 · **Status:** accepted

**Context.** Assemblies must place chambers arbitrarily (a one-super-layer or a
five-super-layer station, two stations at an angle) without changing a single
CMS result.

**Decision.** ``build_detector`` makes the detector the root of the same node
tree; stations hang under it at their own poses. CMS-specific frames exist only
in a preset applied to CMS geometries. A custom station is a ``StationSpec``
plus a view and never sees CMS conventions.

**Consequences.** One builder for CMS and custom geometry, and plotting can
choose the views from the geometry instead of the chamber number. The CMS
signature and its oracle are untouched.

ADR-014 — The phi and eta views follow the super layer orientation
------------------------------------------------------------------
**Date:** 2026-11-08 · **Status:** accepted

**Context.** The station patch picked the two views by the CMS convention that
super layer 2 is the turned one. That is a layout fact of CMS chambers, not
geometry: a spec-built chamber drew its middle super layer in the wrong place.

**Decision.** A patch asks the super layer whether it is turned (its x axis runs
along the station length) and draws it in the view where ``faceview`` does not
match. ``faceview`` stays accepted. The segment convention (a segment with
``sl == 2``) stays a rule of the segments, not of the station.

**Consequences.** Identical rectangles for all 250 CMS chambers, pinned by a
test and by the slow sweep, and custom geometry plots correctly. No API change
for callers.

ADR-015 — Releases are tagged on the integration branch; main moves on approval
-------------------------------------------------------------------------------
**Date:** 2026-11-08 · **Status:** accepted (2.x process)

**Context.** The refactor was reviewed on an integration branch and ``main``
had to stay put until the maintainer approved it, but downstream packages
needed an addressable release to pin.

**Decision.** Tag the integration branch when its version metadata and tests
are green. Merging into ``main`` stays a maintainer action; the tag is then an
ancestor of the same commit, so nothing is rewritten.

**Consequences.** Downstream pins a tag while ``main`` is unchanged, and no
merge has to be forced. Since 3.0.1 the releases are tagged on ``main``.

ADR-016 — A document is the spec, an export is placements, names are not geometry
---------------------------------------------------------------------------------
**Date:** 2026-11-08 · **Status:** accepted

**Context.** Writing a detector down (JSON) and out (``.tg``) tempts a
serializer to store derived values and an exporter to inherit the CMS
generator's conventions: the ``Station_W0_Sec1_St1`` names, the layer-encoding
suffix and a hardcoded gas.

**Decision.**

1. A JSON document holds poses, shapes and names only; centres and world poses
   are rebuilt from it. The reader is strict, because a typo in a detector
   description is a detector that is silently wrong.
2. An exporter sees placements, not the tree: ``VolumeSink.begin/place/end``
   over a walk that folds the grouping frames. The backend owns its names.
   ``TgSink`` qualifies names by the exported root, writes no world volume and
   no identity rotation, and refuses a solid node without a material instead of
   defaulting to air.
3. Names are not part of the geometry contract: parity with the CMS generator
   is judged on placements (solid, material, dimensions, rotation, position),
   not on identifiers.

**Consequences.** A file cannot disagree with the model, and a new backend is a
new module with three methods. The naming contract is the exception, below.

.. note::

   Volume names are a live contract with the Geant4 reader, not an
   implementation detail. ``TgSink.name_of(node)`` lets a consumer keep its own
   scheme, and the CMS simulator uses it to emit
   ``Station_W<w>_Sec<s>_St<n>`` and
   ``DriftCell_..._SL<n>_<encoding>``, because its C++ sensitive detectors
   decode the wheel, super layer, layer and wire from those names. The sign of
   a negative wheel is part of the name: StationSD reads ``W-1``, and a
   sanitiser that dropped the dash broke every negative chamber once. The
   geometry never stores a volume name.

ADR-017 — The downstream packages are part of the release gate
--------------------------------------------------------------
**Date:** 2026-11-08 · **Status:** accepted

**Context.** The pattern-recognition package and the Geant4 simulator import a
small, specific surface of mplDTs, and nothing on either side tested it, so a
rename broke them silently.

**Decision.** ``test/downstream`` imports exactly that surface and exercises it
without ROOT or Qt: the spec constructor, the cell-data table, one station patch
per view, the segment views, ``super_layer().layer().cell()`` and the layer id
bounds. ``FrameView.available_frames`` carries the legacy alias names as well.
Each downstream package pins a tag, never a branch, and runs its own suite
against that tag.

**Consequences.** One small test in the normal suite, a patch release (2.5.1)
to restore the aliases, and a release does not ship until both consumers are
green on the candidate tag.

ADR-018 — 3.0 removes compatibility, not the view layer
-------------------------------------------------------
**Date:** 2026-11-08 · **Status:** accepted (completed 2026-11-09)

**Context.** 2.x kept the pre-refactor API alive so the downstream packages
could migrate one step at a time. The shims were cheap but they were a second
way to build a station, so "3.0 someday" needed a written content or it would
become permanent.

**Decision.** Two releases. 2.9.0 warns on every legacy entry point and names
its replacement; 3.0.0 deletes the XML-backed constructor, ``DTGeometry`` and
``DTGEOMETRY``, ``StationsCache``, ``overlay``/``set_cell_attrs``/``dt_info``,
the standalone child constructors, the ``"SuperLayer"`` alias and the CMS
preset. It keeps ``dt_frame.py``, ``super_layer.py``, ``layer.py`` and
``drift_cell.py``: they are the surface the patches draw through, not
compatibility. Per-event data is the patch's ``(sl, l, w)`` table. Volume names
and ``TgSink.name_of`` stay, because they are the live C++ contract, so 3.0
needed no Geant4 change.

**Consequences.** The release is a deletion with no simulator change and
identical ``.tg`` files. Every removal had a replacement, both downstream
packages were green on the tag, and a future backend that reads the node tree
directly may retire the views, but not this release.

ADR-019 — A station may be a passive solid
------------------------------------------
**Date:** 2026-11-09 · **Status:** accepted (3.0.1)

**Context.** A prototype detector needs volumes that are not chambers: a lead
wall between two pairs of super layers, a support panel. ``StationSpec``
already carried a shape and the builder already handled a station with no super
layers; only the validator rejected it.

**Decision.** A station with a shape and no super layers is valid. A station
with neither a shape nor super layers is still rejected.

**Consequences.** The view and the ``.tg`` exporter read it as one volume with
a pose: no cells, nothing sensitive. The relaxed rule cannot
produce an empty volume.

ADR-020 — History rewrite, and only agent-created branches (D1, D2)
-------------------------------------------------------------------
**Date:** 2026-11-10 · **Status:** accepted

**Context.** ``main`` carried 88 commits, half of them bookkeeping for a
working directory that was about to be deleted, plus ticket ids that mean
nothing outside it. Some branches were the maintainer's originals.

**Decision.** Force-push ``main`` with a lease, delete and recreate the tags,
and merge the curated branches with ``--no-ff``. Touch only the branches the
agent created; every other branch, local or remote, is left exactly as it is.
Keep a local ``archive/pre-rewrite`` branch and a bundle as the safety net.

**Consequences.** About 45 meaningful commits with no ticket ids, and the
original branches remain available. Rewriting never happens without the archive.

ADR-021 — Rewritten commits carry the agent identity (D3)
---------------------------------------------------------
**Date:** 2026-11-10 · **Status:** accepted

**Decision.** Commits created by the rewrite are authored and committed by
``DeepSeek Agent <agent@deepseek.local>``, never by Daniel Estrada.

**Consequences.** Provenance is honest: the maintainer is not credited with
commits an agent wrote.

ADR-022 — The agent workspace is removed; the record moves to the docs (D4)
---------------------------------------------------------------------------
**Date:** 2026-11-10 · **Status:** accepted

**Decision.** Delete ``.agents/``. The decision record becomes this page, and
the pyg4ometry plan survives as a GitHub issue plus the roadmap page.

**Consequences.** One source of truth, in the documentation, instead of a second
copy in a working directory that only agents read.

ADR-023 — The beta tags stay, marked as prereleases (D5)
--------------------------------------------------------
**Date:** 2026-11-10 · **Status:** accepted

**Decision.** Keep the two ``-beta`` tags and publish them as prereleases on
GitHub.

**Consequences.** The history of what downstream packages pinned is preserved,
and a reader is warned that those tags are not supported releases.

ADR-024 — Tutorial notebooks use MyST-NB with execution off (D6)
----------------------------------------------------------------
**Date:** 2026-11-10 · **Status:** accepted

**Decision.** Tutorial notebooks are MyST-NB documents with
``nb_execution_mode = "off"``: outputs are committed by hand, CI does not
execute them and there is no pandoc dependency.

**Consequences.** The docs build stays fast and deterministic, but a stale
output has to be regenerated and committed when the code changes.

ADR-025 — ``AGENTS.md`` is the short entry point (D7)
-----------------------------------------------------
**Date:** 2026-11-10 · **Status:** accepted

**Decision.** One root ``AGENTS.md``, short, where every section points at the
code or the documentation page that holds the detail.

**Consequences.** Agent instructions cannot silently diverge from the docs, and
the detail lives in one place.
