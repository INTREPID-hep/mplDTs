# `.agents` — working memory for the geometry refactor

This folder is the operational workspace for any agent continuing the mplDTs
geometry generalization. It is deliberately small, explicit and kept in the
repository so the context survives sessions, machines and people.

## Start here

1. [`AGENT.md`](AGENT.md) — the contract: mission, rules, workflow, done.
2. [`state.md`](state.md) — the current truth snapshot.
3. [`TICKETS.md`](TICKETS.md) — the board; then `tickets/` for refined work.
4. [`PROGRESS.md`](PROGRESS.md) — checkpoints and the session log.

## Files

| File | Responsibility | Update when |
|---|---|---|
| `AGENT.md` | entry point, non-negotiables, workflow, DoD | rules or mission change |
| `context.md` | why, current architecture, findings, key paths | architecture or findings change |
| `state.md` | dated snapshot of the repo, env, known bugs, last verification | every session |
| `plan.md` | phases, deliverables, exit criteria, estimates | a phase starts/ends |
| `TICKETS.md` | ticket board, milestones, unrefined backlog | a ticket changes state |
| `tickets/` | one file per refined ticket (`T-0xx`) | a ticket is refined |
| `PROGRESS.md` | checkpoints, session log, verification ledger | every session |
| `workflow.md` | branch, commit, PR, CI, release rules | the process changes |
| `conventions.md` | pose, units, naming, shapes, frames, style, tests | a convention is agreed |
| `decisions.md` | ADR log (accepted/proposed/superseded) | any non-obvious decision |
| `commands.md` | exact commands, paths, environment | tooling changes |
| `glossary.md` | domain and code vocabulary | a term is added/clarified |
| `pyg4ometry-readiness.md` | the contract a future backend must satisfy | the backend changes |
| `handoff.md` | the shortest path for the next agent | every session |
| `templates/` | ADR and task templates | rarely |
| `log/` | dated session notes | every session |

## Source-of-truth hierarchy

```
code + tests                        (what is)
.agents/state.md                    (dated snapshot of what is)
.agents/TICKETS.md + PROGRESS.md    (what is planned/done, and when)
docs/design/generalization-plan.md  (technical design / why)
.agents/decisions.md                (decisions and their consequences)
```

If they disagree: **code wins**, then update `state.md` and, if the design
changed, the design document. Do not silently reopen an accepted ADR.

## House rules

- Keep this folder in English, like the code and the design document.
- Prefer short, dated, factual entries over long prose.
- Every ticket has an id (`T-001`, `T-020`, ...); use it in branch names,
  commit messages and session logs.
- Every non-obvious design choice gets an ADR in `decisions.md` using
  `templates/adr.md`.
- **No implementation starts until the maintainer approves the tickets.**
- Do not put secrets, credentials or machine-specific absolute paths outside
  `commands.md`.
