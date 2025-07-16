import warnings
from typing import List, Union

class Segment:
    """
    A class representing a segment like object, which is simply a row that reconstruct the path of a particle traversing a detector.
    This class is designed to manage common attributes, getters, setters, and other functionalities.

    Attributes
    ----------
        number : int
            Number identifier of the segment.
        local_center : tuple
            Local center coordinates (x, y, z) of the segment.
        global_center : tuple
            Global center coordinates (x, y, z) of the segment.
        direction : tuple
            Direction vector of the segment.

    """

    def __init__(self):
        """
        Initialize the segment.
        """
        pass

    def __str__(self):
        """
        Provide a string representation of the object.

        :return: String representation of the object.
        :rtype: str
        """
        return (
            f"number: {self.number}, "
            f"local_center: {self.local_center}, "
            f"global_center: {self.global_center}, "
            f"local_direction: {self.local_direction} "
            f"global_direction: {self.global_direction}"
        )

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
    def local_center(self):
        """
        Local center coordinates of the Object.

        :return: Local center coordinates (x, y, z).
        :rtype: tuple
        """
        return self._x_local, self._y_local, self._z_local

    @property
    def local_direction(self):
        """
        Direction of the Object.

        :return: Direction of the object.
        :rtype: tuple
        """
        return self._local_direction    
    
    @property
    def global_direction(self):
        """
        Global direction of the Object.

        :return: Global direction of the object.
        :rtype: tuple
        """
        return self._global_direction

    @property
    def global_center(self):
        """
        Global center coordinates of the Object.

        :return: Global center coordinates (x, y, z).
        :rtype: tuple
        """
        return self._x_global, self._y_global, self._z_global

    @number.setter
    def number(self, number: int):
        """
        Set the number of the Object.

        :param number: Number of the Object.
        :type number: int
        """
        self._number = number

    @local_center.setter
    def local_center(self, cords: tuple):
        """
        Set the local center coordinates of the Object.

        :param cords: Local center coordinates (x, y, z).
        :type cords: tuple
        """
        self._x_local, self._y_local, self._z_local = cords

    @global_center.setter
    def global_center(self, cords: tuple):
        """
        Set the global center coordinates of the Object.

        :param cords: Global center coordinates (x, y, z).
        :type cords: tuple
        """
        self._x_global, self._y_global, self._z_global = cords

    @local_direction.setter
    def local_direction(self, direction: tuple):
        """
        Set the direction of the Object.

        :param direction: Direction of the Object.
        :type direction: tuple
        """
        self._local_direction = direction

    @global_direction.setter
    def global_direction(self, direction: tuple):
        """
        Set the global direction of the Object.

        :param direction: Global direction of the Object.
        :type direction: tuple
        """
        self._global_direction = direction


class Segments:
    """
    A class representing a collection of segments.

    This class is designed to manage a collection of Segment objects, providing methods to add,
    remove, and access segments.

    Attributes
    ----------
        segments : list
            List of Segment objects in the collection.
    """

    def __init__(self, segments: Union[List[Segment], Segment] = None):
        """
        Initialize the Segments collection.
        """
        self._segments = segments if isinstance(segments, list) else [segments] if segments else []

    def __len__(self):
        """
        Return the number of segments in the collection.

        :return: Number of segments.
        :rtype: int
        """
        return len(self._segments)

    def __getitem__(self, index):
        """
        Retrieve a segment by its index or slice.

        :param index: Index or slice of the segment(s).
        :type index: int or slice
        :return: Segment or list of segments.
        :rtype: DTSegment or list of DTSegment
        """
        return self._segments[index]

    def __iter__(self):
        """
        Iterate over all segments in the collection.

        :yield: Each segment in the collection.
        :rtype: DTSegment
        """
        return iter(self._segments)

    @property
    def segments(self):
        """
        Get all the segments.

        :return: List of segments.
        :rtype: list
        """
        return self._segments

    def get_by_number(self, numbers):
        """
        Retrieve a segment by its number attribute.

        :param number: The number(s) of the segment to retrieve.
        :type number: int or list of int
        :return: Segment(s) with the specified number(s), or None if not found.
        :rtype: DTSegment or None
        """
        if isinstance(numbers, int):
            numbers = [numbers]
        return list((segment for segment in self._segments if segment.number in numbers))

    def groupby(self, attributes):
        """
        Group segments by one or more specified attributes.

        :param attributes: The attribute(s) to group by.
        :type attributes: str or list of str
        :return: A dictionary where keys are tuples of attribute values and values are Segments objects containing the grouped segments.
        :rtype: dict
        """
        if isinstance(attributes, str):
            attributes = [attributes]

        if not all(all(hasattr(segment, attr) for attr in attributes) for segment in self._segments):
            raise AttributeError(f"Not all segments have the specified attributes: {attributes}.")

        grouped_segments = {}
        for segment in self._segments:
            key = tuple(getattr(segment, attr) for attr in attributes)
            if key not in grouped_segments:
                grouped_segments[key] = []
            grouped_segments[key].append(segment)

        return {key: Segments(value) for key, value in grouped_segments.items()}

    def add(self, segment: Segment):
        """
        Add a Segment object to the collection.

        :param segment: The Segment object to add.
        :type segment: Segment
        """
        self._segments.append(segment)