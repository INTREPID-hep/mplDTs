from mpldts.geometry import Station

chamber = Station(wheel=-1, sector=3, station=1)
# lest define the center ref to cell frame
center_cell = (0, 0, 0)

# it is possible to get the equivalent cordinates in each parent frames (Layer, SuperLayer, and Station)
# using the cell transform manager
transformer = chamber.super_layer(1).layer(1).cell(1).transformer

print("Transform manager: ", transformer)

Layer_center_cell = transformer.transform(center_cell, from_frame="Cell", to_frame="Layer")
SuperLayer_center_cell = transformer.transform(center_cell, from_frame="Cell", to_frame="SuperLayer")
Station_center_cell = transformer.transform(center_cell, from_frame="Cell", to_frame="Station")
CMS_center_cell = transformer.transform(center_cell, from_frame="Cell", to_frame="CMS")

print("Cell center in Cell frame: ", center_cell)
print("Cell center in Layer frame: ", Layer_center_cell)
print("Cell center in SuperLayer frame: ", SuperLayer_center_cell)
print("Cell center in Station frame: ", Station_center_cell, " -> check with config file: ", chamber.super_layer(1).layer(1).cell(1).local_center)
# global
print("Cell center in CMS frame: ", CMS_center_cell, " -> check with config file: ", chamber.super_layer(1).layer(1).cell(1).global_center)