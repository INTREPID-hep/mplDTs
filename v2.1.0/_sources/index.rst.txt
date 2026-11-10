mplDTs
======
Document version: |release|

This package provides a set of base tools to produce CMS DT chambers plots using matplotlib patches, 
and taking into account the geometrical features of the CMS DT system.

Installation
============

You can clone the repository, or install via pip:

1. **Cloning and installing the package**:

   .. code-block:: bash

      git clone https://github.com/DanielEstrada971102/mplDTs.git
      cd mplDTs
      git checkout <tag version> # Opcional step: e.g. git checkout v1.0.0
      pip install .
      # To check if the package was installed successfully...
      pip show mpldts

2. **Installing via pip**:

   .. code-block:: bash

      pip install git+https://github.com/DanielEstrada971102/mplDTs.git@<tag version> # e.g. v1.0.0
      # To check if the package was installed successfully...
      pip show mplDTs

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   src/geometry/main
   src/patches/main