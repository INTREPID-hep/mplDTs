# T-057 — The `.tg` naming seam (`TgSink.name_of`)

- **Status:** done
- **Phase:** 5
- **Epic:** E5 Authoring and export
- **Depends on:** T-052
- **Branch:** `feature/T-057-tg-names`
- **PR:** — (merged into `main`, tag `v2.7.0`)
- **Completed:** 2026-11-08
- **Labels:** export, backend-seam, downstream

## Context

The names in a `.tg` file are not decoration: `DTG4Simulator` parses them.
`StationSD` reads the chamber from `Station_W<w>_Sec<s>_St<n>`; `DriftCellSD`
reads the super layer and the cells-per-layer encoding from
`DriftCell_W<w>_Sec<s>_St<n>_SL<n>_<encoding>` and maps the copy number of
that cell volume onto (layer, wire).

`TgSink` (T-052) derived its names from the node tree, so its output was
`DriftCell_<station>_<SL1>`: switching the simulator generator to the sink
(T-005) would have renamed every volume and silently broken every hit.
ADR-025 says the legacy names are API until 3.0, so the exporter has to be able
to speak the consumer's naming.

## What was delivered

- `TgSink(target, world="world", name_of=None)`: `name_of(node) -> str or
  None` overrides the base name of a node; `None` keeps the default. The
  result is sanitised like every other name. The scheme itself stays with the
  consumer: mplDTs knows nothing about CMS chamber names.
- Copy numbers restart for every volume placed in a mother (they were counted
  per mother). A `.tg` is a flat list of placements and the copy number
  identifies the copy *of that volume*, which is what the reference generator
  writes and what the cell decoder reads.
- `test/geometry/test_export.py`: a test for the hook, and the copy-number
  test rewritten to pin the new rule.
- `docs/src/geometry/runtime.rst`: the names are part of the contract with the
  reader.
- Version 2.7.0 (the default naming of an export without a hook is unchanged).

## Acceptance criteria

- [x] A consumer keeps its own volume names without patching mplDTs.
- [x] The CMS station file keeps its names, copy numbers and rotations
      (T-005 parity table).
- [x] The default naming of an export without a hook is unchanged.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_export.py
PYTHONPATH=/home/destrada/mplDTs pytest -q          # 205 passed, 2 skipped
```

## Progress

- 2026-11-08: proposed and done while migrating the simulator (T-005): the
  first `TgSink` output of `W0/Sec1/St1` renamed every cell volume, and the
  two lines of C++ that decode a hit showed why that could not ship.
- 2026-11-08 (2.9.1): the sanitiser still ate the minus of a negative wheel, so
  `Station_W-1_Sec1_St1` came out as `Station_W_1_Sec1_St1` and
  `ExtractIntAfterToken` (`include/DTSimUtils.hh`) could not read the wheel.
  Found by running one Geant4 event on the regenerated geometry: the first
  `:SOLID Solid_Station_W-1_*` the yoke referenced did not exist. The dash is
  legal in a `.tg` name and it is part of the contract, so `_clean` keeps it;
  `test_a_negative_wheel_keeps_its_minus` pins it.
