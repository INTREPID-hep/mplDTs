# Workflow — tickets, branches, commits, PRs

**Last updated:** 2026-11-05
**Board:** [`TICKETS.md`](TICKETS.md)
**Checkpoints:** [`PROGRESS.md`](PROGRESS.md)
**Ticket conventions:** [`tickets/README.md`](tickets/README.md)

---

## 0. Status

**Plan Rev 4 and the tickets were approved on 2026-11-06.** Phase 0 (T-001,
T-003, T-005, T-006, T-007) is in progress; no Phase 1 work starts before M0
is green.

---

## 1. GitHub flow

```
issue/ticket (proposed)
      │ maintainer approves
      ▼
ticket file (ready) ──► branch feature/T-0xx-slug ──► commits T-0xx: ...
      │                                                   │
      │                                                   ▼
      │                                            PR (review, CI)
      │                                                   │
      └────────────── done ◄── merge ◄── approval ◄──────┘
```

- `main` is the integration branch; it must always be green.
- One ticket = one branch = one PR.
- Short-lived branches; rebase or merge `main` as agreed; no force-push to
  shared branches.
- The maintainer merges; the agent does not merge its own PR.

---

## 2. Branches

| Purpose | Pattern | Example |
|---|---|---|
| Ticket work | `feature/T-0xx-<slug>` | `feature/T-001-pytest-scaffolding` |
| Design spike | `feature/T-0xx-<slug>` | `feature/T-030-custom-station` |
| Bugfix | `bugfix/<slug>` | `bugfix/sl2-frame` |
| Docs only | `cleanup/<slug>` | `cleanup/tickets-docs` |

- Branch from `main` (after T-007 reconciles the current branch).
- Keep the branch focused; if the ticket grows, split it.
- Delete the branch after merge.

---

## 3. Commits

Format:

```
T-0xx: <imperative summary>

Optional body: why, trade-offs, references.
```

Examples:

- `T-001: add pytest scaffolding`
- `T-003: compare computed cell centres with the XML oracle`
- `T-024: derive SL2 pose instead of mixing frames`

Rules:

- Small, logical commits; one concern each.
- Do not mix refactor and behaviour change in one commit.
- Reference the ticket and the design section in the body when useful.
- If a test is red, say so and why; do not hide it.
- No generated files, secrets, `env/`, `__pycache__/`.

---

## 4. Pull requests

Title: `T-0xx: <summary>`
Body: use `.github/pull_request_template.md`.

The PR must state:

- what changed and why (link the ticket and design section);
- tests run and the oracle result (if geometry changed);
- compatibility impact (constructors, `transformer`, plotting);
- performance before/after (if relevant);
- what is intentionally out of scope.

Review checklist:

- [ ] Acceptance criteria met.
- [ ] Tests green; CI green.
- [ ] Oracle still passes (or the failure is the documented `xfail`).
- [ ] No new mandatory dependency; no pyg4ometry in the core.
- [ ] Public API preserved or deprecation documented.
- [ ] `.agents/TICKETS.md`, `PROGRESS.md` updated.
- [ ] ADR added/updated for a non-obvious decision.
- [ ] Design doc updated if the model/API changed.

---

## 5. CI

Minimum (T-007):

- install package + `test` extra;
- `pytest -q` (geometry tests);
- docs build (existing Sphinx workflow or a separate job).

Geometry-specific jobs may be marked `slow` and run nightly/manually:
all-chamber oracle, full benchmark, `.tg` parity.

No CI job may require pyg4ometry until T-060 is approved.

---

## 6. Versioning and tags

- Public API stays compatible until 3.0 (ADR-010).
- Milestone tags: `geometry-refactor-M0`, `M1`, ... (annotated).
- No version bump per ticket; a release is a separate decision.
- A breaking change requires an ADR and a major version.

---

## 7. Current branch reconciliation (T-007)

The repository is on `enhancement-cacheObjects`, and the installed package
differs in frame naming. Before the first ticket:

1. Compare `main` vs `enhancement-cacheObjects`; list unique commits.
2. Decide: merge the branch into `main` (recommended), or base the refactor on
   it and merge later.
3. Tag the chosen base (`geometry-refactor-base`).
4. Add the CI workflow and PR template.
5. Record the decision in `PROGRESS.md` and, if architectural, an ADR.

Do not rewrite shared history.

---

## 8. Useful commands

```bash
cd /home/destrada/mplDTs
git switch main
git pull --ff-only
git switch -c feature/T-001-pytest-scaffolding

# ... work, test ...
git add -A
git commit -m "T-001: add pytest scaffolding"
git push -u origin feature/T-001-pytest-scaffolding

# if gh is available:
gh pr create --title "T-001: add pytest scaffolding" \
             --body-file .github/pull_request_template.md
```

After merge:

```bash
git switch main
git pull --ff-only
git branch -d feature/T-001-pytest-scaffolding
```

Update `PROGRESS.md` and the ticket status before/after the merge.

---

## 9. Blocked tickets

- Mark `blocked` in the ticket and `TICKETS.md`; add the reason and the
  unblock condition in `PROGRESS.md` §4.
- Do not silently switch to unrelated work; pick another `ready` ticket only
  if it does not depend on the blocked one.
- A design blocker needs an ADR proposal, not a workaround.
