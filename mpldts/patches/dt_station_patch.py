from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from mpldts.geometry import Station, DriftCell, SuperLayer
from mpldts.patches.dt_patch_base import DTRelatedPatch


def _is_turned(super_layer):
    """True when a super layer is drawn turned, its cells running along the
    station length instead of its width (the CMS middle super layer).

    The orientation comes from the pose, so a chamber built from a spec draws like
    a CMS one without the patch knowing which super layer number it is.
    """
    rotation = super_layer.transformer.node.pose.rotation
    return abs(rotation[1, 0]) > abs(rotation[0, 0])


def _rows(data):
    """The rows of a cell-data table, whatever shape it arrives in (ADR-024).

    A DataFrame (anything with `to_dict`), one dict, or a list of dicts, each
    keyed by `sl`, `l` and `w`. The identifiers are cast to int: a column read
    from a ROOT branch or a CSV arrives as a float, and `(1.0, 2.0, 3.0)` would
    never match a cell.
    """
    if data is None:
        return []
    if hasattr(data, "to_dict"):
        rows = data.to_dict("records")
    elif isinstance(data, dict):
        rows = [data]
    else:
        rows = [dict(row) for row in data]
    for row in rows:
        try:
            for key in ("sl", "l", "w"):
                row[key] = int(row[key])
        except (KeyError, TypeError, ValueError):
            raise ValueError(
                "the cell data must be keyed by 'sl', 'l' and 'w': got %r" % (row,)
            ) from None
    return rows


def _values(rows, vmap):
    """{(sl, l, w): value} of the column named vmap, 0 where the row has none."""
    return {(row["sl"], row["l"], row["w"]): row.get(vmap, 0) for row in rows}


class DTStationPatch(DTRelatedPatch):
    """
    A class to visualize a 2D representation of a DT Station data in matplotlib context.

    The per-event data is a table keyed by `(sl, l, w)` plus value columns
    (ADR-024): the patch colours the cell that matches a row and leaves the
    others at 0. Nothing is written on the geometry, so the same station draws
    two events without being copied.

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
        data=None,
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
        :param data: The cell data to colour the cells with: a DataFrame, a dict or a list of dicts keyed by
            `sl`, `l` and `w`, plus the column `vmap` (e.g. `[{"sl": 1, "l": 1, "w": 1, "time": 300}, ...]`).
            Cells without a row, or without the column, are drawn with 0.
        :type data: pandas.DataFrame, dict, or list of dict
        :param bounds_kwargs: Additional keyword arguments to apply specifically to the bounds PatchCollection.
        :type bounds_kwargs: dict, optional
        :param cells_kwargs: Additional keyword arguments to apply specifically to the cells PatchCollection.
        :type cells_kwargs: dict, optional
        :param kwargs: Additional keyword arguments to apply to both collections.
        :type kwargs: dict, optional
        :return: None. Adds two collections, one for the bounds and another for each DT cell, to the provided matplotlib axes.
        """
        self.vmap = vmap
        self.data = _rows(data)
        self.values = _values(self.data, vmap)

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

    def _drawn_cells(self):
        """The cells of this view, with the value of their row."""
        cells, vars = [], []
        for super_layer in self.station.super_layers:
            if _is_turned(super_layer) != (self.view == "eta"):
                continue  # phi draws the unturned super layers, eta the turned ones
            for layer in super_layer.layers:
                for cell in layer.cells:
                    cells.append(self._create_frame(cell))
                    vars.append(
                        self.values.get((super_layer.number, layer.number, cell.id), 0)
                    )
        return cells, vars

    def _draw_cells(self):
        """
        Draw the cells within the superlayers.
        """
        cells, vars = self._drawn_cells()
        self.cells_collection.set_paths(cells)
        self.cells_collection.set_array(vars)

    def _create_frame(self, obj):
        """
        Create a frame (matplotlib.patches.Rectangle) for the given object.
        """
        width, height, length = obj.bounds
        x_min, y_min, z_min = obj.local_cords_at_min
        turned = isinstance(obj, SuperLayer) and _is_turned(obj)

        if self.view == "phi" and turned:
            x_min, y_min, z_min = y_min, -x_min, z_min
            width = length

        if self.view == "eta" and not isinstance(obj, DriftCell) and (
            isinstance(obj, Station) or not turned
        ):
            x_min, y_min, z_min = -y_min, x_min, z_min
            x_min = x_min - length
            width = length

        frame = Rectangle((x_min, z_min), width, height)

        return frame

    def change_vmap(self, vmap):
        """
        Change the variable to map to the colormap. Cells without a value for it are set to 0.

        :param vmap: The variable to map to the colormap.
        :type vmap: str
        """
        self.vmap = vmap
        self.values = _values(self.data, vmap)
        self.cells_collection.set_array(self._drawn_cells()[1])
