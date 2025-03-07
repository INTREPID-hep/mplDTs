import xml.etree.ElementTree as ET
import os
import re


class DTGeometry:
    """
    A class to represent the CMS DT Geometry from an XML file.

    Attributes
    ----------
    root : xml.etree.ElementTree.Element
        The root element of the parsed XML tree.
    """

    def __init__(self, xml_file):
        """
        Initialize the DTGeometry object by parsing the XML file.

        :param xml_file: Path to the XML file containing the DT Geometry.
        :type xml_file: str
        """
        tree = ET.parse(xml_file)
        self.root = tree.getroot()

    def get(self, attribute=None, **kwargs):
        """
        Retrieve specific attributes or elements from the XML based on the provided criteria.

        :param attribute: The attribute to retrieve (e.g., 'GlobalPosition', 'LocalPosition', 'Bounds').
        :type attribute: str, optional
        :param kwargs: Additional criteria to filter the elements (e.g., rawId, wh, sec, st, sl, l).
        :type kwargs: dict
        :return: The requested attribute values or element text.
        :rtype: tuple or str
        :raises ValueError: If the element is not found for the given query.
        """
        query = "."
        if "rawId" in kwargs:
            query += f"//*[@rawId='{kwargs['rawId']}']"
        if all(key in kwargs for key in ["wh", "sec", "st"]):
            query += f"//Chamber"
            query += f"[@Id=' Wh:{kwargs['wh']} St:{kwargs['st']} Se:{kwargs['sec']} ']"
        if "sl" in kwargs:
            query += f"//SuperLayer"
            query += f"[@superLayerNumber='{kwargs['sl']}']"
        if "l" in kwargs:
            query += f"//Layer"
            query += f"[@layerNumber='{kwargs['l']}']"

        if attribute is None:
            return self.root.find(query)

        element = self.root.find(query)
        if element is not None:
            if attribute in ["GlobalPosition", "LocalPosition", "NormalVector"]:
                x, y, z = self._transform_to_pos(
                    str_pos_tuple=element.find(attribute).text
                )
                return x, y, z
            elif attribute == "Bounds":
                width, height, length = element.find(attribute).attrib.values()
                return (float(width), float(height), float(length))
            else:
                sub_element = element.find(attribute)
                if sub_element is not None:
                    return sub_element.text
                else:
                    return element.get(attribute)
        else:
            raise ValueError(f"Element not found for query: {query}")

    @staticmethod
    def _transform_to_pos(str_pos_tuple):
        """
        Transform a string representation of coordinates into a tuple of floats.

        :param str: The string containing the coordinates.
        :type str: str
        :param local: Flag to determine if the coordinates are local or global.
        :type local: bool, optional
        :return: A tuple containing the transformed coordinates.
        :rtype: tuple
        """
        cords = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str_pos_tuple)
        x, y, z = (
            float(cord) for cord in cords
        )  # Bear in mind that the CMS local and global coordinates are different and depend of chamber and superlayer
        return (x, y, z)


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


# Initialize the DTGeometry object with the path to the XML file
DTGEOMETRY = DTGeometry(
    os.path.join(os.path.dirname(__file__), "./DTGeometry.xml")
)

# Example usage
if __name__ == "__main__":
    dt_geometry = DTGeometry(os.path.abspath("./DTGeometry.xml"))

    # Retrieve and print global and local positions, and bounds for specific chambers
    global_pos_1 = dt_geometry.get("GlobalPosition", wh=-2, sec=1, st=1)
    local_pos_1 = dt_geometry.get("GlobalPosition", wh=-1, sec=1, st=4)
    bounds = dt_geometry.get("Bounds", wh=-1, sec=1, st=4)
    print(f"Bounds for Wh:-1, Sec:1, St:4: {bounds}")

    print(f"Global position for Wh:-2, Sec:1, St:1: {global_pos_1}")
    print(f"Local position for Wh:1, Sec:1, St:4: {local_pos_1}")

    # Iterate through all layers in a specific SuperLayer and print their attributes
    for sl in dt_geometry.root.find(".//SuperLayer[@rawId='574922752']").iter("Layer"):
        print(sl.attrib)

    # Test retrieving the total number of channels in a specific layer
    print("TEST cells")
    print(dt_geometry.root.find(".//Layer[@rawId='579380224']//Channels//total").text)

    # Test retrieving attributes of a specific SuperLayer
    print("TEST super layer")
    print(dt_geometry.get(rawId=574922752).attrib)
