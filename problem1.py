import pygmt

grid = "dataset/dataset/heightmaps/ldem_4_uint.tif+s0.5+o-20000"

fig = pygmt.Figure()

fig.grdview(
    grid=grid,
    projection="X20c/10c",
    zscale="0.00005c",
    surftype="s",
    shading=True,
    frame="afg"
)

fig.show()