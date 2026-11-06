# T-030 — `DetectorSpec` assemblies and custom stations

- **Status:** proposed
- **Phase:** 3
- **Epic:** E3 Assemblies and extras
- **Depends on:** T-020, T-021, T-022, T-026
- **Branch:** `feature/phase-3-assemblies`
- **PR:** —
- **Owner:** unassigned
- **Labels:** model, assemblies

## Context

`DetectorSpec` exists in `specs.py` and validates, but nothing builds it.
`build_station` accepts an optional parent and nothing else, `Station` is hardwired
to `(wheel, sector, station)` and the chamber cache is keyed by those CMS
coordinates. A custom chamber therefore cannot be built or plotted, and an
assembly of stations has no API.

## Scope

- `build_detector(spec, parent=None)` in `model.py`: the detector is the root
  node and every `DetectorSpec.stations` entry hangs under it at its own pose.
- One public path from a spec to the legacy views that does not go through the
  CMS cache, e.g. `Station.from_spec(spec)`; reuse the existing view/bind
  machinery and `FrameView` rather than a second code path.
- Custom `StationSpec` with 1 and 5 super layers in the tests, and one example
  in `docs/examples/`.
- The CMS path must not change: same constructor, same values, same cache.

## Out of scope

- JSON authoring (T-051), exporters (T-052), honeycomb (T-032), yoke (T-033).
- A new plotting class: the existing patches must accept the new stations.

## Acceptance criteria

- [ ] Two stations with different poses build into one detector; a point taken
      through `FrameGraph` matches the composed `world_pose` (0.0 cm).
- [ ] A custom 1-SL and a 5-SL station build and plot in phi and eta.
- [ ] The 250-chamber oracle and the current suite stay green.
- [ ] Station cost stays below 20 ms on a warm process.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
PYTHONPATH=/home/destrada/mplDTs pytest -q -m slow
```

## Risks / notes

- Do not duplicate the builder: an assembly is a tree with the detector at the
  root, not a second builder.
- The station cache may only serve CMS keys; custom stations are built once per
  spec and cached on the spec instance if a measurement asks for it.
