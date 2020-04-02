# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import click
import sys
import os
import numpy as np
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from geopandas import read_file
import pandas as pd
import json
from bokeh.io import show
from bokeh.models import LogColorMapper
from bokeh.palettes import Blues256 as palette

palette.reverse()
from bokeh.plotting import figure, output_file, save


# geopandas functions for getting coordinates
# references:
# https://automating-gis-processes.github.io/2016/Lesson5-interactive-map-bokeh.html
# https://discourse.bokeh.org/t/mapping-europe-with-bokeh-using-geopandas-and-handling-multipolygons/2571


def get_xy_coords(geometry, coord_type):
    """
    Returns either x or y coordinates from geometry coordinate sequence. Used with Polygon geometries.
    """
    if coord_type == "x":
        return list(geometry.coords.xy[0])
    elif coord_type == "y":
        return list(geometry.coords.xy[1])


def get_poly_coords(geometry, coord_type):
    """
    Returns Coordinates of Polygon using the Exterior of the Polygon
    """
    return get_xy_coords(geometry.exterior, coord_type)


def multi_geom_handler(multi_geometry, coord_type):
    """
    Function for handling MultiPolygon geometries.
    Returns a list of coordinates where all parts of Multi-geometries are merged into a single list.
    Individual geometries are separated with np.nan which is how Bokeh wants them.
    Bokeh documentation regarding the Multi-geometry issues can be found here (it is an open issue).
    https://github.com/bokeh/bokeh/issues/2321
    """
    all_poly_coords = [
        np.append(get_poly_coords(part, coord_type), np.nan)
        for part in multi_geometry
    ]
    coord_arrays = np.concatenate(all_poly_coords)
    return coord_arrays


def get_coords(row, coord_type):
    """
    Returns the coordinates ('x' or 'y') of edges of a Polygon exterior
    """
    poly_type = type(row["geometry"])

    # get coords from a single polygon
    if poly_type == Polygon:
        return get_poly_coords(row["geometry"], coord_type)
    # get coords from multiple polygons
    elif poly_type == MultiPolygon:
        return multi_geom_handler(row["geometry"], coord_type)


# plot data on the shapefile
# references:
# https://docs.bokeh.org/en/latest/docs/gallery/texas.html
def plot_mongo_doc(
    data,
    shapefile_dir=".",
    projection=4326,
    plot_width=1200,
    plot_height=800,
    show_fig=False,
    save_fig=True,
):

    df = {}
    geographies = {}
    datasets = data["payload"].keys()

    for dataset in datasets:

        granularity = data["payload"][dataset]["granularity"]
        if not granularity:
            print(
                f"skipping {dataset} (does not have a granularity specified)"
            )
            continue
        else:
            print(f"plotting {dataset} (granularity: {granularity})")
        instance_col_name = "ID"
        year = data["year"]
        unit = data["payload"][dataset]["unit"]

        df[dataset] = pd.DataFrame.from_dict(
            data["payload"][dataset]["data"],
            orient="index",
            columns=[f"{dataset}_value"],
        )
        df[dataset][instance_col_name] = df[dataset].index

        shapefile_path = f"{shapefile_dir}/{granularity}.shp"
        if os.path.exists(shapefile_path):
            geographies[dataset] = read_file(shapefile_path).to_crs(
                epsg=projection
            )
        else:
            print(f"{shapefile_path} not found, skipping")
            continue
        geographies[dataset] = geographies[dataset].merge(
            df[dataset], on=instance_col_name
        )

        # reset the color palette
        color_mapper = LogColorMapper(palette=palette)

        geographies[dataset]["x"] = geographies[dataset].apply(
            get_coords, coord_type="x", axis=1
        )
        geographies[dataset]["y"] = geographies[dataset].apply(
            get_coords, coord_type="y", axis=1
        )

        plot_data = dict(
            x=geographies[dataset]["x"].tolist(),
            y=geographies[dataset]["y"].tolist(),
            name=geographies[dataset]["NAME"].tolist(),
            identifier=geographies[dataset]["ID"].tolist(),
            value=geographies[dataset][f"{dataset}_value"].tolist(),
        )

        TOOLS = "pan,wheel_zoom,reset,hover,save,box_zoom"

        coords_tuple = (
            ("(Lat, Lon)", "($y, $x)")
            if projection == 4326
            else ("(x, y)", "($x, $y)")
        )
        title = f"{dataset} ({unit}, {year})" if unit else f"{dataset} ({year})"
        fig = figure(
            title=title,
            tools=TOOLS,
            plot_width=plot_width,
            plot_height=plot_height,
            x_axis_location=None,
            y_axis_location=None,
            tooltips=[
                ("Name", "@name"),
                ("ID", "@identifier"),
                ("Value", "@value{(0.000 a)}"),
                coords_tuple,
            ],
        )
        fig.grid.grid_line_color = None
        fig.hover.point_policy = "follow_mouse"

        fig.patches(
            "x",
            "y",
            source=plot_data,
            fill_color={"field": "value", "transform": color_mapper},
            fill_alpha=0.7,
            line_color="white",
            line_width=0.5,
        )

        if save_fig:
            output_file(f"{year}_{dataset}.html")
            save(fig)
        if show_fig:
            show(fig)


@click.command()
@click.option(
    "--data",
    type=click.Path(),
    required=True,
    help="path to the JSON file created by export.sh",
)
@click.option(
    "--shapefile_dir",
    type=click.Path(),
    default=os.path.join(
        os.path.dirname(__file__), os.pardir, "graphs", "shapefiles"
    ),
    help="path to the directory of shapefiles",
)
@click.option(
    "--projection",
    default=4326,
    help="coordinate reference system to use for plotting",
)
@click.option("--width", default=1200, help="pixel width of the plot")
@click.option("--height", default=800, help="pixel height of the plot")
@click.option(
    "--show", type=click.BOOL, default=False, help="display the plot"
)
@click.option(
    "--save", type=click.BOOL, default=True, help="write the plot to a file"
)
def main(data, shapefile_dir, projection, width, height, show, save):

    # load the data
    with open(data) as f:
        data_dict = json.load(f)

    # plot the data
    plot_mongo_doc(
        data_dict,
        shapefile_dir=shapefile_dir,
        projection=projection,
        plot_width=width,
        plot_height=height,
        show_fig=show,
        save_fig=save,
    )


if __name__ == "__main__":
    main()
