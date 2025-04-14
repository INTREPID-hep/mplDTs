from mpldts.geometry import Station
from mpldts.geometry import DTGeometry
# only to see gemoetrical cords of a sector in all wheels

sc = 3
for wh in range(-2, 3):
    for sta in range(1, 5):
        st = Station(wheel=wh, sector=sc, station=sta)
        print(st.name)
        print(st)
        for sl in st.super_layers:
            print("\t", sl)
            for l in sl.layers:
                print(2*"\t", l)
                for cell in l.cells:
                    print(3*"\t", l.cell(l._first_cell_id))
                    print(3*"\t", l.cell(len(l.cells)-1))