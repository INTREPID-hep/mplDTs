# Base Tools for Pattern visualization in CMS DTs

This package provides a set of base tools for implementing pattern recognition plots using matplotlib
patches methodology, and taking into account the geometrical features of the CMS DT system.

If you are a developer please start with reading the [Contributor][contributing]'s  and [Developers][developers]  guides to be updated...

## Installation

You can clone the repo and install or use directly pip:

```shell
git clone https://github.com/INTREPID-hep/mplDTs.git
cd mplDTs
git checkout <tag version> # Opcional step: e.g. git checkout v1.0.0
pip install .
# To check if the package was installed successfully...
pip show mpldts

```

```shell
pip install git+https://github.com/INTREPID-hep/mplDTs.git@<tag version> # e.g. v1.0.0
# To check if the package was installed successfully...
pip show mplDTs
```


## Tests

```shell
pip install -e ".[test]"
pytest -q
```

The default run covers six representative chambers (`15 s). The full
250-chamber geometry oracle is behind the `slow` marker and takes minutes:

```shell
pytest -q -m slow test/geometry/test_oracle.py
```

To test a checkout without installing it, prefix `PYTHONPATH=$(pwd)`.

## Usage

Visit de documentation on [mplDTs documentation](https://intrepid-hep.github.io/mplDTs/).

## Geometry refactor (Phase 0)

The geometry layer is being generalized into a declarative, XML-free DT model
(boxes now, generic shapes later; segments/tracks/jets as a separate event
layer). Phase 0 (safety net) is in progress: regression tests, the CMS oracle
harness, a benchmark and CI.

- Start at [`.agents/AGENT.md`](.agents/AGENT.md).
- Ticket board: [`.agents/TICKETS.md`](.agents/TICKETS.md).
- Design: [`docs/design/generalization-plan.md`](docs/design/generalization-plan.md).
- Prototype: [`prototype/parametric_poc.py`](prototype/parametric_poc.py).

Phase 1 (specs + CMS source) starts only after M0 is green.

[contributing]: CONTRIBUTING.md
[developers]: DEVELOPERS.md