import pygmt
import numpy as np
import panel as pn
import xarray as xr

np.set_printoptions(suppress=True)

# Load datasets, converting data to meters and removing the offset
height_data = pygmt.grd2xyz("dataset/dataset/heightmaps/ldem_4_uint.tif+s0.5+o-10000", output_type='numpy')
light_data = pygmt.grd2xyz("dataset/dataset/illumination/lroc_color_poles_2k.tif", output_type='numpy')

# Move the data coordinates to the corners of the pixels to line up the longitudes
height_data[:, 0] = height_data[:, 0]-0.5
height_data[:, 1] = height_data[:, 1]-0.5

light_data[:, 0] = light_data[:, 0]-0.5
light_data[:, 1] = light_data[:, 1]-0.5

# Repeat the data at 0 longitude so the polar representation wraps correctly
long0 = height_data[height_data[:, 0] == 0]
long0[:, 0] = 1440
height_data = np.vstack((height_data, long0))

long0 = light_data[light_data[:, 0] == 0]
long0[:, 0] = 2048
light_data = np.vstack((light_data, long0))

# Map coordinates to longitude and latitude, also recenter 0 degrees longitude
height_data[:, 0] = ((height_data[:, 0] / 1440) * 360) - 180
height_data[:, 1] = ((height_data[:, 1] / 720) * 180) - 90

light_data[:, 0] = ((light_data[:, 0] / 2048) * 360) - 180
light_data[:, 1] = ((light_data[:, 1] / 1024) * 180) - 90

# Extract scalar data for bounds
height_z_data = height_data[height_data[:, 1] < -60]
height_min, height_max = np.min(height_z_data[:, 2]), np.max(height_z_data[:, 2])

light_z_data = light_data[light_data[:, 1] < -60]
light_min, light_max = np.min(light_z_data[:, 2]), np.max(light_z_data[:, 2])

# Create a geographic grid from the longitudes and latitudes
grid = pygmt.xyz2grd(height_data, region="-180/180/-90/90", spacing=(0.25, 0.25), coltypes="0x,1y", registration='g')
light_grid = pygmt.xyz2grd(light_data, region="-180/180/-90/90", spacing=(360/2048, 180/1024), coltypes="0x,1y", registration='g')
light_grid = pygmt.grdsample(light_grid, spacing=(0.25, 0.25))

# Crop the data to only the south pole
grid = pygmt.grdcut(grid, region="-180/180/-90/-60")
light_grid = pygmt.grdcut(light_grid, region="-180/180/-90/-60")

# Generate the slope data
slope_gridS = pygmt.grdgradient(grid, azimuth=180)
slope_grid = pygmt.grdgradient(grid, azimuth=90)

# The slopes along the seams are corrupted because of the NaN values so clip them
slope_grid.values[slope_grid.values < -100] = np.nan
slope_gridS.values[slope_gridS.values < -100] = np.nan

slope_grid.values = np.sqrt(slope_gridS.values**2 + slope_grid.values**2)

print(pygmt.grdinfo(grid))
print(pygmt.grdinfo(light_grid))
print(pygmt.grdinfo(slope_grid))

pn.extension()
def plot_colourbar():
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        pygmt.makecpt(cmap=str.lower(cmap_toggle.value), series=[light_min, light_max, f"{cdepth_toggle.value}+n"])
        fig.colorbar(position="jML", frame=['x+lIllumination'])
    elif display_data == 'Height':
        pygmt.makecpt(cmap=str.lower(cmap_toggle.value), series=[height_min, -height_min, f"{cdepth_toggle.value}+n"])
        fig.colorbar(position="jML", frame=['x+lElevation', 'y+lm'])
    else:
        pygmt.makecpt(cmap=str.lower(cmap_toggle.value), series=[0, 0.1, f"{cdepth_toggle.value}+n"])
        fig.colorbar(position="jML", frame=['x+Slope'])
    
    fig.savefig("colorbar.png")
    
    return pn.pane.PNG("colorbar.png", width=100, height=500)

def plot_polar():
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        pygmt.makecpt(cmap=str.lower(cmap_toggle.value), series=[light_min, light_max, f"{cdepth_toggle.value}+n"])
    elif display_data == 'Height':
        pygmt.makecpt(cmap=str.lower(cmap_toggle.value), series=[height_min, -height_min, f"{cdepth_toggle.value}+n"])
    else:
        pygmt.makecpt(cmap=str.lower(cmap_toggle.value), series=[0, 0.1, f"{cdepth_toggle.value}+n"])

    # Plot the contour map
    fig.grdimage(
        grid=display_grid,
        region=f"{long_start}/{long_end}/{latitude[0]}/{latitude[1]}",
        projection="S0/-90/18c",
        cmap=True,
        frame="afg",
    )
    fig.grdcontour(grid=height_grid, levels=contour_slider.value)

    fig.savefig("polar.png")
    
    return pn.pane.PNG("polar.png", width=500, height=500)

def plot_displacement():
    fig = pygmt.Figure()

    if display_data == 'Illumination':
        pygmt.makecpt(cmap=str.lower(cmap_toggle.value), series=[light_min, light_max, f"{cdepth_toggle.value}+n"])
    elif display_data == 'Height':
        pygmt.makecpt(cmap=str.lower(cmap_toggle.value), series=[height_min, -height_min, f"{cdepth_toggle.value}+n"])
    else:
        pygmt.makecpt(cmap=str.lower(cmap_toggle.value), series=[0, 0.1, f"{cdepth_toggle.value}+n"])

    # Plot the 3D displacement map
    fig.grdview(
        grid=height_grid,
        drapegrid=display_grid,
        region=f"{long_start}/{long_end}/{latitude[0]}/{latitude[1]}/{height_min}/{height_max}",
        perspective=[135, 30],
        projection="S0/-90/20c",
        zsize="3c",
        surftype="s",
        cmap=True,
        frame="afg",
        shading="+a45"
    )

    fig.savefig("displacement.png")
    
    return pn.pane.PNG("displacement.png", width=500, height=500)

def generate_plots(clicks):
    print("Regenerating...")
    global latitude
    global display_data
    global long_start
    global long_end
    global height_grid
    global display_grid

    latitude = lat_slider.value
    display_data = display_data_toggle.value
    long_start = long_s_slider.value
    long_end = long_e_slider.value
    height_grid = grid

    # Prevent region bound errors
    if latitude[0] == latitude[1]:
        latitude = (-90, -60)
    
    if long_start == long_end:
        long_start = -180
        long_end = 180

    # Change the displayed grid based on what was selected
    if display_data == 'Illumination':
        display_grid = light_grid
    elif display_data == 'Height':
        display_grid = grid
    else:
        display_grid = slope_grid

    # update the grid to allow the data to wrap around the seam
    if long_start > long_end:
        E = display_grid.sel(lon=slice(long_start, 180))
        W = display_grid.sel(lon=slice(-180, long_end))
        W.coords['lon'] = W.coords['lon'] + 360
        display_grid = xr.concat([E, W], dim="lon").sortby("lon")

        E = height_grid.sel(lon=slice(long_start, 180))
        W = height_grid.sel(lon=slice(-180, long_end))
        W.coords['lon'] = W.coords['lon'] + 360
        height_grid = xr.concat([E, W], dim="lon").sortby("lon")

        long_end += 360
    
    # For some reason the data doesn't plot in this specific instance
    if long_start == -180 and long_end != 180:
        display_grid = display_grid.drop_duplicates(dim='lon')
        height_grid = height_grid.drop_duplicates(dim='lon')

    # Plot the selected visualisation type
    if vis_toggle.value == 'Polar':
        plot = plot_polar()
    else:
        plot = plot_displacement()
    
    pane = pn.Row(plot_colourbar(), plot)

    print("Regeneration Completed")
    
    return pane

latitude = (-90, -60)
display_data='Height'
long_start=-180
long_end=180

height_grid = grid
display_grid = grid

# The interactive elements
lat_slider = pn.widgets.RangeSlider(name='Latitude', start=-90, end=-60, step=1, value=(-90, -60))
long_s_slider = pn.widgets.FloatSlider(name='Longitude Start', start=-180, end=180, step=1, value=-180)
long_e_slider = pn.widgets.FloatSlider(name='Longitude End', start=-180, end=180, step=1, value=180)

contour_slider = pn.widgets.FloatSlider(name='Contour Interval', start=500, end=5000, step=100, value=2000)

display_data_toggle = pn.widgets.ToggleGroup(name='Data Display', options=['Height', 'Illumination', 'Slope'], behavior="radio")
cmap_toggle = pn.widgets.ToggleGroup(name='Colour Map', options=['Gray', 'Magma', 'Balance'], behavior="radio")
cdepth_toggle = pn.widgets.ToggleGroup(name='Colour Depth', options=['5', '10', '20', '100'], behavior="radio")
vis_toggle = pn.widgets.ToggleGroup(name='Visualisation', options=['Polar', 'Displacement'], behavior="radio")

polar_pane = None 
displacement_pane = None

update_btn = pn.widgets.Button(name='Regenerate Plot')
plots = pn.bind(generate_plots, clicks=update_btn.param.clicks)

layout = pn.Column(
    "# Lunar South Pole Visualisation", 
    lat_slider, 
    pn.Row(long_s_slider, long_e_slider), 
    contour_slider, 
    pn.Row("### Visualised Data:", display_data_toggle), 
    pn.Row("### Colour Map:", cmap_toggle, cdepth_toggle), 
    pn.Row("### Plot Type:", vis_toggle), 
    update_btn, 
    plots
)

layout.show()