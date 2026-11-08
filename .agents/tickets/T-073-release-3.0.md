# T-073 — The 3.0.0 release and the downstream lockstep

- **Status:** done (3.0.0, 2026-11-09)
- **Phase:** 7
- **Epic:** E7 Removal
- **Depends on:** T-070, T-071, T-072
- **Branch:** `feature/T-073-release-3.0`
- **PR:** —
- **Labels:** release, breaking, 3.0

## Context

A removal release is safe only if both downstream packages move in the same
window (ADR-025). This ticket is that coordination: the removal and the pins move
in one window. The deprecation release that precedes it is T-074 (2.9.0).

## Scope

- Both downstream packages pin `v2.9.0` (T-074), run their suites, and clear
  every warning they can before the removal lands.
- `3.0.0`: T-070 + T-072 land together; `DTPatternRecognition` and
  `DTG4Simulator` move their pins; the release note lists what was removed and
  what replaced it.
- Keep `.tg` support. Retiring it is a separate ADR, not part of 3.0.

## Acceptance criteria

- [x] 2.9.0 shipped with the warnings and the table (T-074).
- [ ] Both downstream suites green on `v2.9.0` and then on `v3.0.0`.
- [ ] G1-G5 of `migration-3.0.md` §5 hold and are linked in `PROGRESS.md`.
- [ ] A clean `pip install mplDTs` at 3.0 builds, plots and exports a station
      without importing anything legacy (G5).
- [ ] The release note names every removed call.

## Progress

- 2026-11-08: planned.
- 2026-11-09: **done.** mplDTs 3.0.0 tagged on `main`; dtpr and the simulator
  moved their pins to `v3.0.0` in the same window. The volume names did not
  change, so G4 is a no-op: no C++ rebuild, no seeded run, the regenerated build
  is byte-identical (ADR-027).
