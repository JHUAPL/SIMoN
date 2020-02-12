# SIMoN Granularity Graph Tool

Build granularity graphs used for data translation in the SIMoN software application.

Copyright 2020 The Johns Hopkins University Applied Physics Laboratory
Licensed under the MIT License

## Description

This tool uses shapefiles to generate two JSON graphs: an abstract graph and an instance graph.

To use the generated graphs, rename the abstract graph to abstract-graph.geojson, and the instance graph to instance-graph.geojson.

Then place these two files in the graphs/ directory so that SIMoN will use them.

Both JSON graphs have 3 key attributes:
* `nodes` maps to a list of the graph's vertices
* `links` maps to a list of the graph's edges
* `graph` maps to a dictionary of the graph's metadata
    * `id` is a UUID for the abstract-instance graph pair, that both the abstract graph and the corresponding instance graph share
    * `projection` is the coordinate reference system that the shapefile geometries are defined on
    * `granularities` are the granularities that the graphs connect
    * `min_intersect_area` is the minimum area of a wedge node in the instance graph (a node made by intersecting disparate geographic granularities)
    * `nodes` is the number of vertices in the graph
    * `links` is the number of edges in the graph
    * `counts` is the number of vertices in the graph, categorized by granularity
    * `areas` is the total area of each granularity's scope, that is, the sum of all the node areas of each granularity. Ideally, these areas should be equal so that the graph will have a consistent scope.

## Installation

1. install `libspatialindex`
    a. install `make`, `cmake`, and a compiler (`g++` or `gcc`)
    b. `wget` https://github.com/libspatialindex/libspatialindex/releases/download/1.9.3/spatialindex-src-1.9.3.tar.gz
    c. `tar xfvz spatialindex-src-1.9.3.tar.gz`
    d. `cd spatialindex-src-1.9.3`
    e. `cmake -DCMAKE_INSTALL_PREFIX=/home/username .`
    f. `make`
    g. `make install`

2. install Python packages
    a. `pip install -r requirements.txt`

3. test installation
    a. `export LD_LIBRARY_PATH=/home/username/lib`
    b. `python test_installation.py`
