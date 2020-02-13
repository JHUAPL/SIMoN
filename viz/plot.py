#!/usr/bin/env python
# coding: utf-8

# Plot data on a choropleth map

# import packages
import sys
import numpy as np
from geopandas import read_file
import pandas as pd
import json
from bokeh.io import show
from bokeh.models import LogColorMapper
from bokeh.palettes import Blues256 as palette
palette.reverse()
from bokeh.plotting import figure, output_file, save

# parameters
json_file = sys.argv[1]  # path to the Mongo document to plot
shapefile_dir = "../graphs/shapefiles/"  # path to the directory of shapefiles
plot_width = 1200  # pixel width of the plot
plot_height = 800  # pixel height of the plot
projection = 4326  # coordinate reference system to use for plotting

# geopandas functions for getting coordinates
# references:
# https://automating-gis-processes.github.io/2016/Lesson5-interactive-map-bokeh.html
# https://discourse.bokeh.org/t/mapping-europe-with-bokeh-using-geopandas-and-handling-multipolygons/2571

def getXYCoords(geometry, coord_type):
    # Returns either x or y coordinates from geometry coordinate sequence. Used with LineString and Polygon geometries."""
    if coord_type == 'x':
        return list(geometry.coords.xy[0])
    elif coord_type == 'y':
        return list(geometry.coords.xy[1])


def getPolyCoords(geometry, coord_type):
    # Returns Coordinates of Polygon using the Exterior of the Polygon."""
    ext = geometry.exterior
    return getXYCoords(ext, coord_type)


def multiGeomHandler(multi_geometry, coord_type, geom_type):
    """
    Function for handling multi-geometries. Can be MultiPoint, MultiLineString or MultiPolygon.
    Returns a list of coordinates where all parts of Multi-geometries are merged into a single list.
    Individual geometries are separated with np.nan which is how Bokeh wants them.
    # Bokeh documentation regarding the Multi-geometry issues can be found here (it is an open issue)
    # https://github.com/bokeh/bokeh/issues/2321
    """

    for i, part in enumerate(multi_geometry):
        # On the first part of the Multi-geometry initialize the coord_array (np.array)
        if i == 0:
            if geom_type == "MultiPoint":
                coord_arrays = np.append(
                    getPointCoords(part, coord_type), np.nan
                )
            elif geom_type == "MultiLineString":
                coord_arrays = np.append(
                    getLineCoords(part, coord_type), np.nan
                )
            elif geom_type == "MultiPolygon":
                coord_arrays = np.append(
                    getPolyCoords(part, coord_type), np.nan
                )
        else:
            if geom_type == "MultiPoint":
                coord_arrays = np.concatenate(
                    [
                        coord_arrays,
                        np.append(getPointCoords(part, coord_type), np.nan),
                    ]
                )
            elif geom_type == "MultiLineString":
                coord_arrays = np.concatenate(
                    [
                        coord_arrays,
                        np.append(getLineCoords(part, coord_type), np.nan),
                    ]
                )
            elif geom_type == "MultiPolygon":
                coord_arrays = np.concatenate(
                    [
                        coord_arrays,
                        np.append(getPolyCoords(part, coord_type), np.nan),
                    ]
                )

    # Return the coordinates
    return coord_arrays


def get_coords(row, coord_type):
    """Returns the coordinates ('x' or 'y') of edges of a Polygon exterior"""
    try:
        # plot a single polygon
        return getPolyCoords(row['geometry'], coord_type)
    except Exception as e:
        # plot multiple polygons
        return multiGeomHandler(row['geometry'], coord_type, 'MultiPolygon')


# plot data on the shapefile
# references:
# https://docs.bokeh.org/en/latest/docs/gallery/texas.html
def plot_mongo_doc(data, projection=4326, save_fig=True, show_fig=True):

    df = {}
    geographies = {}
    datasets = data['payload'].keys()

    for dataset in datasets:

        granularity = data['payload'][dataset]['granularity']
        print(f"dataset: {dataset}, granularity: {granularity}")
        instance_col_name = 'ID'
        year = data['year']

        df[dataset] = pd.DataFrame.from_dict(
            data['payload'][dataset]['data'],
            orient='index',
            columns=[f"{dataset}_value"],
        )
        df[dataset][instance_col_name] = df[dataset].index

        geographies[dataset] = read_file(
            f"{shapefile_dir}/simple1000_clipped_{granularity}.shp"
        ).to_crs(epsg=projection)
        geographies[dataset] = geographies[dataset].merge(
            df[dataset], on=instance_col_name
        )

        # reset the color palette
        color_mapper = LogColorMapper(palette=palette)

        geographies[dataset]['x'] = geographies[dataset].apply(
            get_coords, coord_type='x', axis=1
        )
        geographies[dataset]['y'] = geographies[dataset].apply(
            get_coords, coord_type='y', axis=1
        )

        plot_data = dict(
            x=geographies[dataset]['x'].tolist(),
            y=geographies[dataset]['y'].tolist(),
            name=geographies[dataset]['ID'].tolist(),
            value=geographies[dataset][f"{dataset}_value"].tolist(),
        )

        TOOLS = "pan,wheel_zoom,reset,hover,save,box_zoom"

        coords_tuple = (
            ("(Lat, Lon)", "($y, $x)")
            if projection == 4326
            else ("(x, y)", "($x, $y)")
        )
        fig = figure(
            title=f"USA {dataset} ({year})",
            tools=TOOLS,
            plot_width=plot_width,
            plot_height=plot_height,
            x_axis_location=None,
            y_axis_location=None,
            tooltips=[("Name", "@name"), ("Value", "@value"), coords_tuple],
        )
        fig.grid.grid_line_color = None
        fig.hover.point_policy = "follow_mouse"

        fig.patches(
            'x',
            'y',
            source=plot_data,
            fill_color={'field': 'value', 'transform': color_mapper},
            fill_alpha=0.7,
            line_color="white",
            line_width=0.5,
        )

        if save_fig:
            output_file(f"{year}_{dataset}.html")
            save(fig)
        if show_fig:
            show(fig)


# load and plot the data
with open(json_file) as f:
    data = json.load(f)

plot_mongo_doc(data, projection=projection, show_fig=False)
