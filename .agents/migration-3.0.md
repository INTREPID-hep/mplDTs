# Migration to 3.0 — the compatibility removal plan

**Status:** S1 shipped in 2.9.0 (T-074). The removal itself is planned and not
started: nothing else here runs until the entry gate (§5) is met; 2.x carries
no deprecation timer, so waiting costs nothing.
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

Measured on `v2.8.0`:

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

### S2 — downstream move to the new surface (T-071, T-073)

- `DTPatternRecognition`: `StationsCache.get(dt_info=dataframe)` becomes the
  ADR-024 contract table; `Station` usage becomes the spec/node constructor.
  Its mplDTs surface is small (7 imports in 3 files, 18 legacy attribute uses).
- `DTG4Simulator`: the generator stops importing anything legacy
  (`Station` is only used by the yoke by then).

### S3 — mplDTs 3.0.0 (T-070)

- Delete §1's first six rows, the alias table and `StationsCache`. The public
  entry points are `CMSXMLSource` → `StationSpec`/`DetectorSpec` →
  `build_station`/`build_detector` → nodes and frames, and one station
  constructor for the patches (`Station.from_spec`, kept, no XML behind it).
- `test/geometry/test_legacy.py` goes; `test/downstream` grows to cover what it
  used to pin.

### S4 — the name contract (T-072), in the same window as S3

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
