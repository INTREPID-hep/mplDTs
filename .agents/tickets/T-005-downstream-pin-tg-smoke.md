# T-005 — Downstream pin + `.tg` smoke test

- **Status:** done
- **Phase:** 0
- **Epic:** E0 Safety net
- **Depends on:** T-001
- **Branch:** `feature/T-005-downstream-pin-tg-smoke`
- **PR:** —
- **Owner:** unassigned
- **Labels:** downstream, compatibility

## Context

`DTG4Simulator` currently installs `mplDTs` from a moving source, and the
checked-out branch renames the super-layer frame from `"SuperLayer"` to
`"SL{n}"`. The generator asks for `"SuperLayer"`, so installing the branch
breaks every SL2 station. There is no smoke test.

## Scope

- Pin the `mplDTs` version/commit used by `DTG4Simulator` (requirements or
  install script) to a known good revision.
- Add the `"SuperLayer"` alias (or update the generator to `"SL{n}"`; prefer
  the alias for compatibility).
- Add a smoke test/script that generates one station `.tg` and asserts:
  - the file is non-empty;
  - it contains one `:VOLU` for the cell volume and the expected number of
    `:PLACE` lines;
  - the SL2 rotation matrix is present.
- Document the command in `.agents/commands.md`.

## Out of scope

- Generating all 250 stations.
- Refactoring the generator (Phase 5/T-052).
- Changing the geometry semantics.

## Acceptance criteria

- [x] The downstream environment resolves a fixed `mplDTs` revision.
- [x] `"SuperLayer"` resolves (alias) or the generator uses the new name.
- [x] One station `.tg` is generated and asserted.
- [x] The smoke test is runnable from a single documented command.
- [x] The check does not depend on the full 250-chamber build.

## Verification

```bash
cd /home/destrada/Geant4/DTG4Simulator/geometry
source ../env/bin/activate
PYTHONPATH=/home/destrada/mplDTs python generate_geometry_data.py
python - <<'PY'
from pathlib import Path
p = Path("stations/station_W0_Sec1_St1.tg")
text = p.read_text()
assert ":VOLU" in text and ":PLACE" in text
print("ok", p.stat().st_size, "bytes")
PY
```

## Risks / notes

- The current generator builds each station 2–3×; keep the smoke test to one
  station until the model is faster.
- Do not switch `DTG4Simulator` to the new spec path in this ticket.

## Progress

- 2026-11-05: proposed, awaiting review.
- 2026-11-06: done. `SuperLayer` alias added per super layer
  (`super_layer.py`); DTG4Simulator `requirements.txt` pin;
  `geometry/smoke_tg.py` passes (621 placements, SL2 rotation present).
