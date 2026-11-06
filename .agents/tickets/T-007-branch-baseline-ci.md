# T-007 — Branch baseline and CI

- **Status:** doing
- **Phase:** 0
- **Epic:** E0 Safety net
- **Depends on:** —
- **Branch:** `feature/T-007-branch-baseline-ci`
- **PR:** —
- **Owner:** unassigned
- **Labels:** infra, github, release

## Context

The repository is on `enhancement-cacheObjects`, with local changes and a
frame-name divergence from the installed package. Before a multi-phase
refactor, we need a clean integration branch and CI so every ticket PR is
verifiable.

## Scope

- Compare `main` and `enhancement-cacheObjects`; decide the integration base
  (recommended: reconcile into `main`, then branch tickets from `main`).
- Record the decision in `PROGRESS.md` / `decisions.md`.
- Add a GitHub Actions workflow:
  - install the package + `test` extra;
  - run `pytest -q` (geometry tests);
  - run the docs build (existing Sphinx workflow can stay separate).
- Add a branch rule / documented policy: no direct commits to `main`; one
  approval; green CI.
- Add `.github/pull_request_template.md` if not already present.

## Out of scope

- Refactoring code.
- Publishing a release or bumping the version.
- Rewriting the docs build.

## Acceptance criteria

- [x] The integration base is recorded and understandable.
- [ ] A pytest workflow exists and is green on the base branch.
- [x] The PR template links a ticket and lists tests/oracle/compatibility.
- [x] The policy is documented in `.agents/workflow.md`.
- [x] No history rewrite of a shared branch without the maintainer's approval.

## Verification

- Open a draft PR from a scratch branch and confirm the workflow runs.
- Check the PR template appears.

## Risks / notes

- Current branch may contain unmerged work; do not discard it.
- If GitHub Actions is unavailable in the environment, document the local
  equivalent and keep the workflow file for later.

## Progress

- 2026-11-05: proposed, awaiting review.
- 2026-11-06: `.github/workflows/tests.yml` added (pytest, slow deselected);
  integration base recorded as an open maintainer decision; remote green run
  still pending.
