from mpldts.geometry import Station
from matplotlib.transforms import Affine2D
from numpy import array, sqrt


class DTRelatedPatch:
    """
    A base class for creating patches related to the DT geometry. This class is designed to manage
    common methods and functionalities such as moving to global coordinates and inverting views.

    Attributes:
    -----------
        station : Station
            The Station object containing the geometry information.
        axes : matplotlib.axes.Axes
            The matplotlib axes to draw the patches on.
        view : str
            The view type, either "phi" or "eta".
        local : bool
            Boolean indicating whether to use local or global coordinates.
        inverted : bool
            Boolean indicating whether to invert the view. If local is False, this will not have any effect.
    """

    def __init__(
        self, station: Station, axes, collections, faceview="phi", local=True, inverted=False
    ):
        """
        Initialize a DTRelatedPatch instance.

        :param station: The Station object containing the geometry information.
        :type station: Station
        :param axes: The matplotlib axes to draw the patches on.
        :type axes: matplotlib.axes.Axes
        :param collections: matplotlib.collections.PatchCollection or list of PatchCollection objects to be drawn on the axes.
        :type collections: list
        :param faceview: The view type, either "phi" or "eta".
        :type faceview: str, optional
        :param local: Boolean indicating whether to use local or global coordinates.
        :type local: bool, optional
        :param inverted: Boolean indicating whether to invert the view. If local is False, this will not have any effect.
        :type inverted: bool, optional
        """
        self.station = station
        self.axes = axes
        self.view = faceview
        self.local = local
        self.inverted = (
            inverted if inverted and local else False
        )  # if global required (local = False), no inversion needed
        self._collections = collections

        self._draw_collections()

        self._add_collections_to_axes()

        if self.inverted:
            self.invert_view()

        if not self.local:
            self.move_to_global()

    def _draw_collections(self):
        """
        Draw the collections on the axes. This method should be implemented in subclasses.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def _add_collections_to_axes(self):
        """
        Add the collections to the axes.
        """
        for _collection in self._collections:
            self.axes.add_collection(_collection)

    def move_to_global(self):
        """
        Move the collections to the global CMS frame.
        """
        to_global_matrix = self.station.transformer.get_transformation("Station", "CMS")

        if self.view == "phi":
            affine_matrix_2d = array(
                [
                    [to_global_matrix[0, 0], to_global_matrix[0, 2], to_global_matrix[0, 3]],
                    [to_global_matrix[1, 0], to_global_matrix[1, 2], to_global_matrix[1, 3]],
                    [0, 0, 1],
                ]
            )

        elif self.view == "eta":
            affine_matrix_2d = array(
                [
                    [-to_global_matrix[2, 1], 0, to_global_matrix[2, 3]],
                    [0, -1, sqrt(to_global_matrix[0, 3] ** 2 + to_global_matrix[1, 3] ** 2)],
                    [0, 0, 1],
                ]
            )

        for _collection in self._collections:
            base_transform = _collection.get_transform()
            _collection.set_transform(Affine2D(affine_matrix_2d) + base_transform)

    def invert_view(self):
        """
        Invert the view. The inversion depends on the current view and the station's wheel and sector.
        Details about DT chamber orientations can be found `here. <https://dt-sx5.web.cern.ch/dt-sx5/run/docs/050912DT_type_naming.pdf>`_
        """
        if not self.local:
            return
        if not self.inverted:
            from_frame = "Station"
            to_frame = "StationNvPhi" if self.view == "phi" else "StationNvEta"
        else:
            from_frame = "StationNvPhi" if self.view == "phi" else "StationNvEta"
            to_frame = "Station"

        to_local_inverted_matrix = self.station.transformer.get_transformation(from_frame, to_frame)

        affine_matrix_2d = array(
            [
                [to_local_inverted_matrix[0, 0], to_local_inverted_matrix[0, 2], 0],
                [to_local_inverted_matrix[2, 0], to_local_inverted_matrix[2, 2], 0],
                [0, 0, 1],
            ]
        )

        for _collection in self._collections:
            base_transform = _collection.get_transform()
            _collection.set_transform(Affine2D(affine_matrix_2d) + base_transform)

        self.inverted = not self.inverted
