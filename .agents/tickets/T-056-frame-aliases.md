# T-056 — `FrameView.available_frames` accepts the legacy aliases

- **Status:** done
- **Phase:** 4
- **Epic:** E4 Downstream
- **Depends on:** T-021
- **Branch:** `feature/T-056-frame-aliases`
- **PR:** —
- **Owner:** unassigned
- **Labels:** compat, bug, frames

## Context

`AMDTSegment._compute_segment_properties` (and therefore
`AMDTSegments(reference_frame=...)`) checks
`rframe not in self.parent.transformer.available_frames` and then transforms
from that frame to `Station`.

- On 2.2.0-beta: `available_frames` is the set of names passed to `add()`, so
  `"Station"` and `"SL13Center"` are members; `AMDTSegments` works.
- On 2.5.0: `FrameView.available_frames` returns **resolved frame ids only**
  (`Station_W0_Sec1_St1`, `/SL1`, ...), so the alias is not a member and
  `AMDTSegments` raises
  `ValueError: The specified reference frame 'Station' is not available in the parent transformer.`

The design promised "aliases in scope + full paths"
(`docs/design/generalization-plan.md` §5 table), so this is a bug in the
implementation, not a design change.

## Scope

- `FrameView.available_frames`: add the alias names that resolve in scope
  alongside the frame ids (superset; no id is removed).
- Regression test: `"Station"`, `"CMS"`, `"SL1"` and `"SL13Center"` are members
  for a CMS chamber, and `AMDTSegments(..., reference_frame="Station")` builds
  with the same centres as the 2.2.0-beta output.
- Patch release: 2.5.1 (`__version__`, `pyproject.toml`, tag).

## Out of scope

- Changing the alias resolution rules or the graph.
- Any `AMDTSegments` rewrite: it only needs the membership to be true again.

## Acceptance criteria

- [x] `"Station" in Station(0, 1, 1).transformer.available_frames` is true.
- [x] `AMDTSegments([{...}], reference_frame="Station")` and
      `reference_frame="SL13Center"` build and produce finite centres.
- [x] `test/geometry/test_frames.py` keeps passing (it asserts the ids).
- [x] `pytest -q` green; version 2.5.1 in both metadata sources.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs \
  /home/destrada/Geant4/DTG4Simulator/env/bin/python -m pytest -q test/geometry/test_frames.py
cd /home/destrada/DTPatternRecognition
PYTHONPATH=/home/destrada/mplDTs ./env/bin/python /tmp/frames_check2.py   # both frames OK
```

## Risks / notes

- `available_frames` is used in error messages and `__str__`; a superset makes
  those longer but correct.
- Keep it a patch release: no API change, no behaviour change for existing code.

## Progress

- 2026-11-08: found while checking the dtpr contract against 2.5.0; 2.2.0-beta
  was measured on the same script and works.
- 2026-11-08: fixed. `available_frames` is now the graph ids plus every name
  `_alias` accepts, derived from the frame basenames (0.13 ms on a CMS
  chamber, and only `AMDTSegments` asks in a loop); `__str__` untouched.
  Two tests in `test_frames.py`: the names are members, and `AMDTSegments`
  builds from `Station`, `SL13Center` and `SL1` with finite centres.
  2.5.1 in `__init__.py` and `pyproject.toml`, tag `v2.5.1`; the dtpr check
  that raised on 2.5.0 now prints all three frames.
