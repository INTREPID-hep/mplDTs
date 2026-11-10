"""Legacy super-layer wrapper.

A SuperLayer is a view over its node in the station tree. The station
graph carries every frame, so nothing is copied per object and the SL2
orientation comes from the source, not from a hand-written rotation matrix.
"""

from mpldts.geometry.dt_frame import DTFrame
from mpldts.geometry.frames import FrameView
from mpldts.geometry.layer import Layer


class SuperLayer(DTFrame):
    """
    Class representing a SuperLayer.

    Attributes
    ----------
        parent : Station
            Parent station of the super layer.
        number : int
            Number of the super layer (1, 2 and 3 for the CMS chambers).
        layers : list
            List of layers in the super layer.

        Others inherit from ``mpldts.geometry.DTFrame``... (e.g. id, local_center, global_center, direction, etc.)
    """

    def __init__(self, rawId=None, parent=None):
        """
        Constructor of the SuperLayer class.

        :param rawId: Raw identifier of the super layer.
        :type rawId: int
        :param parent: Parent station of the super layer.
        :type parent: Station
        """
        if rawId is None or parent is None:
            raise ValueError("SuperLayer needs a rawId and its station (Station.from_spec).")

        node, record = parent._legacy_part(rawId)
        self.id = int(rawId)
        self.parent = parent
        self.number = int(node.name[2:])
        self.local_center = record["local"]
        self.global_center = record["global"]
        self.bounds = record["bounds"]
        self._node = node
        self.transformer = FrameView(parent.transformer.graph, node)
        self._layers = [Layer(rawId=layer_record["raw_id"], parent=self) for layer_record in record["layers"]]

    @property
    def layers(self):
        """
        Get all the layers in the super layer.

        :return: List of layers in the super layer.
        :rtype: list of Layer objects
        """
        return self._layers

    @DTFrame.number.setter
    def number(self, number):
        """
        Set the number of the super layer.

        :param number: Number of the super layer.
        :type number: int
        :raises ValueError: If the number is not a positive int.
        """
        if number < 1:
            raise ValueError("SuperLayer number must be a positive int")
        DTFrame.number.fset(self, number)

    def layer(self, layer_number):
        """
        Get a layer by its number. If the layer does not exist, it returns None.

        :param layer_number: Number of the layer.
        :type layer_number: int
        :return: Layer with the specified number.
        :rtype: Layer
        """
        return next((l for l in self._layers if l.number == layer_number), None)

    def _legacy_part(self, raw_id):
        """(node, record) of a layer, resolved in the parent station."""
        return self.parent._legacy_part(raw_id)


# Example usage
