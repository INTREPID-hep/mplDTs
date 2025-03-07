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

# Initialize the DTGeometry object with the path to the XML file
DTGEOMETRY = DTGeometry(
    os.path.join(os.path.dirname(__file__), "../utils/templates/DTGeometry.xml")
)

# Example usage
if __name__ == "__main__":
    dt_geometry = DTGeometry(os.path.abspath("../utils/templates/DTGeometry.xml"))

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
