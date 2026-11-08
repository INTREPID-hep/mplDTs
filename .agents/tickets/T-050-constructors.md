# T-050 — Short constructors for hand-written specs

- **Status:** done
- **Phase:** 5
- **Epic:** E5 Authoring and export
- **Depends on:** T-030 (done)
- **Branch:** `feature/phase-5-authoring`
- **PR:** — (branch pushed; the maintainer merges)
- **Owner:** —
- **Labels:** model, authoring
- **Completed:** 2026-11-08

## Context

The spec dataclasses are explicit by design, but a test beam station written by
hand should not repeat `pose=Pose.identity()` and `shape=None` on every
layer. The plan asks for four constructors that fill the boring defaults.

## What was delivered

- `mpldts/geometry/constructors.py`: `make_layer`, `make_superlayer`,
  `make_station`, `make_detector`.
- Defaults: identity pose, no envelope, `G4_AIR` for a station,
  `G4_Galactic` for the detector; attachments and structure are copied into
  lists so a tuple is accepted.
- No eager validation: `validate()` stays the single gate, so a spec built
  with the helpers fails exactly where a hand-built spec fails.
- `test/geometry/test_constructors.py` (2 tests): the defaults, and a spec built
  with the helpers is the same document as the long hand-written one.

## Out of scope

- A builder DSL, a YAML front end or a CLI (T-053 is deferred).
- Guessing geometry: no helper invents a pitch, a count or an envelope.

## Acceptance criteria

- [x] The four constructors exist and fill the documented defaults.
- [x] A spec built with them is identical (same JSON document) to the
      hand-written equivalent.
- [x] No validation is duplicated in the builders.

## Verification

```python
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_constructors.py
```

## Risks / notes

- The builders are thin on purpose: if one starts doing work (deriving a pose,
  fitting a grid), the work belongs in the source or in `validate`.
