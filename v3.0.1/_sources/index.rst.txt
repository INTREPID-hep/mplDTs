mplDTs
======
Document version: |release|

*mplDTs* turns the geometry of a Drift Tube detector into numbers you can plot,
transform and export. It carries the CMS DT geometry - 250 chambers read from
`DTGeometry_v3.xml` - and it accepts any DT-like detector written by hand.

It does four things and nothing else:

- reads a chamber into **specs**: frozen dataclasses with a parent-relative pose each;
- builds the **node tree** of that spec: one node per station, super layer, layer, cell;
- resolves **frames**, so a point moves between a cell and CMS in one call;
- feeds the **plotting patches** and the **`.tg` exporter** for Geant4.

Install
=======

.. code-block:: bash

   pip install git+https://github.com/INTREPID-hep/mplDTs.git@v3.0.1

For development, clone the repository and use the `test` and `docs` extras:

.. code-block:: bash

   git clone https://github.com/INTREPID-hep/mplDTs.git
   cd mplDTs
   pip install -e ".[test,docs]"

Ten lines
=========

.. code-block:: python

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

To colour the cells with an event, hand the patch a table keyed by
`(sl, l, w)`; the geometry is not touched:

.. code-block:: python

   rows = [{"sl": 1, "l": 1, "w": 1, "time": 350}]
   DTStationPatch(station, axis, faceview="phi", vmap="time", data=rows)

Where to go
===========

- **New to 3.0?** the three tutorial notebooks go from a CMS chamber to
  per-event data and to a detector of your own.
- **Changing the library?** :doc:`concepts/model` explains the four layers, and
  `AGENTS.md` in the repository is the one-page map an agent or a new
  maintainer reads first.
- **Exporting for Geant4?** :doc:`howto/geant4`.

.. toctree::
   :maxdepth: 2
   :caption: Tutorial

   tutorial/01-geometry-quickstart
   tutorial/02-event-data
   tutorial/03-own-detector

.. toctree::
   :maxdepth: 2
   :caption: Concepts

   concepts/model
   concepts/frames
   concepts/naming
   concepts/events

.. toctree::
   :maxdepth: 2
   :caption: How-to

   howto/cms
   howto/custom_detector
   howto/geant4
   howto/downstream
   howto/agents

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/geometry/main
   reference/patches/main

.. toctree::
   :maxdepth: 1
   :caption: About

   about/changelog
   about/decisions
   about/roadmap
   about/contributing
