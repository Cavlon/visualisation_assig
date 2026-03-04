import pygmt
import numpy as np

np.set_printoptions(suppress=True)

data = pygmt.grd2xyz("dataset/dataset/heightmaps/ldem_4_uint.tif+s0.5+o-20000", output_type='numpy')
data[:, 0] = data[:, 0]-0.5
data[:, 1] = data[:, 1]-0.5

long0 = data[data[:, 0] == 0]
long0[:, 0] = 1440
data = np.vstack((data, long0))

data[:, 0] = (data[:, 0] / 1440) * 360
data[:, 1] = ((data[:, 1] / 720) * 180) - 90

grid = pygmt.xyz2grd(data, region="0/360/-90/90", spacing=(0.25, 0.25), registration='g')

fig = pygmt.Figure()

# pygmt.makecpt(cmap="turbo", series=[np.nanmin(data[:, 2]), np.nanmax(data[:, 2])])

fig.grdview(
    grid=grid,
    region="0/360/-90/-60+g",
    perspective=[135, 30],
    projection="S0/-90/24c",
    zscale="0.00005c",
    surftype="s",
    shading=True,
    # cmap=True,
    frame="afg"
)

# fig.grdimage(
#     grid=grid,
#     region="0/360/-90/-60+g",
#     projection="S0/-90/12c",
#     shading=True,
#     frame="afg"
# )

# fig.colorbar(perspective=True, frame=["a2000", "clunar height (m)"])

fig.show()