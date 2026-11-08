# T-054 — Docs, tutorial and the 2.5 release note

- **Status:** done
- **Phase:** 5
- **Epic:** E5 Authoring and export
- **Depends on:** T-050, T-051, T-052 (done)
- **Branch:** `feature/phase-5-authoring`
- **PR:** — (branch pushed; the maintainer merges)
- **Owner:** —
- **Labels:** docs, release
- **Completed:** 2026-11-08

## Context

An authoring path that is only in the tests is not delivered: a user has to be
able to read how to write a detector down, load it, plot it and hand it to
Geant4, and has to know what changed since 2.2.0-beta.

## What was delivered

- `docs/src/geometry/runtime.rst` gains two sections: "Authoring: short
  constructors and JSON" (the builders, the four `serialize` functions, a JSON
  example and what the reader rejects) and "Exporting to Geant4 (.tg)" (the
  sink seam, the placement walk, `TgSink`, and what the file does *not*
  contain), plus a "Migrating from 2.2" section.
- `docs/examples/export_tg.py`: the whole path in one runnable example
  (builders -> JSON -> `from_json` -> `build_station` -> plot -> `.tg`).
  It runs headless in `test/geometry/test_examples.py`, so the tutorial cannot
  rot.
- `mpldts/__init__.py` and `pyproject.toml` at 2.5.0; `docs/conf.py` reads
  the package version, so the docs follow.

## Acceptance criteria

- [x] The docs build warning-free with the new sections.
- [x] The tutorial example runs in the suite (8 examples pass).
- [x] The version is 2.5.0 in one place per artefact and the docs read it.
- [x] The migration note lists the deliberate behaviour changes.

## Verification

```bash
cd /home/destrada/mplDTs/docs
PYTHONPATH="/home/destrada/mplDTs:/home/destrada/Geant4/DTG4Simulator/env/lib/python3.12/site-packages" \
  sphinx-build -b html . /tmp/docs_html
cd ..
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_examples.py
```

## Risks / notes

- The tutorial writes three files into the current directory; the example test
  runs it in a temporary directory, and the docs do not embed those files.
