import os
import re
import xml.etree.ElementTree as ET


class DTGeometry:
    """
    A class to easy access to the CMS DT Geometry from the XML file.

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
        :return: The requested attribute values or element.
        :rtype: tuple, str, or xml.etree.ElementTree.Element
        :raises ValueError: If the element or attribute is not found for the given query.
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
        if "w" in kwargs:
            query += f"//Wire"
            query += f"[@wireNumber='{kwargs['w']}']"

        element = self.root.find(query)
        if attribute is None:
            return element

        if element is not None:
            if attribute in ["GlobalPosition", "LocalPosition", "NormalVector"]:
                try:
                    x, y, z = self._transform_to_pos(str_pos_tuple=element.find(attribute).text)
                except AttributeError:
                    x, y, z = self._transform_to_pos(str_pos_tuple=element.get(attribute))
                return x, y, z
            elif attribute == "Bounds":
                width, height, length = element.find(attribute).attrib.values()
                return (float(width), float(height), float(length))
            elif "wire" in attribute.lower():
                element = element.find(".//Wires")
                width, height, length, first, last = element.attrib.values()
                if attribute == "WiresSize":
                    return (float(width), float(height), float(length))
                elif attribute == "WiresRange":
                    return (int(first), int(last))
                else:
                    return element
            else:
                sub_element = element.find(attribute)
                if sub_element is not None:
                    return sub_element
                else:
                    try:
                        return element.get(attribute)
                    except AttributeError:
                        raise ValueError(
                            f"Attribute or element '{attribute}' not found for query: {query}"
                        )
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
        x, y, z = (float(cord) for cord in cords)
        return (x, y, z)


# Initialize the DTGeometry object with the path to the XML file
DTGEOMETRY = DTGeometry(os.path.join(os.path.dirname(__file__), "./DTGeometry_v3.xml"))

# Example usage
if __name__ == "__main__":
    dt_geometry = DTGeometry(os.path.abspath("./DTGeometry_v3.xml"))

    # Retrieve and print global and local positions, and bounds for specific chambers
    global_pos_1 = dt_geometry.get("GlobalPosition", wh=-2, sec=1, st=1)
    local_pos_1 = dt_geometry.get("GlobalPosition", wh=-1, sec=1, st=4)
    bounds = dt_geometry.get("Bounds", wh=-1, sec=1, st=4)
    print(f"Bounds for Wh:-1, Sec:1, St:4: {bounds}")

    print(f"Global position for Wh:-2, Sec:1, St:1: {global_pos_1}")
    print(f"Local position for Wh:1, Sec:1, St:4: {local_pos_1}")

    # Iterate through all layers in a specific SuperLayer and print their attributes
    # 1. by using the root element
    for layer in dt_geometry.root.find(".//SuperLayer[@rawId='574922752']").iter("Layer"):
        print("Layer", layer.attrib)
        break
    # 2. by using the get method
    for layer in dt_geometry.get(rawId="574922752").iter("Layer"):
        print("Layer", layer.attrib)
        break
    # Test retrieving attributes of a specific SuperLayer
    print("Super_Layer", dt_geometry.get(rawId=574922752).attrib)
