from mpldts.geometry._geometry import DTGEOMETRY, DTGeometry
from mpldts.geometry.dt_frame import DTFrame
from mpldts.geometry.drift_cell import DriftCell
from mpldts.geometry.transforms import TransformManager

class Layer(DTFrame):
    """
    Class representing a Layer.

    Attributes
    ----------
        cells : list
            List of drift cells in the layer.
        parent : SuperLayer
            Parent super layer of the layer.

        Others inherit from ``mpldts.geometry.DTFrame``... (e.g. id, local_center, global_center, direction, etc.)
    """

    def __init__(self, rawId=None, parent=None):
        """
        Constructor of the Layer class.

        :param rawId: Raw identifier of the layer.
        :type rawId: int
        :param parent: Parent super layer of the layer. Default is None.
        :type parent: SuperLayer, optional
        """
        self.id = rawId
        self.parent = parent
        if rawId is not None:
            self.number = int(DTGEOMETRY.get("layerNumber", rawId=rawId))
            self.local_center = DTGEOMETRY.get("LocalPosition", rawId=rawId)
            self.global_center = DTGEOMETRY.get("GlobalPosition", rawId=rawId)
            self.bounds = DTGEOMETRY.get("Bounds", rawId=rawId)
            # these attributes are used inside cell() method to check if the cell_id is valid
            self._first_cell_id, self._last_cell_id = DTGEOMETRY.get("WiresRange", rawId=rawId)
        else:
            self._first_cell_id = 1
            self._last_cell_id = 49

        self._setup_tranformer()
        self._DriftCells = []
        self._build_layer()

    @property
    def cells(self):
        """
        Get all the layer's cells.

        :return: List of drift cells in the layer.
        :rtype: list of DriftCell
        """
        return self._DriftCells

    @DTFrame.number.setter
    def number(self, number):
        """
        Set the number of the layer.

        :param number: Number of the layer.
        :type number: int
        :raises ValueError: If the number is not between 1 and 4.
        """
        if number < 1 or number > 4:
            raise ValueError("Layer number must be between 1 and 4")
        DTFrame.number.fset(self, number)

    def cell(self, cell_number):
        """
        Get a layer cell by its number. If the cell_number is invalid, a ValueError is raised, or if the cell is not found, None is returned.

        :param cell_number: Identifier of the cell.
        :type cell_number: int
        :return: Drift cell with the specified number.
        :rtype: DriftCell
        :raises ValueError: If the cell_number is invalid.
        """
        if cell_number < self._first_cell_id or cell_number > self._last_cell_id:
            raise ValueError(f"Invalid cell number: {cell_number}")
        return next((c for c in self._DriftCells if c.id == cell_number), None)

    def _add_cell(self, cell):
        """
        Add a new cell to the layer.

        :param cell: Drift cell to be added.
        :type cell: DriftCell
        """
        self._DriftCells.append(cell)

    def _build_layer(self):
        """
        Ensemble a DT layer.
        """
        wire_bounds = DTGEOMETRY.get("WiresSize", rawId=self.id)
        for wire in DTGEOMETRY.get("Wires", rawId=self.id).iter("Wire"):
            num, local_pos_str, global_pos_str = wire.attrib.values()
            
            cell = DriftCell(number=int(num))
            
            local_pos = DTGeometry._transform_to_pos(local_pos_str)
            global_pos = DTGeometry._transform_to_pos(global_pos_str)
            
            cell.local_center = local_pos
            cell.global_center = global_pos
            cell.bounds = wire_bounds
            cell.parent = self
            cell._setup_tranformer()

            self._add_cell(cell)


    def _setup_tranformer(self):
        """
        Set up the transformer for the layer. It defines the transformation from the local frame to the global frame.
        """
        from numpy import array

        self.transformer = TransformManager("Layer") # intial frame is the layer frame

        # Inherit transformation from the parent to the global frame
        if self.parent is not None:
            transform_matrix = self.parent.transformer.get_transformation("Station", "CMS")
            self.transformer.add("Station", "CMS", transformation_matrix=transform_matrix)
            transform_matrix = self.parent.transformer.get_transformation("SuperLayer", "Station")
            self.transformer.add("SuperLayer", "Station", transformation_matrix=transform_matrix)

            # Define the transformation from the layer to the SL frame
            _parent_center = self.parent.local_center
            _SlTL = array([self._x_local, self._y_local, self._z_local]) - array(_parent_center) # This translation leave te cords in the SL frame

            self.transformer.add("Layer", "SuperLayer", translation_vector=_SlTL) # add the transformation from layer to SL frame


if __name__ == "__main__":
    # This is to check that nothing fails
    layer = Layer(574923776)
    print(layer)
    for cell in layer.cells:
        print("\t", cell)
