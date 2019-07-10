#!/usr/bin/env python
# coding: utf-8

import sys

# Pandas for data management
import pandas as pd
import bokeh
import math
import numpy as np
from bokeh.plotting import figure
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.palettes import RdYlBu
from bokeh.palettes import brewer
from bokeh.transform import linear_cmap
from bokeh.palettes import Spectral6
from bokeh.models import LinearColorMapper, LinearAxis
from bokeh.layouts import widgetbox
from bokeh.models.widgets import Dropdown
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import HoverTool
from bokeh.models.ranges import Range1d
import matplotlib
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap

TOOLS = "pan, box_zoom, wheel_zoom, undo, redo, reset, hover, save"

class CivilConflict:

    def __init__(self):
        self.country_name = 'Uganda'
        self.country_code = 500

    ##### plotting 5: normalized gdp per capita vs year, for major and minor, correct custom mapper
    def plot_data(self, diffs, years, major=0):

        norm_diffs = diffs

        if major:
            gdp_diff = diffs
            list_y = norm_diffs * 1000
            sh = -1.48*gdp_diff
            expected_no_deaths = (-1.48) *gdp_diff *1000
        else:
            gdp_diff = diffs
            sh = gdp_diff * (-2.55)
            expected_no_deaths = (-2.55) *gdp_diff *25

        #generate custom colormap
        bottom = cm.get_cmap('Oranges', 128)
        top = cm.get_cmap('Blues_r', 128)
        newcolors = np.vstack((top(np.linspace(0, 1, 128)),
                                   bottom(np.linspace(0, 1, 128))))
        newcmp = ListedColormap(newcolors, name='OrangeBlue')
        hex_colors = []
        for color in newcolors:
            hex_colors.append(matplotlib.colors.to_hex(color))


        source = bokeh.plotting.ColumnDataSource(data=dict(x=years, y=expected_no_deaths, gdp=gdp_diff, desc=sh))

        TOOLTIPS = [
            ("year", "@x"),
            ("expected_no_deaths", "@y{int}"),
            ('diff in gdp/capita', '@gdp{0.000%}'),
            ('reported conflicts', '@conflicts_r')
        ]
        mapper = LinearColorMapper(palette=hex_colors, low=-.25, high=0.25)

        
        #set up the figure
        p = figure(plot_width=1000, plot_height=800, title='Expected change in number of deaths per year compared to no GDP growth for %s' %self.country_name, tools=TOOLS, tooltips=TOOLTIPS)
        p.xaxis.axis_label = 'Year t ({}-{})'.format(int(years[0]), int(years[-1]))
        p.yaxis.axis_label = 'Loss of Life'
        p.title.text_font_size = '16pt'
        p.xaxis.axis_label_text_font_size = "20pt"
        p.yaxis.axis_label_text_font_size = "20pt"
        #p.yaxis.axis_label = 'Difference in GDP per capita between year t and t-1 (current US $)'
        p.vbar(x ='x', top ='y', width=0.9, source=source,
                 fill_color=bokeh.transform.transform('desc', mapper))
        
        return p


    def run(self, country_gdps, years):

        p = self.plot_data(np.array(country_gdps), years, major=1)
        tab1 = Panel(child=p, title="major conflict")

        p2 = self.plot_data(np.array(country_gdps), years)
        tab2 = Panel(child=p2, title="all conflict")

        tabs = Tabs(tabs=[ tab1, tab2 ])

        html = file_html(tabs, CDN, title="civil conflict")
        html = html.encode()
        return html
