patches
=========

The ``patches`` module provides a set of customized classes designed to work seamlessly with matplotlib
for visualizing CMS DT data. These classes enable the creation of detailed and flexible plots representing
various DT objects, such as chambers and segments like trigger primitives. 

The foundation of this module is the :doc:`DTRelatedPatch <dt_patch_base>` base class, which facilitates the management of patches 
for different DT objects. For example, the :doc:`DTStationPatch <dt_station_patch>` class is used to create DT chambers patches, including their superlayers and cells,
in both local and global coordinate systems. Future extensions will include support for visualizing DT Level 1 AM (Analytical Method) Trigger Primitives.

.. toctree::
    :maxdepth: 1
    :caption: Classes:

    dt_patch_base
    dt_station_patch