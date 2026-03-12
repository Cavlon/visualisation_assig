import pygmt
import numpy as np
import panel as pn
import holoviews as hv
from holoviews import streams

np.set_printoptions(suppress=True)

# Load datasets, converting data to meters and removing the offset
height_data_low = pygmt.grd2xyz("dataset/dataset/heightmaps/ldem_4_uint.tif+s0.5+o-10000", output_type='numpy')
light_data_low = pygmt.grd2xyz("dataset/dataset/illumination/lroc_color_poles_2k.tif", output_type='numpy')
height_data_high = pygmt.grd2xyz("dataset/dataset/heightmaps/ldem_16_uint.tif+s0.5+o-10000", output_type='numpy')
light_data_high = pygmt.grd2xyz("dataset/dataset/illumination/lroc_color_poles_4k.tif", output_type='numpy')

# Map coordinates to longitude and latitude, also recenter 0 degrees longitude and latitude
height_data_low[:, 0] = ((height_data_low[:, 0] / 1440) * 360) - 180
height_data_low[:, 1] = ((height_data_low[:, 1] / 720) * 180) - 90
height_data_high[:, 0] = ((height_data_high[:, 0] / 5760) * 360) - 180
height_data_high[:, 1] = ((height_data_high[:, 1] / 2880) * 180) - 90

light_data_low[:, 0] = ((light_data_low[:, 0] / 2048) * 360) - 180
light_data_low[:, 1] = ((light_data_low[:, 1] / 1024) * 180) - 90
light_data_high[:, 0] = ((light_data_high[:, 0] / 4096) * 360) - 180
light_data_high[:, 1] = ((light_data_high[:, 1] / 2048) * 180) - 90

# Normalise the lighting data
light_data_low[:, 2] = light_data_low[:, 2] / 255
light_data_high[:, 2] = light_data_high[:, 2] / 255

# Create a geographic height_grid_low from the longitudes and latitudes
height_grid_low = pygmt.xyz2grd(height_data_low, region="-180/180/-90/90", spacing=(0.25, 0.25), coltypes="0x,1y", registration='p')
height_grid_high = pygmt.xyz2grd(height_data_high, region="-180/180/-90/90", spacing=(0.0625, 0.0625), coltypes="0x,1y", registration='p')

light_grid_low = pygmt.xyz2grd(light_data_low, region="-180/180/-90/90", spacing=(360/2048, 180/1024), coltypes="0x,1y", registration='p')
light_grid_high = pygmt.xyz2grd(light_data_high, region="-180/180/-90/90", spacing=(360/4096, 180/2048), coltypes="0x,1y", registration='p')

light_grid_low = pygmt.grdsample(light_grid_low, spacing=(0.25, 0.25))
light_grid_high = pygmt.grdsample(light_grid_high, spacing=(0.0625, 0.0625))

# Generate the slope data in degrees
slope_gridS = pygmt.grdgradient(height_grid_low, azimuth=180)
slope_grid_low = pygmt.grdgradient(height_grid_low, azimuth=90)
slope_grid_low.values = np.rad2deg(np.arctan(np.sqrt(slope_gridS.values**2 + slope_grid_low.values**2)))

slope_gridS = pygmt.grdgradient(height_grid_high, azimuth=180)
slope_grid_high = pygmt.grdgradient(height_grid_high, azimuth=90)
slope_grid_high.values = np.rad2deg(np.arctan(np.sqrt(slope_gridS.values**2 + slope_grid_high.values**2)))

pn.extension()
hv.extension('bokeh')

# Creates the colour bar
def plot_colourbar(display_data, cmap, cdepth, height):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 1, f"{int(cdepth)+1}+n"])
        fig.colorbar(position="jML", frame=['x+lIllumination'])
    elif display_data == 'Height':
        pygmt.makecpt(cmap=str.lower(cmap), series=[-10000, 10000, f"{int(cdepth)+1}+n"])
        fig.colorbar(position="jML", frame=['x+lElevation', 'y+lm'])
    else:
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 10, f"{int(cdepth)+1}+n"])
        fig.colorbar(position="jML", frame=['x+lSlope', 'y+ldeg'])
    
    fig.savefig("plots/colourbar.png")
    
    return pn.pane.PNG("plots/colourbar.png", width=100, height=height)

# Plots the map in orthographic view to model a globe
def plot_globe(lat, long, display_data, contour_int, cmap, cdepth):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        display_grid = light_grid_low
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 1, f"{int(cdepth)+1}+n"])
    elif display_data == 'Height':
        display_grid = height_grid_low
        pygmt.makecpt(cmap=str.lower(cmap), series=[-10000, 10000, f"{int(cdepth)+1}+n"])
    else:
        display_grid = slope_grid_low
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 10, f"{int(cdepth)+1}+n"])

    # Plot the contour map
    fig.grdimage(
        grid=display_grid,
        projection=f"G{long}/{lat}/18c",
        cmap=True,
        frame="a45fg45",
    )
    if contour_int > 0:
        fig.grdcontour(grid=height_grid_low, levels=contour_int)

    fig.savefig("plots/globe.png")
    
    return pn.pane.PNG("plots/globe.png", width=500, height=500)

# Manage clicks and box selections
click_handler = streams.Tap(x=0, y=0)
region_handler = streams.BoundsXY(bounds=(0, 0, 0, 0))

# Plots the map as a flat 2D map with contours
def plot_interactive_map(display_data, cmap, cdepth):
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        display_grid = light_grid_low
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 1, f"{int(cdepth)+1}+n"])
    elif display_data == 'Height':
        display_grid = height_grid_low
        pygmt.makecpt(cmap=str.lower(cmap), series=[-10000, 10000, f"{int(cdepth)+1}+n"])
    else:
        display_grid = slope_grid_low
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 10, f"{int(cdepth)+1}+n"])

    # Plot the 2D map
    fig.grdimage(
        grid=display_grid,
        projection="Q18c",
        cmap=True,
        frame="a45fg45",
    )

    fig.savefig("plots/interactive.png")

    # Create an interactive view of the map that tracks clicks and selections
    interactive_map = hv.RGB.load_image("plots/interactive.png", bounds=(0, 0, 1, 1)).opts(width=700, height=400, xaxis=None, yaxis=None, toolbar=None, tools=["tap", "box_select"])
    click_handler.source = interactive_map
    region_handler.source = interactive_map
    
    return interactive_map

# Plots the whole data according to the visualisation mode chosen
def plot_map(display_data, contour_int, cmap, cdepth, vis_type):
    print("Regenerating Map...")

    fig = pygmt.Figure()

    if display_data == 'Illumination':
        display_grid = light_grid_low
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 1, f"{int(cdepth)+1}+n"])
    elif display_data == 'Height':
        display_grid = height_grid_low
        pygmt.makecpt(cmap=str.lower(cmap), series=[-10000, 10000, f"{int(cdepth)+1}+n"])
    else:
        display_grid = slope_grid_low
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 10, f"{int(cdepth)+1}+n"])

    # Plot the selected visualisation type
    if vis_type == '2D':
        # Plot the 2D map
        fig.grdimage(
            grid=display_grid,
            projection="Kf18c",
            cmap=True,
            frame="a45fg45",
        )
        if contour_int > 0:
            fig.grdcontour(grid=height_grid_low, levels=contour_int)
    else:
        # Plot the 3D displacement map
        fig.grdview(
            grid=height_grid_low,
            drapegrid=display_grid,
            perspective=[135, 30],
            projection="Kf18c",
            zsize="1c",
            surftype="s",
            cmap=True,
            frame="a45fg45",
            shading=True
        )
    
    fig.savefig("plots/map.png")

    print("Regeneration Completed")
    
    return pn.pane.PNG("plots/map.png", width=700, height=500)

# Plots the whole data according to the visualisation mode chosen
def plot_region(bounds, display_data, contour_int, cmap, cdepth, vis_type):
    print("Regenerating Region...")
    
    left, bottom, right, top = map_x(bounds[0]), map_y(bounds[1]), map_x(bounds[2]), map_y(bounds[3])

    # Bound the selection
    if top > 90:
        top = 90
    if bottom > 90:
        bottom = 90
    if top < -90:
        top = -90
    if bottom < -90:
        bottom = -90
    
    # Allow for selections across 180 degrees by dragging of the edge
    while left < -180:
        left += 360
        right += 360
    
    # Fall back on previously made selection if the new one is invalid
    if left == right or bottom == top:
        bounds = selected_bounds

        if selected_bounds == (0, 0, 0, 0):
            return None
    else:
        bounds = (left, bottom, right, top)

    fig = pygmt.Figure()

    if display_data == 'Illumination':
        display_grid = light_grid_high
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 1, f"{int(cdepth)+1}+n"])
    elif display_data == 'Height':
        display_grid = height_grid_high
        pygmt.makecpt(cmap=str.lower(cmap), series=[-10000, 10000, f"{int(cdepth)+1}+n"])
    else:
        display_grid = slope_grid_high
        pygmt.makecpt(cmap=str.lower(cmap), series=[0, 10, f"{int(cdepth)+1}+n"])
    
    region_center = (bounds[0]+bounds[2])/2

    # Plot the selected visualisation type
    if vis_type == '2D':
        # Plot the 2D map
        fig.grdimage(
            grid=display_grid,
            region=[bounds[0], bounds[2], bounds[1], bounds[3]],
            projection=f"T{region_center}/18c",
            cmap=True,
            frame="afg",
        )
        if contour_int > 0:
            fig.grdcontour(grid=height_grid_high, levels=contour_int, annotation=contour_int)
    else:

        # Plot the 3D displacement map
        fig.grdview(
            grid=height_grid_high,
            drapegrid=display_grid,
            perspective=[135, 30],
            region=[bounds[0], bounds[2], bounds[1], bounds[3]],
            projection=f"T{region_center}/18c",
            zscale=0.2,
            surftype="s",
            cmap=True,
            frame="afg",
            shading=True,
        )
    
    fig.savefig("plots/region.png")

    print("Regeneration Completed")
    
    return pn.Row(plot_colourbar(display_data, cmap, cdepth, 400), pn.pane.PNG("plots/region.png", width=500, height=400))

# MAP BOUNDS: 0.05, 0.05 to 0.98, 0.98
# Map a x-coordinate from the interactive map to a longitude
def map_x(x):
    return (((x - 0.05) / 0.9325) * 360) - 180

# Map a y-coordinate from the interactive map to a latitude
def map_y(y):
    return (((y - 0.05) / 0.93) * 180) - 90

click_pos = (0, 0)
def sample_point(x, y):
    global click_pos

    x = map_x(x)
    y = map_y(y)

    # Only update sample information if the click was in bounds
    if x > -180 and y > -90 and x < 180 and y < 90:
        click_pos = (x, y)
    
    # Sample the data from the clicked point
    elevation = pygmt.grdtrack(points=[click_pos], grid=height_grid_low)
    illumination = pygmt.grdtrack(points=[click_pos], grid=light_grid_low)
    slope = pygmt.grdtrack(points=[click_pos], grid=slope_grid_low)

    return pn.Row(
        "**Point Info:**", 
        f"**Longitude:** {abs(click_pos[0]):.2f}{'E' if click_pos[0] > 0 else 'W'}", 
        f"**Latitude:** {abs(click_pos[1]):.2f}{'N' if click_pos[1] > 0 else 'S'}", 
        f"**Elevation:** {elevation[2].values[0]:.2f}m",
        f"**Illumination:** {illumination[2].values[0]:.3f}",
        f"**Slope:** {slope[2].values[0]:.2f}",
    )

selected_bounds = (0, 0, 0, 0)
def update_bounds(bounds):
    global selected_bounds

    left, bottom, right, top = map_x(bounds[0]), map_y(bounds[1]), map_x(bounds[2]), map_y(bounds[3])

    # Bound the selection
    if top > 90:
        top = 90
    if bottom > 90:
        bottom = 90
    if top < -90:
        top = -90
    if bottom < -90:
        bottom = -90
    
    # Allow for selections across 180 degrees by dragging of the edge
    while left < -180:
        left += 360
    while right > 180:
        right -= 360
    
    # Don't allow non-2D selections
    if right != left and top != bottom:
        selected_bounds = (left, bottom, right, top)
    
    left = f"{abs(selected_bounds[0]):.2f}{'E' if selected_bounds[0] > 0 else 'W'}"
    right = f"{abs(selected_bounds[2]):.2f}{'E' if selected_bounds[2] > 0 else 'W'}"
    top = f"{abs(selected_bounds[3]):.2f}{'N' if selected_bounds[3] > 0 else 'S'}"
    bottom = f"{abs(selected_bounds[1]):.2f}{'N' if selected_bounds[1] > 0 else 'S'}"

    return pn.Row(f"**Longitude Bounds:** [{left}, {right}]", f"**Latitude Bounds:**[{bottom}, {top}]")

# The interactive elements
lat_slider = pn.widgets.FloatSlider(name='Latitude', start=-90, end=90, step=1, value=0)
long_slider = pn.widgets.FloatSlider(name='Longitude', start=-180, end=180, step=1, value=0)

contour_slider = pn.widgets.FloatSlider(name='Contour Interval', start=0, end=5000, step=100, value=4000)

display_data_toggle = pn.widgets.ToggleGroup(name='Data Display', options=['Height', 'Illumination', 'Slope'], behavior="radio")
cmap_toggle = pn.widgets.ToggleGroup(name='Colour Map', options=['Gray', 'Magma', 'Vik'], behavior="radio")
cdepth_toggle = pn.widgets.ToggleGroup(name='Colour Depth', options=['100', '10', '5', '2'], behavior="radio")
vis_toggle = pn.widgets.ToggleGroup(name='Visualisation', options=['2D', '3D'], behavior="radio")

# Bind interactive elements to plots
colour_bar = pn.bind(plot_colourbar, display_data=display_data_toggle, cmap=cmap_toggle, cdepth=cdepth_toggle, height=500)
globe = pn.bind(plot_globe, lat=lat_slider, long=long_slider, display_data=display_data_toggle, contour_int=contour_slider, cmap=cmap_toggle, cdepth=cdepth_toggle)
plot = pn.bind(plot_map, display_data=display_data_toggle, contour_int=contour_slider, cmap=cmap_toggle, cdepth=cdepth_toggle, vis_type=vis_toggle)
interactive = pn.bind(plot_interactive_map, display_data=display_data_toggle, cmap=cmap_toggle, cdepth=cdepth_toggle)
sample_text = pn.bind(sample_point, x=click_handler.param.x, y=click_handler.param.y)
region_update = pn.bind(update_bounds, bounds=region_handler.param.bounds)
region_plot = pn.bind(plot_region, bounds=region_handler.param.bounds, display_data=display_data_toggle, contour_int=contour_slider, cmap=cmap_toggle, cdepth=cdepth_toggle, vis_type=vis_toggle)

# Format the display
layout = pn.Column(
    "# Exploratory Moon Visualisation", 
    pn.Row(lat_slider, long_slider), 
    pn.Row("### Contour Interval:", contour_slider), 
    pn.Row("### Visualised Data:", display_data_toggle), 
    pn.Row("### Colour Map:", cmap_toggle,"### Colour Bands:", cdepth_toggle), 
    pn.Row("### Plot Type:", vis_toggle), 
    pn.Row(colour_bar, globe, plot),
    "### Click the map to sample a point or switch to box select mode with right-click to select a region",
    sample_text,
    region_update,
    pn.Row(interactive, region_plot)
)

layout.show()