from mpldts.geometry._geometry import DTGEOMETRY
from mpldts.geometry.dt_frame import DTFrame
from mpldts.geometry.layer import Layer
from mpldts.geometry.transforms import TransformManager


class SuperLayer(DTFrame):
    """
    Class representing a SuperLayer.

    Attributes
    ----------
        layers : list
            List of layers in the super layer.
        parent : Station
            Parent station of the super layer.

        Others inherit from ``mpldts.geometry.DTFrame``... (e.g. id, local_center, global_center, direction, etc.)
    """

    def __init__(self, rawId=None, parent=None):
        """
        Constructor of the SuperLayer class.

        :param rawId: Raw identifier of the super layer.
        :type rawId: int
        :param parent: Parent station of the super layer. Default is None.
        :type parent: Station, optional
        """
        self.id = rawId
        self.parent = parent
        if rawId is not None:
            self.number = int(DTGEOMETRY.get("superLayerNumber", rawId=rawId))
            self.local_center = DTGEOMETRY.get("LocalPosition", rawId=rawId)
            self.global_center = DTGEOMETRY.get("GlobalPosition", rawId=rawId)
            self.bounds = DTGEOMETRY.get("Bounds", rawId=rawId)
        self._setup_tranformer()
        self._layers = []
        self._build_super_layer()

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

    def _add_layer(self, layer):
        """
        Add a new layer to the super layer.

        :param layer: Layer to be added.
        :type layer: Layer
        """
        self._layers.append(layer)

    def _build_super_layer(self):
        """
        Build up the super layer. It creates the layers contained in the super layer.
        """
        for layer in DTGEOMETRY.get(rawId=self.id).iter("Layer"):
            self._add_layer(Layer(layer.get("rawId"), parent=self))

    def _setup_tranformer(self):
        """
        Set up the transformer for the super layer. It defines the transformation from the local frame to the global frame.
        """
        from numpy import array

        self.transformer = TransformManager("SuperLayer")  # intial frame is the SL frame
        # Inherit transformation from the parent to the global frame
        if self.parent is not None:
            transform_matrix = self.parent.transformer.get_transformation("Station", "CMS")
            self.transformer.add("Station", "CMS", transformation_matrix=transform_matrix)

        # Define the transformation from Super layer frame to Station frame
        if self.number == 2:
            StezSl = [0, 0, 1] # same as the z axis of the Station frame
            SteySl = [1, 0, 0] # in SL2 y dir is x dir in Station frame
            StexSl = [0, -1, 0] # in SL2 x dir is -y dir in Station frame
            _RStSl = array([StexSl, SteySl, StezSl]).T # rotation matrix from SL to Station frame
        else:
            _RStSl =  None # no rotation needed, Sl1 and SL3 are aligned with the Station frame

        _TStSl = [self._x_local, self._y_local, self._z_local] # translation 

        self.transformer.add("SuperLayer", "Station", rotation_matrix=_RStSl, translation_vector=_TStSl)

# Example usage
if __name__ == "__main__":
    # This is to check that nothing fails
    super_layer = SuperLayer(rawId=589357056)
    print(super_layer)
    for layer in super_layer.layers:
        print("\t", layer)
        for cell in layer.cells:
            print(2 * "\t", cell)
