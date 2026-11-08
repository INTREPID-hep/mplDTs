# T-053 — Thin CLI (`convert`, `info`, `plot`)

- **Status:** done
- **Phase:** 5
- **Epic:** E5 Authoring
- **Depends on:** T-051, T-052
- **Branch:** `feature/T-053-cli`
- **PR:** — (branch `feature/T-053-cli`)
- **Completed:** 2026-11-08
- **Owner:** unassigned
- **Labels:** cli, authoring

## Context

Everything the CLI would do exists as a function: `from_json`, `build_station`,
`export_volumes`, `TgSink`, `Station.from_spec`, `DTStationPatch`. Writing a
five-line script for each conversion is the actual friction, so a thin
`argparse` entry point pays for itself.

`DTPatternRecognition` has a heavier CLI (subcommands declared in
`CLI_CONFIG`, `create_wrapper` mapping a namespace onto the function
signature). That earns its keep with ~10 subcommands and configurable analysis
functions; mplDTs has three. Do not port it.

## Scope

- `mpldts/cli.py` with `main(argv=None)` and a `mpldts` console script in
  `pyproject.toml`:
  - `mpldts info DOC` — station/detector summary (counts, bounds, materials);
  - `mpldts convert DOC OUT` — JSON -> `.tg` via `TgSink` (`--station` for a
    detector document);
  - `mpldts plot DOC -o OUT.svg` — one phi/eta figure via `DTStationPatch`.
- Errors are exit codes plus one line on stderr; no tracebacks for a bad path
  or a bad document.
- A short section in `docs/src/geometry/runtime.rst`.

## Out of scope

- YAML, config files, plugin discovery, an `events` command.
- A GUI.

## What was delivered

- `mpldts/cli.py` (170 lines): `main(argv=None)` and the three commands.
  `info` prints the document summary, `convert` writes the `.tg` through
  `TgSink`, `plot` writes a phi/eta SVG through `Station.from_spec` and
  `DTStationPatch`. `--station N` picks one station out of a detector document;
  without it `convert` exports the whole detector and `plot` needs a single
  station (it draws one chamber).
- A `mpldts` console script in `pyproject.toml`; `python -m mpldts.cli` works
  too. matplotlib is imported inside `plot` only, so the other two commands do
  not pay for it.
- `test/geometry/test_cli.py` (7 tests): the three commands, a detector
  document (whole and `--station`), and the two error paths.
- A "The command line" section in `docs/src/geometry/runtime.rst`.

## Acceptance criteria

- [x] `mpldts convert station.json out.tg` produces a file `TgSink` accepts.
- [x] `mpldts plot station.json -o out.svg` writes a non-empty SVG headless.
- [x] Bad input exits non-zero (2) with a readable one-line message.
- [x] Tests cover the three commands (`test/geometry/test_cli.py`).

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs \
  /home/destrada/Geant4/DTG4Simulator/env/bin/python -m mpldts.cli convert \
  docs/examples/testbeam_station.json /tmp/station.tg
```

## Risks / notes

- Keep it under ~120 lines; if it grows past six subcommands, lift
  `create_wrapper` from dtpr (10 lines) instead of inventing a framework.

## Progress

- 2026-11-08: reopened; was deferred in Rev 4 because JSON + builders covered
  the workflow. The maintainer asked for it (2026-11-08).
- 2026-11-08: done. `mpldts/cli.py`, the console script, 7 tests, the docs
  section; version 2.8.0.
