# Tickets — how to write and use them

**Last updated:** 2026-11-06
**Index/board:** [`../TICKETS.md`](../TICKETS.md)
**Template:** [`../templates/task.md`](../templates/task.md)
**Workflow:** [`../workflow.md`](../workflow.md)

---

## 1. When to create a ticket file

Create a file only when the ticket is about to be reviewed or worked. Future
work stays as a one-line row in `TICKETS.md` §6. This keeps the review queue
small and the board honest.

## 2. Naming

`T-0xx-<short-slug>.md`, e.g. `T-001-pytest-scaffolding.md`.

- `T-001…T-009`: Phase 0 (T-004, T-008, T-009 retired).
- `T-010…T-019`: Phase 1 (T-010 rewritten as specs; T-011/T-012 source/oracle).
- `T-020…T-029`: Phase 2.
- `T-030…T-039`: Phase 3.
- `T-040…T-049`: Phase 4 (optional).
- `T-050…T-059`: Phase 5 (T-053 deferred).
- `T-060…`: Phase 6 (future).
- `D-0xx`: planning artefacts (not implementation).

Never reuse an id. Split as `T-0xxa` / `T-0xxb`. Retired ids stay retired.

## 3. Required sections

Every ticket file has:

1. Title `# T-0xx — ...`
2. Metadata block: status, phase, epic, depends, branch, PR, owner, labels.
3. **Context** — why, with measured facts.
4. **Scope** / **Out of scope** — explicit boundaries.
5. **Acceptance criteria** — observable, testable, not activities.
6. **Verification** — exact commands.
7. **Risks / notes**.
8. **Progress** — dated status notes.

## 4. Status transitions

```
proposed -> ready -> doing -> review -> done
                    |          |
                    +-> blocked+-> (back to doing)
deferred / retired (terminal until an ADR or a decision reopens it)
```

- `proposed`: written, awaiting maintainer review.
- `ready`: approved; branch may be created.
- `doing`: branch exists; one ticket at a time.
- `review`: PR open; CI green.
- `done`: merged; acceptance boxes checked; board updated.
- `blocked`: reason in the file and `PROGRESS.md`; unblock condition stated.
- `retired`: folded into another ticket; do not implement.

Update **both** the ticket file and `TICKETS.md` when the status changes.

## 5. Branch / commit / PR mapping

- Branch: `feature/T-0xx-<slug>` from `main`.
- Commits: `T-0xx: <imperative summary>`.
- PR title: `T-0xx: <summary>`; body follows the PR template; link the ticket
  file.
- One ticket per PR. If the work grows, split the ticket rather than the PR.

## 6. Definition of ready

- [ ] Scope and out-of-scope are explicit.
- [ ] Acceptance criteria are testable.
- [ ] Dependencies are satisfied or scheduled.
- [ ] The ticket does not require a pyg4ometry dependency.
- [ ] The design doc section it implements is linked.

## 7. Definition of done

- [ ] All acceptance boxes checked.
- [ ] Tests pass (and the oracle for geometry changes).
- [ ] PR reviewed and merged.
- [ ] `TICKETS.md` and `PROGRESS.md` updated.
- [ ] Any ADR updated/created.
- [ ] The design doc updated if the model/API changed.

## 8. Reviews

The maintainer reviews the ticket before `ready` and the PR before `done`.
Comments go in the ticket file's **Progress** section or the PR; decisions go
to `decisions.md` as an ADR.
