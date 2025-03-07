from mpldts.geometry._geometry import DTGEOMETRY

class DTFrame(object):
    """
    A parent class representing any possible DT frame object, such as a DT cell, a Layer, a SuperLayer, or the whole DT.
    This class is designed to manage common attributes, getters, setters, etc.
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

    @property
    def id(self):
        """
        Identifier of the Object.

        :return: Identifier of the object.
        :rtype: int
        """
        return self._id

    @property
    def number(self):
        """
        Number of the Object.

        :return: Number of the Object.
        :rtype: int
        """
        return self._number

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
    def global_center(self):
        """
        Global center coordinates of the Object.

        :return: Global center coordinates (x, y, z).
        :rtype: tuple
        """
        return self._x_global, self._y_global, self._z_global

    @property
    def local_position_at_min(self):
        """
        Local position at the minimum coordinates of the Object. It means the lower left corner of the object.

        :return: Local position at minimum coordinates (x, y, z).
        :rtype: tuple
        """
        x = self._x_local - self.width / 2
        y = self._y_local - self.height / 2
        z = self._z_local - self.length / 2
        return x, y, z

    @property
    def global_position_at_min(self):
        """
        Global position at the minimum coordinates of the Object. It means the lower left corner of the object.

        :return: Global position at minimum coordinates (x, y, z).
        :rtype: tuple
        """
        x = self._x_global - self.width / 2
        y = self._y_global - self.height / 2
        z = self._z_global - self.length / 2
        return x, y, z

    @id.setter
    def id(self, id):
        """
        Set the identifier of the Object.

        :param id: Identifier of the Object.
        :type id: int
        """
        self._id = id

    @number.setter
    def number(self, number):
        """
        Set the number of the Object.

        :param number: Number of the Object.
        :type number: int
        """
        self._number = number

    @bounds.setter
    def bounds(self, bounds):
        """
        Set the space dimensions of the Object.

        :param bounds: Space dimensions of the Object (width, height, length).
        :type bounds: tuple
        """
        self._width, self._height, self._length = bounds

    @local_center.setter
    def local_center(self, position):
        """
        Set the local center coordinates of the Object.

        :param position: Local center coordinates (x, y, z).
        :type position: tuple
        """
        self._x_local, self._y_local, self._z_local = self._correct_cords(*position)

    @global_center.setter
    def global_center(self, position):
        """
        Set the global center coordinates of the Object.

        :param position: Global center coordinates (x, y, z).
        :type position: tuple
        """
        self._x_global, self._y_global, self._z_global = position

    def _correct_cords(self, x, y, z):
        """
        Correct the coordinates to the CMS coordinate system. This method should be implemented by subclasses.

        :param x: The x coordinate.
        :type x: float
        :param y: The y coordinate.
        :type y: float
        :param z: The z coordinate.
        :type z: float
        :return: The corrected coordinates.
        :rtype: tuple
        """
        raise NotImplementedError("Subclasses should implement this method")
