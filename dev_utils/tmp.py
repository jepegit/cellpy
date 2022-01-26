import cellpy

filename = "something.res"


c = cellpy.get(filename, mass=1.2)

c.get_cap(cycle=1)

summary = c.cell.summary
