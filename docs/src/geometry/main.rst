geometry
=========

This module provides tools to manage geometrical objects in the context of CMS DT detectors.

The CMS DTs geometry information is stored in an XML file (:download:`DTGeometry.xml <../../_static/DTGeometry_v2.xml>`). 
The ``geometry`` module includes a class to read and manage this file (`DTGeometry`_).

By default, an instance of this class is created when the package is imported, and the geometry information
can be accessed through the ``DTGEOMETRY`` variable.

Additionally, this module offers a base class for defining geometrical objects representing various
DT chamber components (e.g., :doc:`./drift_cell`, DT :doc:`./layer`, DT :doc:`./super_layer`). This base class represents a general 
cubic frame with properties such as bounds, center, id, width, height, etc. In this way, CMS DT chambers are built by nesting instances
of DTFrames (see the `geometry-submodules`_ below). In other words, a Chamber is a DTFrame child
which contains SuperLayers; SuperLayers are DTFrame children that contain Layers; Layers are DTFrame
children that contain DriftCells. The following image shows the composition of a CMS DT chamber and 
indicates how the reference frames for each component are defined, which is important when reading the
geometry information from the XML file because it will be gotten in those frames.


.. image:: ../../_static/img/dt_chamber.png
    :width: 400
    :align: center

.. toctree::
    :maxdepth: 1
    :caption: Submodules
    :name: geometry-submodules

    station
    super_layer
    layer
    drift_cell

.. warning::
    Starting from version 1.1.0, the XML geometry file includes the local and global positions of each Drift Cell. 
    Consequently, the :doc:`./drift_cell` module was updated to directly read these properties from the file. 
    While this enhancement simplifies data access, it significantly increases the creation time of a :doc:`./station` 
    object. To mitigate this, parallelization of the process is strongly recommended.

Classes
-------
- :ref:`DTGeometry`
- :ref:`DTFrame`

.. _DTGeometry:

DTGeometry
**********

.. autoclass:: mpldts.geometry.DTGeometry
    :members: get

The following example shows how to access the CMS DT geometry information.

.. literalinclude:: ../../../mpldts/geometry/_geometry.py
    :language: python
    :dedent:
    :lines: 100-117

.. rubric:: Output

.. code-block:: text

    Bounds for Wh:-1, Sec:1, St:4: (416.339996, 32.5999985, 251.100006)
    Global position for Wh:-2, Sec:1, St:1: (431.175, 39.12, -533.35)
    Local position for Wh:1, Sec:1, St:4: (720.2, -94.895, -267.75)
    {'rawId': '574923776', 'layerNumber': '1'}
    {'rawId': '574924800', 'layerNumber': '2'}
    {'rawId': '574925824', 'layerNumber': '3'}
    {'rawId': '574926848', 'layerNumber': '4'}
    TEST cells
    59
    TEST super layer
    {'rawId': '574922752', 'superLayerNumber': '1'}

.. note::
    Notice that the root attribute of the DTGeometry class is simply an instance of the `xlm.etree.ElementTree <https://docs.python.org/3/library/xml.etree.elementtree.html>`_
    class, so you can use all its methods to navigate through the XML file. The only advantage of using
    DTGeometry is that it provides a more intuitive way to access the specific information of the CMS DT
    geometry through the ``get`` method.

.. tip::
    instead of creating an instance of DTGeometry each time, if you will use the default geometry file,
    you can access the geometry information from the variable ``DTGEOMETRY``.


.. _DTFrame:

DTFrame
*******

.. autoclass:: mpldts.geometry.DTFrame
    :member-order: bysource
    :members:
    :special-members: __init__

Other utils
-----------
- :ref:`Transforms`


.. _Transforms:

Transforms
***************
.. automodule:: mpldts.geometry.transforms
    :members:
