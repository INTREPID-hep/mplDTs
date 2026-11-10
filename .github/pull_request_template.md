<!--
PR title: <area>: <imperative summary>   (for example: patches: keep the sign in the volume name)
Say what a user gets, and link the docs page or issue where the change is argued.
-->

## What and why

<!-- One or two paragraphs. What problem does this solve? -->

## Scope

<!-- What is included. -->

## Out of scope

<!-- What is deliberately not included. -->

## Tests

- [ ] `pytest -q` (name the new or changed tests)
- [ ] 250-chamber oracle: <!-- pytest -q -m slow, or: not applicable -->
- [ ] Docs build clean: <!-- cd docs && sphinx-build -b html . _build/html -->

## Compatibility

- [ ] Public API unchanged, or the change is in `docs/about/changelog.rst`
- [ ] No new mandatory dependency
- [ ] `.tg` format and volume names unchanged (otherwise say why, they are a contract)

## Checklist

- [ ] The specs stay data, and no per-event value reaches the geometry
- [ ] A decision is recorded in `docs/about/decisions.rst` if it is not obvious
- [ ] Changelog entry for a user-visible change
- [ ] No generated or secret files committed

## Reviewer notes

<!-- Anything the maintainer should look at first: risks, open questions. -->
