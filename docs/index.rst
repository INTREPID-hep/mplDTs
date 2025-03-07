.. DT Pattern Recognition documentation master file, created by
   sphinx-quickstart on Thu Nov 28 01:21:14 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

mplDTs
======
This package provides a set of base tools for implementing pattern recognition plots using matplotlib
patches methodology, and taking into account the geometrical features of the CMS DT system.

Installation
------------

First, download the source files or clone the repository:

.. code-block:: bash

   git clone https://github.com/DanielEstrada971102/mplDTs.git
   cd mplDTs

You can then install the package with pip by running:

.. code-block:: bash

   pip install .

To check if the package was installed successfully, run:

.. code-block:: bash

   pip show mpldts

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   src/geometry/main
   src/patches/main