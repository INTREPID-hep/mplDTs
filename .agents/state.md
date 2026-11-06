# State — dated snapshot

**Last updated:** 2026-11-06 10:30 (Europe/Madrid)
**Branch:** `feature/phase-2-runtime`
**Repo:** `/home/destrada/mplDTs`
**Plan:** `.agents/plan.md` Rev 4
**Design revision:** Rev 4 (`docs/design/generalization-plan.md`)
**Current phase:** M1 done — Phase 2 (runtime model) in progress: T-020 done

---

## 1. What exists

| Artefact | Status | Notes |
|---|---|---|
| `docs/design/generalization-plan.md` | done (Rev 4) | full design; Rev 4 only changes delivery order and scope |
| `docs/design/generalization-plan-v1.md` | **removed** | superseded; removed in Rev 4 |
| `prototype/parametric_poc.py` | done (v2) | numpy-only; box + tube stations, frame graph, backend seam |
| `prototype/parametric_poc_v1.py` | **removed** | superseded; boxes only |
| `prototype/custom_station.png` | done | box (top) and tube (bottom) stations, phi/eta |
| `.agents/` | done | this operating workspace |
| `.agents/pyg4ometry-readiness.md` | done | contract for the deferred backend |
| `.agents/TICKETS.md` + `tickets/` | done | board and refined tickets; all `proposed` |
| `.agents/plan.md` | done (Rev 4) | specs-first order, leaner scope |
| `.agents/PROGRESS.md` | done | checkpoints and session log |
| `mpldts/` library changes | Phase 0 + 1 + 2 | `super_layer.py` alias; `specs.py`, `sources/cms_xml.py` and `model.py` (`Node`, `build_station`) added; legacy runtime classes unchanged |
| pytest suite for geometry | **through Phase 2 (T-020)** | `test/geometry/`: smoke, reference, specs, source, spec oracle, nodes; 73 pass, 4 xfail, 2 skip |

The prototype verifies:

- builder vs independent 4×4 matrices: `0.0` cm;
- frame graph full path vs alias: `0.0` cm; `Cell → CMS` legacy alias: `0.0` cm;
- inverse round-trip and vector-vs-axis: `0.0`;
- virtual frame `StationNvPhi`;
- JSON round-trip (`mpldts.station/2`): `0.0` cm;
- exporter pose folding: `0.0` cm;
- `RecordingSink` receives all 193 placements (1 station + 192 cells);
- G4 alignment: box = identity, tube axis y = `R_x(-90)` (z→y);
- box cell volume 546 cm³, tube cell volume 1520.5 cm³.

There is no separate wire object: the XML `<Wire>` is the cell entry, so the
prototype has no wire fields either.

---

## 2. What does not exist yet

- `mpldts/geometry/presets/`.
- `FrameGraph`/`FrameView` in the library (only in the prototype).
- `SolidSpec` attachments (honeycomb) and `StructureSpec` (yoke) in the library.
- `mpldts/events/` (segments refactor, tracks, jets).
- A JSON loader or validation (CLI is out of scope).
- Any change to the `.tg` generator or a `TgSink`.
- pyg4ometry anywhere (intentionally).

---

## 3. Known issues to fix (do not regress)

| Id | Issue | Evidence |
|---|---|---|
| `BUG-01` | SL2 transform off by `√2·|SL_local_x|` | measured 2.4749 cm (W−2/S1/MB2), 0.7071 cm (W0/S1/MB1); `layer.py:137-143`, `drift_cell.py:87-93` |
| `BUG-02` | shared cache mutates cell data across events | `station.py:386-387`, `:288-325` |
| `BUG-03` | attribute-order-dependent XML parsing | `_geometry.py:122`, `:126`, `layer.py:101` |
| `BUG-04` | `bounds`/`width/height/length` assume a box | `dt_frame.py`; G4 generator reorders at `generate_geometry_data.py:68` |
| `BUG-05` | frame-name divergence breaks the generator | legacy `SuperLayer` alias added in Phase 0 (T-005); the generator uses it |
| `BUG-06` | version metadata drift | `pyproject.toml` 2.1.0 vs `__version__` 2.2.0-beta |

`BUG-01` is expected to fail the transform invariant test until Phase 2
(T-022). Mark it `xfail(strict=True)` with a comment referencing this id,
never delete the test.

---

## 4. Environment and versions

| Item | Value |
|---|---|
| OS / shell | WSL Ubuntu 24.04, bash |
| Python | 3.12.3 |
| Env used for runs | `/home/destrada/Geant4/DTG4Simulator/env` |
| Installed `mpldts` | 2.2.0-beta in that env (`site-packages`); no XML indexes |
| Source checkout | branch `enhancement-cacheObjects`, package `__version__` 2.2.0-beta; indexed XML |
| `pyproject.toml` version | 2.1.0 (drift) |
| pyg4ometry | **not installed**; deferred |
| pytest | 9.2.0 in the env; `test` extra in `pyproject.toml` |
| Dependencies available | numpy, pandas, matplotlib, pytransform3d, mplhep |

The installed package and the checkout are **not identical**. State which one
you used in any measurement.

---

## 5. Measured baseline (2026-11-06)

| Measurement | Checkout | Installed 2.2.0-beta |
|---|---|---|
| geometry import + XML parse/index | ~3.4 s | not measured |
| `Station(-2,1,2)` | 1.00 s | 1.25 s |
| `Station(2,14,4)` | 0.71 s | 2.26 s |
| `Station(0,1,1)` | 0.87 s | 1.66 s |
| SL2 error | 2.4749 cm (W−2/S1/MB2), 0.7071 cm (W0/S1/MB1) | same |
| XML | 20.8 MB, 250 chambers, 61,760 layers, 171,732 cell centres | — |
| CMS stagger | L1 49 @ x=−102.4; L2 50 @ −104.5; L3 49 @ −102.4; L4 48, first id 2 @ −100.3; pitch 4.2 cm | — |
| `build_station` (spec -> node tree) | 1.87 s for 250 stations = **7.46 ms/station** | — |

The old 2.3–4.1 s/station, 10–17 min for all 250, and the 3.75 s/2.64 s
profile are retired: they belong to the pre-index code.

Target after Phase 2: **< 20 ms per station** (already met by the builder).

---

## 6. Last verification

- `python prototype/parametric_poc.py` after removing the wire object → all
  checks pass, 0.0 errors, 193 placements.
- `python -m py_compile prototype/parametric_poc.py` → OK.
- Station timing + SL2 check on the checkout (2026-11-06): see §5.
- `pytest -q` on the checkout: 73 passed, 4 xfailed (SL2 `BUG-01`), 2 skipped,
  12.5 s.
- Builder oracle (`-m slow`): all 250 chambers through `build_station`, green
  at `2e-3` cm, 4.9 s.
- Legacy runtime oracle (`-m slow`): 250 chambers, only SL2 disagrees
  (`BUG-01`); the spec and builder paths match the XML.
- `smoke_tg.py` on the checkout: 621 placements, SL2 rotation present.
- `bench_station.py`: 0.65 / 0.46 / 0.57 s for the three stations.

---

## 7. Immediate next actions

Plan Rev 4 and `TICKETS.md` were approved on 2026-11-06. M0 and M1 are
done; Phase 2 is in progress on `feature/phase-2-runtime`:

1. `T-021` — `FrameGraph`/`FrameView`, scoped aliases, virtual frames.
2. `T-022` — legacy constructors delegate; `BUG-01` fixed; plotting works.
3. `T-023` — immutable geometry + per-event overlay.
4. `T-024` — performance pass, `DTGEOMETRY` shim, no XML in the model.
5. `T-025` — triage the visual scripts in `test/`.

Do not start Phase 3 before M2 is green. Do not merge the branch into
`main` until the maintainer approves it.

---

## 8. Resolved decisions

- **Physical volumes:** station, cells, honeycomb, yoke. SL/layer are grouping
  frames. There is no separate wire object. (ADR-011, ADR-019)
- **Shapes:** Box now; the `Shape` protocol stays generic; Tube is cheap.
  (ADR-013)
- **Wire:** the XML `<Wire>` is the cell entry; no separate object, radius or
  material. (ADR-019)
- **pyg4ometry:** optional extra `mplDTs[g4]`, deferred. (ADR-014)
- **Output:** `.tg` first, GDML later via the same `VolumeSink`. (ADR-015)
- **Events:** a separate annotation layer; optional Phase 4. (ADR-016)
- **Honeycomb/yoke:** station attachment / detector structure data; CSG is a
  backend concern. (ADR-017)
- **Plan Rev 4:** specs-first, `VolumeSink` at the first exporter, CLI/YAML
  out, events optional. (ADR-018)

**Open:** none blocking the plan. Compatibility horizon 3.0, plotting
orientation-based, event scope Segment/Track/Jet, yoke in simulator until
Phase 6.

---

## 9. Note on the prototype

The prototype (`prototype/parametric_poc.py`) now carries no `Wire` object:
the XML `<Wire>` is the cell entry, so a cell is the only object needed.
