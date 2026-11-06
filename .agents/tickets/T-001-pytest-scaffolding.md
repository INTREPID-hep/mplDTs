# T-001 — Add pytest scaffolding

- **Status:** done
- **Phase:** 0
- **Epic:** E0 Safety net
- **Depends on:** —
- **Branch:** `feature/T-001-pytest-scaffolding`
- **PR:** —
- **Owner:** unassigned
- **Labels:** tests, infra

## Context

There is no automated test suite for geometry. The existing `test/*.py` are
visual scripts. The refactor must start from a regression net, and every later
ticket depends on being able to run `pytest`.

## Scope

- Add a `test` optional dependency in `pyproject.toml` (pytest only; no
  runtime dependency).
- Create `test/geometry/__init__.py` and a trivial test that imports
  `mpldts.geometry` and constructs one `Station`.
- Document the install/run command in `.agents/commands.md` and the README.
- Keep the test deterministic and fast (< 5 s), using the installed package or
  the checkout as documented.

## Out of scope

- The oracle harness and node snapshot (T-003) and any refactor.
- Changing library code.
- CI wiring (T-007).

## Acceptance criteria

- [x] `pytest -q` from the repo root collects `test/geometry/` and passes.
- [x] A failure in the trivial test would be visible in the exit code.
- [x] `pyproject.toml` has a `test` extra; no runtime dependency was added.
- [x] The test uses `PYTHONPATH` or an editable install consistently; the
      command is documented.

## Verification

```bash
cd /home/destrada/mplDTs
source /home/destrada/Geant4/DTG4Simulator/env/bin/activate
pip install pytest          # dev only
PYTHONPATH=/home/destrada/mplDTs pytest -q
```

## Risks / notes

- The env currently has no pytest. Installing it is a dev step, not a library
  change.
- Do not convert the visual scripts into tests in this ticket; they need
  assertions and are covered by T-003.

## Progress

- 2026-11-05: proposed, awaiting review.
- 2026-11-06: approved and started; status `doing`.
- 2026-11-06: done. pytest 9.2.0 in the env, `test` extra, `testpaths`,
  `addopts = -m 'not slow'`; `test/geometry/test_smoke.py` builds one chamber.
