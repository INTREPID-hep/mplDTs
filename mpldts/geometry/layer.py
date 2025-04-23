from mpldts.geometry._geometry import DTGEOMETRY
from mpldts.geometry.dt_frame import DTFrame
from mpldts.geometry.drift_cell import DriftCell


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

    def __init__(self, rawId, parent=None):
        """
        Constructor of the Layer class.

        :param rawId: Raw identifier of the layer.
        :type rawId: int
        :param parent: Parent super layer of the layer. Default is None.
        :type parent: SuperLayer, optional
        """
        self.parent = parent
        self.number = int(DTGEOMETRY.get("layerNumber", rawId=rawId))
        super().__init__(rawId=rawId)
        self._DriftCells = []

        # these attributes are used inside DriftCell class to compute the position of the cell
        # and in cell() method to check if the cell_id is valid
        self._first_cell_id, self._last_cell_id = DTGEOMETRY.get("WiresRange", rawId=rawId)

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

        for n_cell in range(self._first_cell_id, self._last_cell_id + 1):
            cell = DriftCell(number=n_cell, parent=self)
            self._add_cell(cell)


if __name__ == "__main__":
    # This is to check that nothing fails
    layer = Layer(574923776)
    print(layer)
    for cell in layer.cells:
        print("\t", cell)
