<!--
PR title: T-0xx: <imperative summary>
Link the ticket file in .agents/tickets/ and the design section it implements.
-->

## Ticket

- Ticket: `T-0xx` — <title>
- Ticket file: `.agents/tickets/T-0xx-<slug>.md`
- Design section: `docs/design/generalization-plan.md` §<n>

## What and why

<!-- One or two paragraphs. What problem does this solve? -->

## Scope

<!-- What is included. -->

## Out of scope

<!-- What is deliberately not included. -->

## Tests

- [ ] `pytest -q` (list the new/changed tests)
- [ ] CMS oracle: <!-- pass / documented xfail / not applicable -->
- [ ] Prototype/benchmark: <!-- command and result -->
- [ ] `.tg` smoke/parity: <!-- pass / not applicable -->

## Compatibility

- [ ] `Station(wheel, sector, station)` and `rawId` constructors still work.
- [ ] `obj.transformer` / `get_transformation` / `transform` still work.
- [ ] Plotting API unchanged (or deprecation documented).
- [ ] No new mandatory dependency; pyg4ometry remains optional/absent.
- [ ] No separate wire object; SL/layer remain grouping; yoke still data-only.

## Performance (if relevant)

<!-- Before/after station build or full geometry. -->

## Checklist

- [ ] Acceptance criteria in the ticket are met.
- [ ] `.agents/TICKETS.md` and `.agents/PROGRESS.md` updated.
- [ ] ADR added/updated for a non-obvious decision.
- [ ] Design doc updated if the model/API changed.
- [ ] No generated/secret files committed.

## Reviewer notes

<!-- Anything the maintainer should look at first, risks, open questions. -->
