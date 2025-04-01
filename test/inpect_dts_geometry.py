from mpldts.geometry import Station

# only to see gemoetrical cords of a sector in all wheels

sc = 3
for wh in range(-2, 3):
    for st in range(1, 5):
        st = Station(wheel=wh, sector=sc, station=st)
        print(st.name)
        print(st)
        for sl in st.super_layers:
            print("\t",sl)
            for l in sl.layers:
                print(2*"\t",l)
                print(3*"\t", l.cell(l._first_cell_id))
                print(3*"\t", l.cell(len(l.cells)-1))