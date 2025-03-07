geometry
=========

This module provides tools to manage geometrical objects for data pattern recognition.

The CMS DTs geometry information is stored in an XML file (`DTGeometry.xml <https://github.com/DanielEstrada971102/mplDTs/blob/main/mpldts/utils/templates/DTGeometry.xml>`_). 
The ``geometry`` module includes a class to read and manage this file. By default, an instance of this class is created
when the package is imported, and the geometry information can be accessed from the variable ``DTGEOMETRY``.

Additionally, this module offers a base class for defining geometrical objects representing various
DT chamber components (e.g., :doc:`./drift_cell`, DT :doc:`./layer`, DT :doc:`./super_layer`). This base class represents a general 
cubic frame with properties such as bounds, center, id, width, height, etc. In this way, CMS DT chambers are built by nesting instances
of DTFrames (see the Submodules below). It means, a Chamber is a DTFrame child which contains SuperLayers, SuperLayers are DTFrame children which contain Layers, and so on until the DriftCells.
The following image shows the composition of a CMS DT chamber and indicates how the reference frames for each component are defined, which is important when reading the geometry information from the XML file.

.. image:: ../../_static/img/dt_chamber.png
    :width: 400
    :align: center

.. toctree::
    :maxdepth: 1
    :caption: Submodules:

    station
    super_layer
    layer
    drift_cell

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

.. code-block:: python

    dt_geometry = DTGeometry(os.path.abspath("./DTGeometry.xml"))

    # Retrieve and print global and local positions, and bounds for specific chambers
    global_pos_1 = dt_geometry.get("GlobalPosition", wh=-2, sec=1, st=1)
    local_pos_1 = dt_geometry.get("GlobalPosition", wh=-1, sec=1, st=4)
    bounds = dt_geometry.get("Bounds", wh=-1, sec=1, st=4)
    print(f"Bounds for Wh:-1, Sec:1, St:4: {bounds}")
    print(f"Global position for Wh:-2, Sec:1, St:1: {global_pos_1}")
    print(f"Local position for Wh:1, Sec:1, St:4: {local_pos_1}")

    # Iterate through all layers in a specific SuperLayer and print their attributes
    for sl in dt_geometry.root.find(".//SuperLayer[@rawId='574922752']").iter("Layer"):
        print(sl.attrib)

    # Test retrieving the total number of channels in a specific layer
    print("TEST cells")
    print(dt_geometry.root.find(".//Layer[@rawId='579380224']//Channels//total").text)

    # Test retrieving attributes of a specific SuperLayer
    print("TEST super layer")
    print(dt_geometry.get(rawId=574922752).attrib)

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
    Notice that the root atrribte of the DTGeometry class is simply an instance of the `xlm.etree.ElementTree <https://docs.python.org/3/library/xml.etree.elementtree.html>`_ class, so you can use all its methods to navigate through the XML file. 
    the only advantage of using DTGeometry is that it provides a more intuitive way to access the specific information of the CMS DT geometry through the ``get`` method.

.. tip::
    insted of create an instance of DTGeometry each time, if you will use the default geometry file, you can access the geometry information from the variable ``DTGEOMETRY``.


.. _DTFrame:

DTFrame
*******

.. autoclass:: mpldts.geometry.DTFrame
    :members:
    :special-members: __init__
    :private-members: _correct_cords
    :exclude-members: __module__, __dict__, __weakref__