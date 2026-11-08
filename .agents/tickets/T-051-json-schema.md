# T-051 — JSON documents for detectors and stations

- **Status:** done
- **Phase:** 5
- **Epic:** E5 Authoring and export
- **Depends on:** T-030 (done)
- **Branch:** `feature/phase-5-authoring`
- **PR:** — (branch pushed; the maintainer merges)
- **Owner:** —
- **Labels:** model, serialization
- **Completed:** 2026-11-08

## Context

A detector description that only exists as Python is a description only Python
can read. The plan asks for one explicit JSON schema (`mpldts.detector/2`)
that stores the spec and nothing else: poses, shapes, names. Derived values
(cell centres, world poses, offsets) are rebuilt, never stored, so a document
cannot disagree with the model.

## What was delivered

- `mpldts/geometry/serialize.py`: `to_dict` / `from_dict` / `to_json` /
  `from_json` for a `StationSpec` (`mpldts.station/2`) and a
  `DetectorSpec` (`mpldts.detector/2`), including super layers, layers,
  cell grids, attachments and structure entries.
- The rotation is a 3x3 matrix in rows, the translation a triple; boxes and
  tubes carry their real dimensions (no half-widths, no unit ambiguity).
- Strict reading: unknown keys, a missing field, a wrong type, an unknown shape
  kind, a wrong schema string, a non-orthonormal or mirrored rotation and a grid
  that does not fit are errors with the path to the problem. `from_dict` runs
  `validate()` as its last step, so a document that loads is a document that
  builds.
- Defaults on read only where the field is genuinely optional: `first_id` 1,
  `offset` 0, a tube `axis` `y` and `inner_radius` 0, station material
  `G4_AIR`, detector material `G4_Galactic`, attachment `G4_Al`, structure
  `G4_Fe`.
- `test/geometry/test_serialize.py` (14 tests).

## Decisions

- **Two documents, one module.** A station document is what a test beam user
  writes by hand; the detector document is the assembly. Both share the reader.
- **No derived values.** A document is the spec, not a cache of the model; the
  round trip is `to_dict(from_dict(document)) == document`.
- **Strict on input, complete on output.** Optional fields are written when
  they carry information and omitted when they are `None`; the reader accepts
  the defaults above.
- **JSON only.** No YAML, no file helpers: `path.write_text(to_json(spec))` is
  the whole I/O layer (and keeps the tests free of temp files).

## Out of scope

- A JSON Schema file for editors and CI linting: the strict reader is the
  contract; add the schema file when an editor asks for it.
- Event documents: not planned (ADR-024); the event model is in
  `DTPatternRecognition`.
- The CLI (T-053).
- Convenience builders that make hand-written Python shorter: T-050.

## Acceptance criteria

- [x] A station and a detector round-trip through JSON without loss.
- [x] A CMS chamber with its honeycomb round-trips field by field.
- [x] The reader rejects unknown keys, wrong types, bad rotations and grids
      that do not fit.
- [x] A document loads, builds and exports to `.tg`.

## Verification

```python
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_serialize.py
PYTHONPATH=/home/destrada/mplDTs pytest -q
```

## Risks / notes

- A CMS chamber document is about 13 kB with `indent=2` (3 MB for the whole
  detector): verbose but diffable, and small next to the 20 MB XML.
- The schema version is in the document, so a future `/3` can be read next to
  `/2` instead of breaking the old files.
