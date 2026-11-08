# Migration to 3.0 — the compatibility removal plan

**Status:** S1 shipped in 2.9.0 (T-074); S2 and S3 shipped in **3.0.0**
(2026-11-09, T-070, T-071, T-073). S4 (the volume names) was **skipped**:
``TgSink.name_of`` is the live seam with the simulator's C++ decoders, not
compatibility, so 3.0 deleted compatibility only and left the names, the C++
and the .tg files untouched. S5 (the yoke as CSG) stays with T-060. §9 records
what the release actually deleted, including where it deviated from §1.
**Decided:** 2026-11-08 ([ADR-026](decisions.md)).
**Board:** [T-070](tickets/T-070-legacy-layer-removal.md),
[T-071](tickets/T-071-event-contract.md),
[T-072](tickets/T-072-volume-names.md),
[T-073](tickets/T-073-release-3.0.md),
[T-074](tickets/T-074-deprecations-2.9.md) (done, 2.9.0).
**Purpose:** 2.x keeps the pre-refactor API alive so the downstream packages
migrated one step at a time (ADR-025). This is the plan that removes it in one
deliberate, gated release instead of letting the shims become permanent.

---

## 1. What 3.0 removes

Measured on `v2.8.0`. §9 is the correction: the three view classes in
rows 5-7 stayed, because the patches draw with them, so the ~1.2-1.5k lines
below are the classes the release really deleted plus the tests.

| Goes | Lines | Why it exists |
|---|---|---|
| `mpldts/geometry/station.py` | 557 | the XML-backed `Station(wheel, sector, station)`, `transformer`, `bounds`, the raw-id plumbing |
| `mpldts/geometry/dt_frame.py` | 310 | the legacy `TransformManager` wrapper over the frame graph |
| `mpldts/geometry/_geometry.py` | 245 | `DTGeometry` + the lazy `DTGEOMETRY` proxy, absorbed by `CMSXMLSource` |
| `super_layer.py`, `layer.py`, `drift_cell.py` | 286 | view classes nothing would build any more |
| `presets/cms.py` | 88 | folds onto the spec path |
| `test/geometry/test_legacy.py` | 177 | the compatibility tests |
| `StationsCache`, `dt_info`, `set_cell_attrs`, `Station.overlay` | — | the per-event side channel that produced `BUG-02`; the ADR-024 `(sl, l, w)` table replaces it |
| the `"SuperLayer"` frame alias | — | compatibility only |
| `TgSink.name_of` + per-volume copy numbering | — | compatibility with the current `DriftCellSD` decoder |
| the hand-written yoke strings in `DTG4Simulator` | — | ASCII `.tg` cannot do booleans (needs T-060) |

Roughly 1.2–1.5k lines and two side channels less, and one way to build a
station instead of three. The rule stays: **what goes is compatibility, not
concepts.**

## 2. What does not change

`specs.py`, `model.py`, `frames.py` (minus the alias table),
`sources/cms_xml.py`, `serialize.py`, `constructors.py`, `export/`, the
patches, the CLI, the JSON schema and every measured number. That half is the
model and it is already the clean one; 3.0 does not shrink it.

## 3. The sequence

The order is what makes it safe: each step leaves both consumers green, and the
two breaking steps share one release window.

### S1 — the deprecation release (2.9.0, T-074) — done

- Every API in §1 that has a call site gets a `DeprecationWarning` with the
  replacement named, and `docs/src/geometry/runtime.rst` grows the "Migrating
  to 3.0" table (old call → new call). No behaviour changes.
- The frame alias `"SuperLayer"` is in the table and not in a warning: a
  dictionary lookup has no call site to report.
- Both downstream packages pin `v2.9.0` and run their suites against it: with
  `-W error::DeprecationWarning` they now see, one warning at a time,
  everything they use that 3.0 removes.

### S2 — downstream move to the new surface (T-071, T-073) — done (3.0.0)

- `DTPatternRecognition`: `StationsCache.get(dt_info=dataframe)` becomes the
  ADR-024 contract table; `Station` usage becomes the spec/node constructor.
  Its mplDTs surface is small (7 imports in 3 files, 18 legacy attribute uses).
- `DTG4Simulator`: the generator stops importing anything legacy
  (`Station` is only used by the yoke by then).

### S3 — mplDTs 3.0.0 (T-070) — done (3.0.0)

- Delete §1's first six rows, the alias table and `StationsCache`. The public
  entry points are `CMSXMLSource` → `StationSpec`/`DetectorSpec` →
  `build_station`/`build_detector` → nodes and frames, and one station
  constructor for the patches (`Station.from_spec`, kept, no XML behind it).
- `test/geometry/test_legacy.py` goes; `test/downstream` grows to cover what it
  used to pin.

### S4 — the name contract (T-072), in the same window as S3 — skipped

Skipped on purpose (ADR-027). The volume names are the contract with
`DriftCellSD` and `StationSD`, and changing them without the golden
identity table of §4 would make every existing ntuple incomparable. T-072 keeps
its own gate and can ship as 3.1 or 4.0.

- mplDTs drops `name_of`; `TgSink` emits `DriftCell_<station>_<SL>`.
- `DTG4Simulator`: `generate_geometry_data.py` drops the naming hook, and
  `DriftCellSD::DecodeCellID` / `StationSD::DecodeStationID` read the new names.
  The cell's `(layer, wire)` has to come from something explicit — a copy-number
  block per super layer or a name field — not from the per-layer encoding.

### S5 — the yoke as CSG (T-060, after 3.0.0)

With a booleans-capable backend the yoke leaves the simulator's string builder.
Independent of 3.0 and can ship as 3.0.x.

## 4. The trap: the cell identity

The encoding in `DriftCell_.._SL<n>_<encoding>` is decoded into
`(wheel, sector, station, sl, layer, wire)` and that tuple is what dtpr writes
into its ntuples. **The new scheme must decode to the same tuple for all 250
chambers**, or every old file becomes incomparable with the new ones.

That is a test, not a hope (T-072): a golden table of 171732
`(volume, copyNo) → (wheel, sector, station, sl, layer, wire)` rows produced by
the old decoder and re-checked against the new one.

The trap is not hypothetical. Validating the 2.9 chain found that `TgSink`'s
name sanitiser rewrote `Station_W-1_Sec1_St1` into `Station_W_1_Sec1_St1`:
every negative-wheel chamber stopped decoding and the yoke could not find its
solids. 2.9.1 keeps the dash. Any change to a name is exactly this risky, which
is why T-072 needs the table before it touches one.

## 5. Gates

3.0 ships only when all of these hold:

- **G1 — every removal has a replacement** written in the "Migrating to 3.0"
  table, and `test/downstream` imports the new surface (it already pins the old
  one, T-040).
- **G2 — the cell identity table** (§4) matches for all 250 chambers.
- **G3 — both downstream packages are green on the candidate tag**, in their own
  repositories, with their pins moved (ADR-025).
- **G4 — one seeded Geant4 run** with the new files matches the old one hit for
  hit (same seed, same macro).
- **G5 — a clean 3.0 install** needs nothing legacy: `pip install mplDTs`, build
  a station from the bundled XML, plot it, export it.

## 6. Anti-patterns (reject these)

- Removing a shim before its replacement is exercised by `test/downstream`.
- Changing the names in a different release than the API: the simulator's C++
  would be broken in between.
- Retiring `.tg` in the same window (make it an explicit ADR, later).
- "Cleaning while we're there": this release is a deletion, not a redesign. Any
  new idea gets its own ticket.
- Deleting the legacy classes and keeping a private copy of them for the
  patches; the patches take the model or nothing.

## 7. Effort

Two days in mplDTs (mostly deletions and the migration table), one day in dtpr,
one day in the simulator plus one validation run. Gated on both consumers
having a free window, not on engineering.

## 8. Why not do it now

The gain is size and one-way-to-do-it, not capability: nothing in 2.x is
deprecated on a timer and no shim is on a hot path. Doing it now would mean
dtpr and the simulator move before their own work is settled, which is the
reverse of the order that made this refactor safe.

---

## 9. What 3.0.0 actually did (2026-11-09)

The release deleted the compatibility, not the drawing surface: 42 files,
+569 / -1567 lines, plus two new test modules (``test_views.py``,
``test_station_patch.py``).

Deleted: `geometry/_geometry.py` (`DTGeometry`, `DTGEOMETRY`),
`_deprecation.py`, `geometry/presets/`, the XML-backed
`Station(wheel, sector, station)` and its chamber cache (`_built`,
`station_for`), `StationsCache`/`STATION_CACHE`,
`Station.overlay`, `set_cell_attrs`/`dt_info`, the standalone
`SuperLayer(rawId=)` / `Layer(rawId=)` / `DriftCell(number=)`
constructors, the `"SuperLayer"` frame alias, `test_legacy.py` and
`test_deprecations.py`.

Kept, against §1: `dt_frame.py`, `super_layer.py`, `layer.py`,
`drift_cell.py`. They are what `DTStationPatch` draws (`bounds`,
`local_cords_at_min`, `transformer`, `super_layers/layers/cells`);
deleting them was a rewrite of 627 lines of patches, which §6 forbids and S3's
acceptance criteria assume away. They are no longer compatibility, they are the
view layer (ADR-027).

| Gone | Now |
|---|---|
| `Station(w, s, n)` | `Station.from_spec(source.station(w, s, n), w, s, n)` |
| `dt_info`, `overlay`, `STATION_CACHE` | `DTStationPatch(..., data=rows)` keyed by `(sl, l, w)` (ADR-024) |
| `DTGeometry`, `DTGEOMETRY` | `CMSXMLSource()` (unchanged since 2.9) |

Four details a reader will otherwise trip over:

- **the honeycomb** moved from `presets/cms.py` into
  `CMSXMLSource._station_spec`: it is derived from the XML record exactly
  like the poses, so a CMS `StationSpec` always carries the panel and the
  generator's `include_honeycomb` switch is redundant.
- **`SL13Center`** moved from the preset into
  `station._add_natural_views`: it is the centre of the outermost super
  layers of any station, which is what `AMDTSegments`' default reference
  frame needs. `SectorRef` (CMS sector arithmetic) is gone.
- **the chamber numbers** stay on the view (`wheel`, `sector`,
  `number`) only because dtpr labels a plot window with them; a station that
  is not a CMS chamber reads `None`.
- **grouping frames** (`superlayer`, `layer`) carry no solid, so the view
  derives their `bounds` from the union of their children. The patches
  therefore still draw the SL and layer outlines; the box is the envelope of
  the cells, slightly smaller than the XML aluminium frame (3% on an MB1).

Gates: **G1** met (`docs/src/geometry/runtime.rst`, "What 3.0 removed").
**G2** was S4's and is not taken. **G3** is the dtpr and simulator work in the
same window (pins move to `v3.0.0`). **G4** is a no-op: the names did not
change, so the regenerated build is byte-identical and no seeded Geant4 run is
needed. **G5** met: `test/geometry/test_runtime.py` proves that importing
`mpldts.geometry` never imports the XML module, and `test_smoke.py` builds
a chamber from the bundled XML through the source.

