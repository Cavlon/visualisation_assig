import os
import pygmt
import numpy as np
import panel as pn
import holoviews as hv
from holoviews import streams

if not os.path.exists("plots"):
    os.makedirs("plots")

# Load datasets, converting data to meters and removing the offset
height_data_low = pygmt.grd2xyz("dataset/dataset/heightmaps/ldem_4_uint.tif+s0.5+o-10000", output_type='numpy')
light_data_low = pygmt.grd2xyz("dataset/dataset/illumination/lroc_color_poles_2k.tif", output_type='numpy')

# Map coordinates to longitude and latitude, also recenter 0 degrees longitude and latitude
height_data_low[:, 0] = ((height_data_low[:, 0] / 1440) * 360) - 180
height_data_low[:, 1] = ((height_data_low[:, 1] / 720) * 180) - 90

light_data_low[:, 0] = ((light_data_low[:, 0] / 2048) * 360) - 180
light_data_low[:, 1] = ((light_data_low[:, 1] / 1024) * 180) - 90

# Normalise the lighting data
light_data_low[:, 2] = light_data_low[:, 2] / 255

# Create a geographic height_grid_low from the longitudes and latitudes
height_grid_low = pygmt.xyz2grd(height_data_low, region="-180/180/-90/90", spacing=(0.25, 0.25), coltypes="0x,1y", registration='p')
light_grid_low = pygmt.xyz2grd(light_data_low, region="-180/180/-90/90", spacing=(360/2048, 180/1024), coltypes="0x,1y", registration='p')
light_grid_low = pygmt.grdsample(light_grid_low, spacing=(0.25, 0.25))

pn.extension()
hv.extension('bokeh')

# Creates the colour bar
def plot_colourbar(display_data, cmap, cdepth, width):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 1, f"{int(cdepth)+1}+n"])
        fig.colorbar(position="jBC", frame=['x+lIllumination'])
    else:
        pygmt.makecpt(cmap=str.lower(cmap), series=[-10000, 10000, f"{int(cdepth)+1}+n"])
        fig.colorbar(position="jBC", frame=['x+lElevation', 'y+lm'])
    
    fig.savefig(f"plots/colourbar_{display_data}.png")
    
    return pn.pane.PNG(f"plots/colourbar_{display_data}.png", width=width, height=100)

# Plots the map in orthographic view to model a globe
def plot_globe(lat, long, lat_range, display_data, vis_type):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        display_grid = light_grid_low
        if vis_type == "2D":
            pygmt.makecpt(cmap='gray', series=[0, 1, f"101+n"])
        else:
            pygmt.makecpt(cmap='gray', series=[0, 1, f"11+n"])
        contour_int = 0
    else:
        display_grid = height_grid_low
        pygmt.makecpt(cmap='vik', series=[-10000, 10000, f"11+n"])
        contour_int = 4000
    
    if lat_range[0] == lat_range[1]:
        lat_range = (-90, 90)
    
    # Extract the data from the defined region
    highlight_grid = display_grid.where((display_grid.lat >= lat_range[0]) & (display_grid.lat <= lat_range[1]))
    height_grid = height_grid_low.where((height_grid_low.lat >= lat_range[0]) & (height_grid_low.lat <= lat_range[1]))

    if vis_type == "2D":
        # Plot the contour map
        fig.grdimage(
            grid=highlight_grid,
            projection=f"G{long}/{lat}/18c",
            cmap=True,
            frame="a45fg45",
        )
        if contour_int > 0:
            fig.grdcontour(grid=height_grid, levels=contour_int)
    else:
        # Plot the 3D displacement map
        fig.grdview(
            grid=height_grid,
            drapegrid=highlight_grid,
            perspective=[135, 30],
            projection=f"G{long}/{lat}/18c",
            zscale=0.0001,
            surftype="s",
            cmap=True,
            frame="afg",
            shading=True,
        )

    fig.savefig(f"plots/globe_{display_data}.png")
    
    return pn.pane.PNG(f"plots/globe_{display_data}.png", width=500, height=500)

# Manage clicks and box selections
click_handler1 = streams.Tap(x=0, y=0)
click_handler2 = streams.Tap(x=0, y=0)

# Plots the map as a flat 2D map with contours
def plot_interactive_map(display_data, lat_range):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        display_grid = light_grid_low
        pygmt.makecpt(cmap='gray', series=[0, 1, f"101+n"])
        contour_int = 0.5
    else:
        display_grid = height_grid_low
        pygmt.makecpt(cmap='vik', series=[-10000, 10000, f"10+n"])
        contour_int = 4000
    
    if lat_range[0] == lat_range[1]:
        lat_range = (-90, 90)
    
    # Extract the data from the defined region
    highlight_grid = display_grid.where((display_grid.lat >= lat_range[0]) & (display_grid.lat <= lat_range[1]))

    # Plot the 2D map
    fig.grdimage(
        grid=highlight_grid,
        projection="Q18c",
        cmap=True,
        frame="a45fg45",
    )
    if contour_int > 0:
        fig.grdcontour(grid=display_grid, levels=contour_int)

    fig.savefig(f"plots/interactive_{display_data}.png")

    # Create an interactive view of the map that tracks clicks and selections
    interactive_map = hv.RGB.load_image(f"plots/interactive_{display_data}.png", bounds=(0, 0, 1, 1)).opts(width=700, height=400, xaxis=None, yaxis=None, toolbar=None, tools=["tap", "box_select"])
    
    if display_data == 'Illumination':
        click_handler1.source = interactive_map
    else:
        click_handler2.source = interactive_map
    
    return interactive_map

def plot_histogram(display_data, lat_range):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        display_grid = light_grid_low
        pygmt.makecpt(cmap='gray', series=[0, 1, f"101+n"])
        region = [0, 1, 0, 0]
        series = 0.05
        label = "Illumination"
    else:
        display_grid = height_grid_low
        pygmt.makecpt(cmap='vik', series=[-10000, 10000, f"11+n"])
        region = [-10000, 10000, 0, 0]
        series = 1000
        label = "Elevation (m)"
    
    if lat_range[0] == lat_range[1]:
        lat_range = (-90, 90)
    
    # Extract the data from the defined region and clean it for plotting
    data_grid = display_grid.where((display_grid.lat >= lat_range[0]) & (display_grid.lat <= lat_range[1]))
    data = data_grid.values.flatten()
    data = data[~np.isnan(data)]

    # Plot the histogram
    fig.histogram(
        data=data,
        region=region,
        projection="X10c",
        series=series,
        frame=["WStr", f"xaf+l{label}", "yaf+lProportion%"],
        cmap=True,
        pen="1p,darkgray,solid",
        histtype=1
    )
    
    fig.savefig(f"plots/histogram_{display_data}.png")
    
    return pn.pane.PNG(f"plots/histogram_{display_data}.png", width=400, height=400)

# MAP BOUNDS: 0.05, 0.05 to 0.98, 0.98
# Map a x-coordinate from the interactive map to a longitude
def map_x(x):
    return int((((x - 0.05) / 0.9325) * 360) - 180)

# Map a y-coordinate from the interactive map to a latitude
def map_y(y):
    return int((((y - 0.05) / 0.93) * 180) - 90)

click_pos = (0, 0)
prev_click = (0, 0)
def sample_point(x1, y1, x2, y2):
    global click_pos
    global prev_click

    # Determine which map was clicked
    if x1 == prev_click[0] and y1 == prev_click[1]:
        x, y = x2, y2
    else:
        x, y = x1, y1
    
    prev_click = (x1, y1)

    x = map_x(x)
    y = map_y(y)

    # Only update sample information if the click was in bounds
    if x > -180 and y > -90 and x < 180 and y < 90:
        click_pos = (x, y)
    
    # Sample the data from the clicked point
    elevation = pygmt.grdtrack(points=[click_pos], grid=height_grid_low)
    illumination = pygmt.grdtrack(points=[click_pos], grid=light_grid_low)

    return pn.Row(
        "**Point Info:**", 
        f"**Longitude:** {abs(click_pos[0]):.2f}{'E' if click_pos[0] > 0 else 'W'}", 
        f"**Latitude:** {abs(click_pos[1]):.2f}{'N' if click_pos[1] > 0 else 'S'}", 
        f"**Elevation:** {elevation[2].values[0]:.2f}m",
        f"**Illumination:** {illumination[2].values[0]:.3f}",
    )

# The interactive elements
lat_slider = pn.widgets.FloatSlider(name='Latitude', start=-90, end=90, step=1, value=0)
long_slider = pn.widgets.FloatSlider(name='Longitude', start=-180, end=180, step=1, value=0)

lat_range_slider = pn.widgets.RangeSlider(name='Latitude Region', start=-90, end=90, step=1, value=(-90, 90))

vis_toggle = pn.widgets.ToggleGroup(name='Visualisation', options=['2D', '3D'], behavior="radio")

# Bind interactive elements to plots
colour_barI = plot_colourbar('Illumination', 'gray', 100, 500)
colour_barH = plot_colourbar('Height', 'vik', 10, 500)

interactiveI = pn.bind(plot_interactive_map, display_data='Illumination', lat_range=lat_range_slider)
interactiveH = pn.bind(plot_interactive_map, display_data='Height', lat_range=lat_range_slider)

globeI = pn.bind(plot_globe, lat=lat_slider, long=long_slider, lat_range=lat_range_slider, display_data='Illumination', vis_type=vis_toggle)
globeH = pn.bind(plot_globe, lat=lat_slider, long=long_slider, lat_range=lat_range_slider, display_data='Height', vis_type=vis_toggle)

histogramI = pn.bind(plot_histogram, display_data="Illumination", lat_range=lat_range_slider)
histogramH = pn.bind(plot_histogram, display_data="Height", lat_range=lat_range_slider)

sample_text = pn.bind(sample_point, x1=click_handler1.param.x, y1=click_handler1.param.y, x2=click_handler2.param.x, y2=click_handler2.param.y)

# Format the display
layout = pn.Column(
    "# General Moon Visualisation", 
    "### Define the region and the rotate the globe with the sliders:",
    lat_range_slider,
    pn.Row(lat_slider, long_slider), 
    vis_toggle,
    pn.Row(globeI, globeH),
    pn.Row(colour_barI, colour_barH),
    "## Distribution of Illumination and Elevation within the Region:",
    pn.Row(histogramI, histogramH),
    "## Interactive Maps:",
    "### Zoom in with scroll, pan with drag, or click to sample a point",
    sample_text,
    pn.Row(interactiveI, interactiveH)
)

layout.show()