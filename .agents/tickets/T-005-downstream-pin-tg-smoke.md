# T-005 — Downstream pin + `.tg` smoke test

- **Status:** done (reopened 2026-11-08; closed 2026-11-08 on 2.7.0)
- **Phase:** 0
- **Epic:** E0 Safety net
- **Depends on:** T-001
- **Branch:** `feature/T-005-tg-smoke` (DTG4Simulator)
- **PR:** — (branch `feature/T-005-tg-smoke` in `DTG4Simulator`, pushed;
  not merged into the simulator's `main`, whose tip is the old `43b1057`)
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
- 2026-11-08: closed on `v2.7.0` (see above); the smoke runs against the
  installed package, no `PYTHONPATH`.
- 2026-11-06: done. `SuperLayer` alias added per super layer
  (`super_layer.py`); DTG4Simulator `requirements.txt` pin;
  `geometry/smoke_tg.py` passes (621 placements, SL2 rotation present).

## Reopened (2026-11-08) — closed the same day on 2.7.0

The merge into `main` unblocked the migration. What was done:

- [x] `DTG4Simulator/requirements.txt` pins
      `mplDTs @ git+https://github.com/INTREPID-hep/mplDTs.git@v2.7.0` (was
      `v2.2.0-beta` on the old URL).
- [x] `geometry/generate_geometry_data.py` writes every station through
      `build_station` + `TgSink`: the XML is parsed once (`SOURCE`), one node
      tree per chamber, one export per file. The legacy `create_station_volume`,
      `create_superlayer_cells` and `create_honeycomb` are gone; the yoke stays
      (it needs boolean solids) and defines its own `RM_Yoke_Station_*`
      rotation while keeping the exporter's `Solid_Station_*` solid name.
- [x] The volume names did **not** change: the generator passes `name_of` to
      `TgSink` (T-057) and keeps `Station_W.._Sec.._St..`,
      `DriftCell_.._SL<n>_<encoding>` and `Honeycomb_W.._Sec.._St..`, because
      `StationSD`/`DriftCellSD` parse them and the copy number of a cell volume is
      decoded to (layer, wire). The ticket's original "cells become
      `DriftCell_<station>_<SL>`" would have broken every hit; ADR-025 keeps the
      legacy names until 3.0.
- [x] `geometry/smoke_tg.py` rewritten: names, 621 placements, the three cell
      volumes with their encodings, the SL2 rotation values, and copy numbers
      restarting at 1 for every cell volume.
- [x] Command recorded in `.agents/commands.md` §6.

## Parity (2026-11-08)

| Check | Result |
|---|---|
| `W0/Sec1/St1` placements, Station frame | 621, same as the reference file |
| cell volumes and encodings | `SL1_49504948`, `SL2_57585756`, `SL3_49504948`, same as the reference |
| rotations | the SL2 90-degree matrix is the same, now named `RM_W0_S1_MB1_2` |
| positions | identical to 1e-6 cm (the composition rounds at the 6th decimal) |
| the 36 station files of the previous build | 25896 cells, per-file counts identical (the +1 was the honeycomb, not enabled by default) |
| all 250 chambers | 171732 cells in 11.6 s |
| `include_honeycomb=True` | 622 placements, `Honeycomb_W0_Sec1_St1` (`G4_Al`) |
| `include_yoke=True` | `yoke.tg` with `RM_Yoke_Station_0_1_1` and the exporter's `Solid_Station_W0_Sec1_St1` |
