import pygmt
import numpy as np
import panel as pn
import xarray as xr

np.set_printoptions(suppress=True)

# Load datasets, converting data to meters and removing the offset
height_data = pygmt.grd2xyz("dataset/dataset/heightmaps/ldem_4_uint.tif+s0.5+o-10000", output_type='numpy')
light_data = pygmt.grd2xyz("dataset/dataset/illumination/lroc_color_poles_2k.tif", output_type='numpy')

# Map coordinates to longitude and latitude, also recenter 0 degrees longitude and latitude
height_data[:, 0] = ((height_data[:, 0] / 1440) * 360) - 180
height_data[:, 1] = ((height_data[:, 1] / 720) * 180) - 90

light_data[:, 0] = ((light_data[:, 0] / 2048) * 360) - 180
light_data[:, 1] = ((light_data[:, 1] / 1024) * 180) - 90

# Create a geographic grid from the longitudes and latitudes
grid = pygmt.xyz2grd(height_data, region="-180/180/-90/90", spacing=(0.25, 0.25), coltypes="0x,1y", registration='p')
light_grid = pygmt.xyz2grd(light_data, region="-180/180/-90/90", spacing=(360/2048, 180/1024), coltypes="0x,1y", registration='p')
light_grid = pygmt.grdsample(light_grid, spacing=(0.25, 0.25))

# Generate the slope data
slope_gridS = pygmt.grdgradient(grid, azimuth=180)
slope_grid = pygmt.grdgradient(grid, azimuth=90)
slope_grid.values = np.sqrt(slope_gridS.values**2 + slope_grid.values**2)

print(pygmt.grdinfo(grid))
print(pygmt.grdinfo(light_grid))
print(pygmt.grdinfo(slope_grid))

pn.extension()

# Creates the colour bar
def plot_colourbar(display_data, cmap, cdepth):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 255, f"{int(cdepth)+1}+n"])
        fig.colorbar(position="jML", frame=['x+lIllumination'])
    elif display_data == 'Height':
        pygmt.makecpt(cmap=str.lower(cmap), series=[-10000, 10000, f"{int(cdepth)+1}+n"])
        fig.colorbar(position="jML", frame=['x+lElevation', 'y+lm'])
    else:
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 0.1, f"{int(cdepth)+1}+n"])
        fig.colorbar(position="jML", frame=['x+lSlope'])
    
    fig.savefig("plots/colourbar.png")
    
    return pn.pane.PNG("plots/colourbar.png", width=100, height=500)

# Plots the map in orthographic view to model a globe
def plot_globe(lat, long, display_data, contour_int, cmap, cdepth):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        display_grid = light_grid
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 255, f"{int(cdepth)+1}+n"])
    elif display_data == 'Height':
        display_grid = grid
        pygmt.makecpt(cmap=str.lower(cmap), series=[-10000, 10000, f"{int(cdepth)+1}+n"])
    else:
        display_grid = slope_grid
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 0.1, f"{int(cdepth)+1}+n"])

    # Plot the contour map
    fig.grdimage(
        grid=display_grid,
        projection=f"G{long}/{lat}/18c",
        cmap=True,
        frame="afg",
    )
    if contour_int > 0:
        fig.grdcontour(grid=grid, levels=contour_int)

    fig.savefig("plots/globe.png")
    
    return pn.pane.PNG("plots/globe.png", width=500, height=500)

# Plots the map as a flat 2D map with contours
def plot_2d(display_data, contour_int, cmap, cdepth, file):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        display_grid = light_grid
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 255, f"{int(cdepth)+1}+n"])
    elif display_data == 'Height':
        display_grid = grid
        pygmt.makecpt(cmap=str.lower(cmap), series=[-10000, 10000, f"{int(cdepth)+1}+n"])
    else:
        display_grid = slope_grid
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 0.1, f"{int(cdepth)+1}+n"])

    # Plot the 2D map
    fig.grdimage(
        grid=display_grid,
        projection="Kf18c",
        cmap=True,
        frame="afg",
    )
    if contour_int > 0:
        fig.grdcontour(grid=grid, levels=contour_int)

    fig.savefig("plots/" + file)
    
    return pn.pane.PNG("plots/" + file, width=700, height=500)

# Plots the map as a 3D displacement map
def plot_3d(display_data, contour_int, cmap, cdepth, file):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        display_grid = light_grid
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 255, f"{int(cdepth)+1}+n"])
    elif display_data == 'Height':
        display_grid = grid
        pygmt.makecpt(cmap=str.lower(cmap), series=[-10000, 10000, f"{int(cdepth)+1}+n"])
    else:
        display_grid = slope_grid
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 0.1, f"{int(cdepth)+1}+n"])

    # Plot the 3D displacement map
    fig.grdview(
        grid=grid,
        drapegrid=display_grid,
        perspective=[135, 30],
        projection="Kf18c",
        zsize="1c",
        surftype="s",
        cmap=True,
        frame="afg",
        shading=True
    )

    fig.savefig("plots/" + file)
    
    return pn.pane.PNG("plots/" + file, width=700, height=500)

# Plots the whole data according to the visualisation mode chosen
def plot_map(display_data, contour_int, cmap, cdepth, vis_type):
    print("Regenerating...")

    # Plot the selected visualisation type
    if vis_type == '2D':
        plot = plot_2d(display_data, contour_int, cmap, cdepth, "2d.png")
    else:
        plot = plot_3d(display_data, contour_int, cmap, cdepth, "3d.png")

    print("Regeneration Completed")
    
    return plot

# The interactive elements
lat_slider = pn.widgets.FloatSlider(name='Latitude', start=-90, end=90, step=1, value=0)
long_slider = pn.widgets.FloatSlider(name='Longitude', start=-180, end=180, step=1, value=0)

contour_slider = pn.widgets.FloatSlider(name='Contour Interval', start=0, end=5000, step=100, value=4000)

display_data_toggle = pn.widgets.ToggleGroup(name='Data Display', options=['Height', 'Illumination', 'Slope'], behavior="radio")
cmap_toggle = pn.widgets.ToggleGroup(name='Colour Map', options=['Gray', 'Magma', 'Vik'], behavior="radio")
cdepth_toggle = pn.widgets.ToggleGroup(name='Colour Depth', options=['100', '10', '5', '2'], behavior="radio")
vis_toggle = pn.widgets.ToggleGroup(name='Visualisation', options=['2D', '3D'], behavior="radio")

# Bind interactive elements to plots
colour_bar = pn.bind(plot_colourbar, display_data=display_data_toggle, cmap=cmap_toggle, cdepth=cdepth_toggle)
globe = pn.bind(plot_globe, lat=lat_slider, long=long_slider, display_data=display_data_toggle, contour_int=contour_slider, cmap=cmap_toggle, cdepth=cdepth_toggle)
plot = pn.bind(plot_map, display_data=display_data_toggle, contour_int=contour_slider, cmap=cmap_toggle, cdepth=cdepth_toggle, vis_type=vis_toggle)

# Format the display
layout = pn.Column(
    "# Exploratory Moon Visualisation", 
    pn.Row(lat_slider, long_slider), 
    pn.Row("### Contour Interval:", contour_slider), 
    pn.Row("### Visualised Data:", display_data_toggle), 
    pn.Row("### Colour Map:", cmap_toggle,"### Colour Bands:", cdepth_toggle), 
    pn.Row("### Plot Type:", vis_toggle), 
    pn.Row(colour_bar, globe, plot)
)

layout.show()