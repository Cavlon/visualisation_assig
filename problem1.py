import pygmt
import numpy as np

np.set_printoptions(suppress=True)

# Load dataset, converting data to meters and removing the offset
data = pygmt.grd2xyz("dataset/dataset/heightmaps/ldem_4_uint.tif+s0.5+o-10000", output_type='numpy')

# Move the data coordinates to the corners of the pixels to line up the longitudes
data[:, 0] = data[:, 0]-0.5
data[:, 1] = data[:, 1]-0.5

# Repeat the data at 0 longitude so the polar representation wraps correctly
long0 = data[data[:, 0] == 0]
long0[:, 0] = 1440
data = np.vstack((data, long0))

# Map coordinates to longitude and latitude
data[:, 0] = (data[:, 0] / 1440) * 360
data[:, 1] = ((data[:, 1] / 720) * 180) - 90

z_data = data[data[:, 1] < -60]
z_min, z_max = np.min(z_data[:, 2]), np.max(z_data[:, 2])

# Create a geographic grid from the longitudes and latitudes
grid = pygmt.xyz2grd(data, region="0/360/-90/90", spacing=(0.25, 0.25), coltypes="0x,1y", registration='g')

print(pygmt.grdinfo(grid))

fig = pygmt.Figure()

pygmt.makecpt(cmap="magma", series=[z_min, z_max])

perspective = True
if perspective:
    fig.grdview(
        grid=grid,
        region="0/360/-90/-60",
        perspective=[135, 30],
        projection="S0/-90/24c",
        zscale="0.00005c",
        surftype="s",
        cmap=True,
        frame="afg"
    )

    fig.colorbar(position="jTL+o-3c/0c+w12c/0.5c", frame=['x+lElevation', 'y+lm'])

else:
    fig.grdimage(
        grid=grid,
        region="0/360/-90/-60",
        projection="S0/-90/24c",
        cmap=True,
        frame="afg",
    )

    fig.colorbar(position=("-5c", "2c"), width="0.5c", length="20c", frame=['x+lElevation', 'y+lm'])

fig.show()