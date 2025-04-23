from mpldts.geometry._geometry import DTGEOMETRY
from mpldts.geometry.transforms import compute_eta, compute_theta
import warnings


class DTFrame:
    """
    A parent class representing any possible DT object, such as a DT cell, a Layer, a SuperLayer, or
    the whole DT chamber. This class is designed to manage common attributes, getters, setters, and
    other functionalities for DT geometrical objects.

    Attributes
    ----------
        id : int
            Identifier of the DT geometrical object.
        parent : DTFrame
            Parent of the DT geometrical object.
        number : int
            Number identifier of the DT geometrical object.
        width : float
            Width of the DT geometrical object.
        height : float
            Height of the DT geometrical object.
        length : float
            Length of the DT geometrical object.
        bounds : tuple
            Space dimensions of the DT geometrical object (width, height, length).
        local_center : tuple
            Local center coordinates (x, y, z) of the DT geometrical object.
        global_center : tuple
            Global center coordinates (x, y, z) of the DT geometrical object.
        direction : tuple
            Direction vector of the DT geometrical object. It is the normal vector to the object's surface and scencially point to the IP of CMS.
        local_cords_at_min : tuple
            Local coordinates at the minimum position (lower left corner) of the DT geometrical object.
        global_cords_at_min : tuple
            Global coordinates at the minimum position (lower left corner) of the DT geometrical object (not implemented).
        theta : float
            Angle in the XY plane of the DT geometrical object.
        eta : float
            Pseudorapidity of the DT geometrical object.

    .. note::
        - This class can be subclassed to create specific types of DT geometrical objects, such as DT cells, Layers, or SuperLayers.
        - The `global_cords_at_min` property is not implemented and will raise a warning if accessed.
    """

    def __init__(self, rawId=None):
        """
        Initialize the DTFrame object.

        :param rawId: Raw identifier of the DT geometrical object. If not provided, no XML geometrical info will be used to initialize the instance.
        :type rawId: int, optional
        """
        if rawId:
            self.id = rawId
            self.local_center = DTGEOMETRY.get("LocalPosition", rawId=rawId)
            self.global_center = DTGEOMETRY.get("GlobalPosition", rawId=rawId)
            self.direction = DTGEOMETRY.get("NormalVector", rawId=rawId)
            self.bounds = DTGEOMETRY.get("Bounds", rawId=rawId)

    def __str__(self):
        """
        Provide a string representation of the principal DTFrame object properties.

        :return: String representation of the object.
        :rtype: str
        """
        return (
            f"id: {self.id} "
            f"number: {self.number} "
            f"local_center: {self.local_center} "
            f"global_center: {self.global_center} "
            f"direction: {self.direction} "
            f"bounds: {self.bounds}"
        )

    @property
    def parent(self):
        """
        Parent of the Object.

        :return: Parent of the object.
        :rtype: object
        """
        try:
            return self._parent
        except AttributeError:
            warnings.warn(f"This {self.__class__.__name__} instance does not have a Parent.")
            return None

    @property
    def id(self):
        """
        Identifier of the Object.

        :return: Identifier of the object.
        :rtype: int
        """
        try:
            return self._id
        except AttributeError:
            warnings.warn(f"This {self.__class__.__name__} instance does not have an ID assigned.")
            return None

    @property
    def number(self):
        """
        Number identifier of the Object.

        :return: Number of the Object.
        :rtype: int
        """
        try:
            return self._number
        except AttributeError:
            warnings.warn(
                f"This {self.__class__.__name__} instance does not have a Number assigned."
            )
            return None

    @property
    def width(self):
        """
        Width of the Object.

        :return: Width of the object.
        :rtype: float
        """
        return self._width

    @property
    def height(self):
        """
        Height of the Object.

        :return: Height of the object.
        :rtype: float
        """
        return self._height

    @property
    def length(self):
        """
        Length of the Object.

        :return: Length of the object.
        :rtype: float
        """
        return self._length

    @property
    def bounds(self):
        """
        Space dimensions of the Object.

        :return: Space dimensions of the object.
        :rtype: tuple
        """
        return self._width, self._height, self._length

    @property
    def local_center(self):
        """
        Local center coordinates of the Object.

        :return: Local center coordinates (x, y, z).
        :rtype: tuple
        """
        return self._x_local, self._y_local, self._z_local

    @property
    def direction(self):
        """
        Direction of the Object.

        :return: Direction of the object.
        :rtype: tuple
        """
        try:
            return self._direction
        except AttributeError:
            if self.parent:
                return self.parent.direction
            else:
                warnings.warn(
                    f"This {self.__class__.__name__} instance does not have a Direction assigned."
                )
                return None

    @property
    def global_center(self):
        """
        Global center coordinates of the Object.

        :return: Global center coordinates (x, y, z).
        :rtype: tuple
        """
        return self._x_global, self._y_global, self._z_global

    @property
    def local_cords_at_min(self):
        """
        Local cords at the minimum coordinates of the Object. It means the lower left corner of the object.

        :return: Local cords at minimum coordinates (x, y, z).
        :rtype: tuple
        """
        x = self._x_local - self._width / 2
        y = self._y_local - self._length / 2  # y is the length acording to station ref frame
        z = self._z_local - self._height / 2  # z is the height acording to station ref frame
        return x, y, z

    @property
    def global_cords_at_min(self):
        """
        Global cords at the minimum coordinates of the Object. It means the lower left corner of the object.

        .. warning::
            This property is not implemented yet.

        :return: Global cords at minimum coordinates (x, y, z).
        :rtype: tuple
        """
        warnings.warn("Global coordinates at the minimum position is not implemented yet.")
        return None

    @property
    def theta(self):
        """
        Angle theta of the Object according to the global center coordinates.

        :return: Angle theta of the object in radians.
        :rtype: float
        """
        return compute_theta(self._x_global, self._y_global, self._z_global)

    @property
    def eta(self):
        """
        Pseudorapidity of the Object acording to the gloal center coordinates.

        :return: Pseudorapidity of the object.
        :rtype: float
        """
        return compute_eta(self._x_global, self._y_global, self._z_global)

    @parent.setter
    def parent(self, parent):
        """
        Set the parent of the Object.

        :param parent: Parent of the Object.
        :type parent: object
        """
        self._parent = parent

    @id.setter
    def id(self, id: int):
        """
        Set the identifier of the Object.

        :param id: Identifier of the Object.
        :type id: int
        """
        self._id = id

    @number.setter
    def number(self, number: int):
        """
        Set the number of the Object.

        :param number: Number of the Object.
        :type number: int
        """
        self._number = number

    @bounds.setter
    def bounds(self, bounds: tuple):
        """
        Set the space dimensions of the Object.

        :param bounds: Space dimensions of the Object (width, height, length).
        :type bounds: tuple
        """
        self._width, self._height, self._length = bounds

    @local_center.setter
    def local_center(self, cords: tuple):
        """
        Set the local center coordinates of the Object.

        :param cords: Local center coordinates (x, y, z).
        :type cords: tuple
        """
        self._x_local, self._y_local, self._z_local = cords

    @direction.setter
    def direction(self, direction: tuple):
        """
        Set the direction of the Object.

        :param direction: Direction of the Object.
        :type direction: tuple
        """
        self._direction = direction

    @global_center.setter
    def global_center(self, cords: tuple):
        """
        Set the global center coordinates of the Object.

        :param cords: Global center coordinates (x, y, z).
        :type cords: tuple
        """
        self._x_global, self._y_global, self._z_global = cords

