"""Legacy super-layer wrapper (T-022).

A SuperLayer is a view over its node in the station tree (T-020). The station
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
            Number of the super layer (1, 2, or 3).
        layers : list
            List of layers in the super layer.

        Others inherit from ``mpldts.geometry.DTFrame``... (e.g. id, local_center, global_center, direction, etc.)
    """

    def __init__(self, rawId=None, parent=None):
        """
        Constructor of the SuperLayer class.

        :param rawId: Raw identifier of the super layer.
        :type rawId: int
        :param parent: Parent station of the super layer. Default is None: the
            station holding the rawId is built for the standalone form.
        :type parent: Station, optional
        """
        if rawId is None:
            raise ValueError(
                "SuperLayer needs a rawId; build one from Station(wheel, sector, station)."
            )
        if parent is None:
            from mpldts.geometry.station import station_for

            parent = station_for(rawId)

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
        :raises ValueError: If the number is not between 1 and 3.
        """
        if number < 1 or number > 3:
            raise ValueError("SuperLayer number must be between 1 and 3")
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
if __name__ == "__main__":
    # This is to check that nothing fails
    super_layer = SuperLayer(rawId=589357056)
    print(super_layer)
    for layer in super_layer.layers:
        print("\t", layer)
        print(2 * "\t", layer.cell(layer._first_cell_id))
        print(2 * "\t", layer.cell(len(layer.cells) - 1))
