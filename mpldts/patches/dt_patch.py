from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from matplotlib.transforms import Affine2D
from mpldts.geometry import Station, DriftCell, SuperLayer
from mpldts.geometry.transforms import change_frame
from math import atan2, degrees, sqrt


class DTPatch:
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
        self.station = station
        self.axes = axes
        self.view = faceview
        self.local = local
        self.vmap = vmap
        self.inverted = (
            inverted if inverted and local else False
        )  # if global required (local = False), no inversion needed

        self.bounds_collection = PatchCollection(
            [], **(bounds_kwargs or {"facecolor": "none", "edgecolor": "k"}), **(kwargs or {})
        )
        self.bounds_collection.set_picker(True)
        self.bounds_collection.station = station

        self.cells_collection = PatchCollection(
            [], **(cells_kwargs or {"facecolor": "none", "edgecolor": "k"}), **(kwargs or {})
        )

        # draw Sl bounds
        self._draw_bounds()
        # draw cells
        self._draw_cells()

        # add collections to axes
        axes.add_collection(self.bounds_collection)
        axes.add_collection(self.cells_collection)

        self.inversion_factors = {
            "phi": (-1, -1) if self.station.number % 2 == 0 else (1, -1),
            "eta": (1, -1) if self.station.number % 2 == 0 else (-1, -1),
        }

        if self.inverted:
            self.invert_station()

        if not self.local:
            self.move_to_global()

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
            x_min, y_min, z_min = change_frame(
                (x_min, y_min, z_min), from_frame="SL2", to_frame="Station"
            )
            width = length

        if (
            self.view == "eta" and not isinstance(obj, DriftCell) and (obj.number != 2 or isinstance(obj, Station))
        ):  # if SL1 or SL3
            x_min, y_min, z_min = change_frame(
                (x_min, y_min, z_min), from_frame="Station", to_frame="SL2"
            )
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

    def move_to_global(self):
        """
        Move the collections to the global CMS frame. This method can be called by the user but ensure
        that the PatchCollections are not inverted, as this method will invert them to adjust to the global frame.
        """

        base_bounds_transform = self.bounds_collection.get_transform()
        base_cells_transform = self.cells_collection.get_transform()
        transformation = Affine2D()

        x, y, z = self.station.global_center

        if not self.inverted:
            transformation = transformation.scale(*self.inversion_factors[self.view])

        if self.view == "phi":
            nx, ny, _ = self.station.direction
            angle = degrees(atan2(ny, nx)) + 90  # ang_incline = ang_normal_refx + 90
            transformation = transformation.translate(x, y).rotate_deg_around(x, y, angle)

        elif self.view == "eta":
            r = sqrt(x**2 + y**2)
            transformation = transformation.translate(z, r)

        self.bounds_collection.set_transform(transformation + base_bounds_transform)
        self.cells_collection.set_transform(transformation + base_cells_transform)


    def invert_station(self):
        """
        Invert the station view. The inversion depends on the current view and the station number:

        - For the "phi" view, the station is inverted along the x-axis.
        - For the "eta" view, the station is inverted along both the x-axis and y-axis 
        (in the DT Chamber local frame).

        The station number determines the inversion factors:
        - If the station number is even, the inversion factors are reversed.
        """
        if not self.local:
            return
        self.inverted = not self.inverted
        base_bounds_transform = self.bounds_collection.get_transform()
        base_cells_transform = self.cells_collection.get_transform()

        adjustment = Affine2D().scale(*self.inversion_factors[self.view])

        self.bounds_collection.set_transform(adjustment + base_bounds_transform)
        self.cells_collection.set_transform(adjustment + base_cells_transform)
