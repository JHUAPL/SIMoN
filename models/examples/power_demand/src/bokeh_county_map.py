import bokeh.sampledata
bokeh.sampledata.download()

from bokeh.embed import file_html
from bokeh.resources import CDN

from bokeh.io import show, save
from bokeh.models import LogColorMapper
from bokeh.palettes import Viridis256 as palette
from bokeh.plotting import figure
from bokeh.io import export_png

from bokeh.sampledata.us_counties import data as counties
from bokeh.sampledata.unemployment import data as unemployment

palette.reverse()

counties = {
            code: county for code, county in counties.items() if county["state"] not in ["ak", "hi", "pr", "vi"]
            }

# in ["ca", "nv", "nm", "az"]

# convert Shannon County (FIPS = 46113) from Bokeh (outdated) to updated Oglala Lakota County (FIPS = 46102)
#counties[(46,102)] = counties.pop((46,113))
#counties[(46,102)]['name'] = "Oglala Lakota"
#counties[(46,102)]['detailed name'] = "Oglala Lakota County, South Dakota"

def CountyMap(county_data):

    county_xs = []
    county_ys = []
    county_names = []
    county_rates = []
    county_states = []

    for fips in county_data:
        if len(fips) == 4:
            state_num = fips[0]
            county_num = fips[1:].lstrip("0")
        elif len(fips) == 5:
            state_num = fips[0:2]
            county_num = fips[2:].lstrip("0")
        tup = (int(state_num), int(county_num))

        county = counties.get(tup)
        if not county:
            continue
        county_xs.append(county['lons'])
        county_ys.append(county['lats'])
        county_names.append(county['name'])
        county_rates.append(county_data[fips])
        county_states.append(county['state'].upper())

    color_mapper = LogColorMapper(palette=palette)

    data=dict(
    x=county_xs,
    y=county_ys,
    name=county_names,
    rate=county_rates,
    state=county_states
    )

    TOOLS = "pan,box_select,lasso_select,box_zoom,wheel_zoom,undo,redo,reset,hover,save"

    p = figure(
    title="Water Demand", tools=TOOLS,
    x_axis_location=None, y_axis_location=None, plot_width=1600, plot_height=1000,
    tooltips=[
    ("Name", "@name"), ("State", "@state"), ("Power Demand", "@rate{int}"),("(Long, Lat)", "($x, $y)")
    ])
    p.grid.grid_line_color = None
    p.hover.point_policy = "follow_mouse"
    p.patches('x', 'y', source=data,
    fill_color={'field': 'rate', 'transform': color_mapper},
    fill_alpha=0.7, line_color="white", line_width=0.5)
    return file_html(p, CDN, title="power demand")
