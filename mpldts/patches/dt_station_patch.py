from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from mpldts.geometry import Station, DriftCell, SuperLayer
from mpldts.patches.dt_patch_base import DTRelatedPatch


class DTStationPatch(DTRelatedPatch):
    """
    A class to visualize a 2D representation of a DT Station data in matplotlib context.

    Attributes:
    -----------
        bounds_collection : matplotlib.collections.PatchCollection
            A collection of patches representing the bounds of the station and its superlayers.

        cells_collection : matplotlib.collections.PatchCollection
            A collection of patches representing each DT cell, with optional colormap based on time information.
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
        vmap : str
            The variable to map to the colormap.

    .. important::

        Be aware that this is not a child class of ``matplotlib.patches.Patch``. Instead, it creates a couple of
        ``matplotlib.collections.PatchCollection`` objects to draw the station bounds and the cells.
    """

    def __init__(
        self,
        station: Station,
        axes,
        faceview="phi",
        local=True,
        inverted=False,
        vmap="time",
        bounds_kwargs=None,
        cells_kwargs=None,
        kwargs=None,
    ):
        """
        Initialize a DTPatch instance.

        :param station: The Station object containing the geometry information.
        :type station: Station
        :param axes: The matplotlib axes to draw the patches on.
        :type axes: matplotlib.axes.Axes
        :param faceview: The view type, either "phi" or "eta".
        :type faceview: str, optional
        :param local: Boolean indicating whether to use local or global coordinates.
        :type local: bool, optional
        :param inverted: Boolean indicating whether to invert the view. If local is False, this will not have any effect.
        :type inverted: bool, optional
        :param vmap: The variable to map to the colormap.
        :type vmap: str, optional
        :param bounds_kwargs: Additional keyword arguments to apply specifically to the bounds PatchCollection.
        :type bounds_kwargs: dict, optional
        :param cells_kwargs: Additional keyword arguments to apply specifically to the cells PatchCollection.
        :type cells_kwargs: dict, optional
        :param kwargs: Additional keyword arguments to apply to both collections.
        :type kwargs: dict, optional
        :return: None. Adds two collections, one for the bounds and another for each DT cell, to the provided matplotlib axes.
        """
        self.vmap = vmap

        self.bounds_collection = PatchCollection(
            [], **(bounds_kwargs or {"facecolor": "none", "edgecolor": "k"}), **(kwargs or {})
        )
        self.bounds_collection.set_picker(True)
        self.bounds_collection.station = station

        self.cells_collection = PatchCollection(
            [], **(cells_kwargs or {"facecolor": "none", "edgecolor": "k"}), **(kwargs or {})
        )

        super().__init__(
            station=station,
            axes=axes,
            collections=[self.bounds_collection, self.cells_collection],
            faceview=faceview,
            local=local,
            inverted=inverted,
        )

    def _draw_collections(self):
        # draw Sl bounds
        self._draw_bounds()
        # draw cells
        self._draw_cells()

    def _draw_bounds(self):
        """
        Draw the bounds of the station and its superlayers.
        """
        frames = []
        # first draw the DT frame
        frames.append(self._create_frame(self.station))

        # then draw the superlayer frames
        for super_layer in self.station.super_layers:
            frames.append(self._create_frame(super_layer))

        self.bounds_collection.set_paths(frames)

    def _draw_cells(self):
        """
        Draw the cells within the superlayers.
        """
        cells = []
        vars = []
        for super_layer in self.station.super_layers:
            if self.view == "phi" and super_layer.number == 2:
                continue  # skip superlayer 2
            elif self.view == "eta" and super_layer.number != 2:
                continue  # skip superlayer 1 and 3
            for layer in super_layer.layers:
                for cell in layer.cells:
                    cell_patch = self._create_frame(cell)
                    var = getattr(cell, self.vmap, 0)

                    cells.append(cell_patch)
                    vars.append(var)

        self.cells_collection.set_paths(cells)
        self.cells_collection.set_array(vars)

    def _create_frame(self, obj):
        """
        Create a frame (matplotlib.patches.Rectangle) for the given object.
        """
        width, height, length = obj.bounds
        x_min, y_min, z_min = obj.local_cords_at_min

        if self.view == "phi" and isinstance(obj, SuperLayer) and obj.number == 2:  # if SL2
            x_min, y_min, z_min = y_min, -x_min, z_min
            width = length

        if (
            self.view == "eta"
            and not isinstance(obj, DriftCell)
            and (obj.number != 2 or isinstance(obj, Station))
        ):  # if SL1 or SL3
            x_min, y_min, z_min = -y_min, x_min, z_min
            x_min = x_min - length
            width = length

        frame = Rectangle((x_min, z_min), width, height)

        return frame

    def change_vmap(self, vmap):
        """
        Change the variable to map to the colormap. Drift cells without the attribute will be set to 0.

        :param vmap: The variable to map to the colormap.
        :type vmap: str
        """
        self.vmap = vmap
        vars = []
        for super_layer in self.station.super_layers:
            if self.view == "phi" and super_layer.number == 2:
                continue  # skip superlayer 2
            elif self.view == "eta" and super_layer.number != 2:
                continue  # skip superlayer 1 and 3
            for layer in super_layer.layers:
                for cell in layer.cells:
                    var = getattr(cell, self.vmap, 0)
                    vars.append(var)

        self.cells_collection.set_array(vars)
