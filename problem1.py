import pygmt
import numpy as np

np.set_printoptions(suppress=True)

# Load datasets, converting data to meters and removing the offset
height_data = pygmt.grd2xyz("dataset/dataset/heightmaps/ldem_4_uint.tif+s0.5+o-10000", output_type='numpy')
light_data = pygmt.grd2xyz("dataset/dataset/illumination/lroc_color_poles_2k.tif", output_type='numpy')

# Move the data coordinates to the corners of the pixels to line up the longitudes, also recenter 0 degrees longitude
height_data[:, 0] = (height_data[:, 0]-720.5) % 1440
height_data[:, 1] = height_data[:, 1]-0.5

light_data[:, 0] = (light_data[:, 0]-1024.5) % 2048
light_data[:, 1] = light_data[:, 1]-0.5

# Repeat the data at 0 longitude so the polar representation wraps correctly
long0 = height_data[height_data[:, 0] == 0]
long0[:, 0] = 1440
height_data = np.vstack((height_data, long0))

long0 = light_data[light_data[:, 0] == 0]
long0[:, 0] = 2048
light_data = np.vstack((light_data, long0))

# Map coordinates to longitude and latitude
height_data[:, 0] = (height_data[:, 0] / 1440) * 360
height_data[:, 1] = ((height_data[:, 1] / 720) * 180) - 90

light_data[:, 0] = (light_data[:, 0] / 2048) * 360
light_data[:, 1] = ((light_data[:, 1] / 1024) * 180) - 90

# Extract scalar data for bounds
height_z_data = height_data[height_data[:, 1] < -60]
height_min, height_max = np.min(height_z_data[:, 2]), np.max(height_z_data[:, 2])

light_z_data = light_data[light_data[:, 1] < -60]
light_min, light_max = np.min(light_z_data[:, 2]), np.max(light_z_data[:, 2])

# Create a geographic grid from the longitudes and latitudes
grid = pygmt.xyz2grd(height_data, region="0/360/-90/90", spacing=(0.25, 0.25), coltypes="0x,1y", registration='g')
light_grid = pygmt.xyz2grd(light_data, region="0/360/-90/90", spacing=(360/2048, 180/1024), coltypes="0x,1y", registration='g')

print(pygmt.grdinfo(grid))
print(pygmt.grdinfo(light_grid))

fig = pygmt.Figure()

# Change the displayed grid and colour map depending on whether illumination view is toggled
illumination = False
if illumination:
    display_grid = light_grid
    pygmt.makecpt(cmap="balance", series=[light_min, light_max])
else:
    display_grid = grid
    pygmt.makecpt(cmap="magma", series=[height_min, height_max])

# Plot the contour map
with fig.shift_origin(xshift="3c", yshift="14c"):
    fig.grdimage(
        grid=display_grid,
        region="0/360/-90/-60",
        projection="S0/-90/12c",
        cmap=True,
        frame="afg",
    )

    # Place the colour bar and add contours
    if illumination:
        fig.grdcontour(grid=display_grid, levels=40)
        fig.colorbar(position="jML+o-3c/0c+w12c/0.5c", frame=['x+lIllumination'])
    else:
        fig.grdcontour(grid=display_grid, levels=2000)
        fig.colorbar(position="jML+o-3c/0c+w12c/0.5c", frame=['x+lElevation above 1727400m', 'y+lm'])

# Plot the 3D displacement map
# The axes and surface are separated with different regions to prevent the surface from getting clipped
with fig.shift_origin(xshift="w+4c", yshift="2c"):
    # Plot the axes
    fig.basemap(
        region=[0, 360, -90, -60],
        projection="S0/-90/14c",
        perspective=[135, 30],
        frame="afg"
    )

    # Plot the surface
    with fig.shift_origin(yshift="1c"):
        fig.grdview(
            grid=grid,
            drape_grid=display_grid,
            region="0/360/-90/-60/4000/4100",
            perspective=[135, 30],
            projection="S0/-90/14c",
            zscale="0.00005",
            surftype="i",
            cmap=True,
            # transparency=10,
        )

# Add a margin around the plots
fig.show(resize="+m1c")