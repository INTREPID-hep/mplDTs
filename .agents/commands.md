# Commands and paths

**Last updated:** 2026-11-05
**Shell:** WSL Ubuntu 24.04, bash
**Repo:** `/home/destrada/mplDTs`

---

## 0. Status

**Plan Rev 5 approved 2026-11-06; Phases 0-3 and 5 merged into `main`
(`2eac105`, `v2.5.0`).** `pytest` is the test entry point. Next: `T-005`
(simulator), `T-006`, then the downstream contract (`T-056`, `T-040`, `T-055`).

## 0b. The downstream package (DTPatternRecognition)

```bash
cd /home/destrada/DTPatternRecognition
# check the contract against the mplDTs checkout, without touching the pin
PYTHONPATH=/home/destrada/mplDTs ./env/bin/python -c \
  "import dtpr.utils.dt_plot_functions, dtpr.utils.gui.artist_gui_manager; print('ok')"
# its own suite (needs ROOT and the test ntuples)
./env/bin/python -m pytest -q tests
```

The dtpr env has `mpldts` 2.2.0-beta installed and `pyproject.toml` pins
`v2.2.0-beta`; `PYTHONPATH=/home/destrada/mplDTs` overrides the installed copy.
T-055 moves the pin to `v2.5.1`.

---

## 1. Environment

```bash
cd /home/destrada/mplDTs
source /home/destrada/Geant4/DTG4Simulator/env/bin/activate
python --version          # 3.12.3
```

Available in that env: numpy, pandas, matplotlib, pytransform3d, mplhep.
**Not installed:** pytest, pyg4ometry. T-001 adds pytest as a test extra; do
not add pyg4ometry.

The source checkout and the installed package are different:

```bash
python -c "import mpldts; print(mpldts.__version__, mpldts.__file__)"
# 2.2.0-beta .../DTG4Simulator/env/lib/python3.12/site-packages/mpldts/__init__.py
```

To run the **source** (not the installed package):

```bash
PYTHONPATH=/home/destrada/mplDTs python ...
```

Always say which one a measurement used.

---

## 2. Prototype

```bash
cd /home/destrada/mplDTs
source /home/destrada/Geant4/DTG4Simulator/env/bin/activate

python prototype/parametric_poc.py
python prototype/parametric_poc.py --plot prototype/custom_station.png
python -m py_compile prototype/parametric_poc.py
```

Expected: all checks `0.000e+00`, 193 placements in the box station, tube
alignment `R_x(-90)`.

---

## 3. Current baseline benchmark

```bash
cd /home/destrada/Geant4/DTG4Simulator
source env/bin/activate
PYTHONPATH=/home/destrada/mplDTs python - <<'PY'
import time
from mpldts.geometry import Station

t = time.time()
st = Station(-2, 1, 2)
print("one station: %.3f s" % (time.time() - t))
print("SLs:", [s.number for s in st.super_layers])
print("frames:", sorted(st.transformer.available_frames))
PY
```

SL2 diagnosis:

```bash
cd /home/destrada/Geant4/DTG4Simulator
source env/bin/activate
PYTHONPATH=/home/destrada/mplDTs python - <<'PY'
import numpy as np
from mpldts.geometry import Station

st = Station(-2, 1, 2)
for sl in st.super_layers:
    errs = [np.linalg.norm(c.transformer.transform((0, 0, 0), "Cell", "CMS")
                           - np.array(c.global_center))
            for layer in sl.layers for c in layer.cells]
    print(sl.number, min(errs), max(errs))
PY
```

Expected: every error ~0, SL2 included (`BUG-01` was fixed in T-022).

---

## 4. XML facts

```bash
cd /home/destrada/mplDTs/mpldts/geometry
python - <<'PY'
import xml.etree.ElementTree as ET
r = ET.parse("DTGeometry_v3.xml").getroot()
from collections import Counter
print(Counter(e.tag for e in r.iter()))
print("chambers:", len(list(r.iter("Chamber"))))
PY
```

Size: ~20.8 MB. 250 chambers, 61,760 layers, 171,732 cell centres.

---

## 5. Tests

pytest lives in the `test` extra (not a runtime dependency). Run against the
**checkout**, not the installed package:

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs /home/destrada/Geant4/DTG4Simulator/env/bin/python -m pytest -q
```

- Default: six representative chambers, ~30 s; the `slow` marker is deselected
  by `addopts`.
- Full 250-chamber oracle (minutes): `pytest -q -m slow test/geometry/test_oracle.py`.
- The SL2 comparison is a plain test (`test_sl2_cell_centres`) since T-022; a
  regression fails the suite.

The XML is the reference; there is no golden JSON file (T-002 folded into
T-003). Cell centres use `2e-3` cm because the XML stores 3 decimals.

---

## 6. Downstream simulator

```bash
cd /home/destrada/Geant4/DTG4Simulator/geometry
source ../env/bin/activate
python generate_geometry_data.py
```

This uses the **installed** `mpldts`; to use the checkout, prefix
`PYTHONPATH=/home/destrada/mplDTs`. One-station smoke test (T-005):

```bash
cd /home/destrada/Geant4/DTG4Simulator/geometry
PYTHONPATH=/home/destrada/mplDTs ../env/bin/python smoke_tg.py
```

Expected: `ok: 621 placements, SL2 rotation present`. The validated `mplDTs`
revision is pinned in `/home/destrada/Geant4/DTG4Simulator/requirements.txt`.

Build/run:

```bash
cd /home/destrada/Geant4/DTG4Simulator
mkdir -p build && cd build
cmake .. && make -j"$(nproc)"
./exampleDTSim macros/batch/run.mac
```

---

## 7. Git and tickets

```bash
cd /home/destrada/mplDTs
git status --short
git log --oneline -10
git diff --stat
git branch --show-current        # enhancement-cacheObjects (before T-007)
```

After the review gate and T-007:

```bash
git switch main
git pull --ff-only
git switch -c feature/T-001-pytest-scaffolding

# work, test, then:
git add -A
git commit -m "T-001: add pytest scaffolding"
git push -u origin feature/T-001-pytest-scaffolding

# if the GitHub CLI is available:
gh pr create --title "T-001: add pytest scaffolding" \
             --body-file .github/pull_request_template.md
```

Branch naming: `feature/T-0xx-<slug>`. Commit: `T-0xx: <imperative summary>`.
One ticket = one branch = one PR. Do not commit directly to `main`; do not
commit `env/`, `__pycache__/`, `*.pyc`, generated `.tg`/GDML, or secrets.

Ticket status and progress:

```bash
# edit .agents/TICKETS.md (status), the ticket file, and .agents/PROGRESS.md
# after a session, add a row to PROGRESS.md §3
```

## 7b. GitHub CLI (optional)

```bash
gh --version
gh pr status
gh pr checks
```

If `gh` is not installed, create the PR in the browser and paste the template.

---

## 8. pyg4ometry (future, not now)

```bash
# Do not run yet; pyg4ometry is deferred (ADR-008/ADR-014).
# When Phase 6 starts:
# pip install pyg4ometry
# python -c "import pyg4ometry; print(pyg4ometry.__version__)"
```

The current compatibility seam is tested without pyg4ometry via
`VolumeSink`/`RecordingSink` in the prototype. The future module is
`mpldts/export/pyg4ometry.py`; it must import lazily.

---

## 9. Tickets and checkpoints

```bash
cd /home/destrada/mplDTs
sed -n '1,120p' .agents/TICKETS.md
ls .agents/tickets/
sed -n '1,80p' .agents/PROGRESS.md
```

Status change checklist:

1. Ticket file: `Status:` line.
2. `.agents/TICKETS.md`: board row and milestone.
3. `.agents/PROGRESS.md`: session log row and checkpoint if a gate was met.
4. Commit message includes `T-0xx`.

## 10. Path mapping (Windows ↔ WSL)

| Windows | WSL |
|---|---|
| `\\wsl.localhost\Ubuntu-24.04\home\destrada\mplDTs` | `/home/destrada/mplDTs` |
| `\\wsl.localhost\Ubuntu-24.04\home\destrada\Geant4\DTG4Simulator` | `/home/destrada/Geant4/DTG4Simulator` |

Use Linux paths in commands and docs.
