DTRelatedPatch
==============

The ``DTRelatedPatch`` class serves as the foundational base for all DT-related patches. It provides a
unified interface for applying ``Affine2D`` transformations to matplotlib patches that represent various
DT objects. These transformations are based on the geometry of the DT Station where the object resides.

This class was designed to ensure that all DT-related objects drawn as matplotlib patches share consistent
``Affine2D`` transformations, aligning them with the DT Station's geometry. By using this common base class,
transformations are applied uniformly across all patches. The figure below illustrates the transformations
from the Local Frame to the Global CMS Frame:

.. image:: ../../_static/img/DTRelatedPatchsTransformations.png
    :class: image-class
    :width: 800px
    :align: center

It is important to note that the Station's geometry information is essential, as the orientation of the Local Frame varies across different stations.

.. autoclass:: mpldts.patches.dt_patch_base.DTRelatedPatch
    :members:
    :special-members: __init__
    :private-members: _draw_collections, _add_collections_to_axes
