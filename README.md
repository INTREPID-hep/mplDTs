# mplDTs

Geometry for Drift Tube detectors: plot it, transform it, export it.

*mplDTs* carries the CMS DT geometry (250 chambers read from
`DTGeometry_v3.xml`) and any DT-like detector written by hand. It reads a
detector into **specs** (frozen dataclasses, one parent-relative pose each),
builds the **node tree** of a spec, resolves **frames**, and feeds the
matplotlib patches and the `.tg` exporter for Geant4.

- Documentation and tutorial: <https://intrepid-hep.github.io/mplDTs/>
- Working on the code: [`AGENTS.md`](AGENTS.md) is the one-page map, and
  [`docs/concepts/`](docs/concepts/) explains the four layers.

## Install

```shell
pip install git+https://github.com/INTREPID-hep/mplDTs.git@v3.0.1
```

For development, clone it and take the extras:

```shell
git clone https://github.com/INTREPID-hep/mplDTs.git
cd mplDTs
pip install -e ".[test,docs]"
```

## Ten lines

```python
import matplotlib.pyplot as plt
from mpldts.geometry import Station
from mpldts.geometry.sources import CMSXMLSource
from mpldts.patches import DTStationPatch

source = CMSXMLSource()                       # the CMS XML, parsed once
spec = source.station(-2, 1, 2)               # a frozen description of one chamber
station = Station.from_spec(spec, -2, 1, 2)   # the view the patches draw

figure, axis = plt.subplots(figsize=(12, 2.6))
patch = DTStationPatch(station, axis, faceview="phi")
axis.set_title(station.id)
figure.savefig("chamber.png")
```

To colour the cells with an event, hand the patch a table keyed by
`(sl, l, w)` - the geometry is never touched:

```python
rows = [{"sl": 1, "l": 1, "w": 1, "time": 350}]
DTStationPatch(station, axis, faceview="phi", vmap="time", data=rows)
```

## Tests

```shell
pip install -e ".[test]"
pytest -q                              # the default run, under a minute
pytest -q -m slow                      # the 250-chamber oracle, minutes
```

To test a checkout without installing it, prefix `PYTHONPATH=$(pwd)`.

## Docs

```shell
pip install -e ".[docs]"
cd docs && make html                   # or: sphinx-build -b html . _build/html
```

## What is where

| Path | What |
|---|---|
| `mpldts/geometry/specs.py` | the frozen specs and `validate()` |
| `mpldts/geometry/model.py` | `build_station` / `build_detector`, the `Node` tree |
| `mpldts/geometry/frames.py` | `FrameGraph` / `FrameView`, the transforms |
| `mpldts/geometry/sources/` | `CMSXMLSource`, the only reader of the XML |
| `mpldts/geometry/{station,super_layer,layer,drift_cell}.py` | the views the patches draw |
| `mpldts/patches/` | the matplotlib patches |
| `mpldts/export/` | `TgSink`, the `.tg` writer for Geant4 |
| `test/` | one file per layer |
| `docs/` | Sphinx site: tutorial, concepts, how-to, reference, about |

## License

MIT, see [`LICENSE`](LICENSE).
