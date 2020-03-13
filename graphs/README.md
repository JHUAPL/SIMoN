# SIMoN Granularity Graph Tool

This tool constructs the granularity graphs used for data translation in the SIMoN software application.

## Granularities

A key difficulty in combining models is resolving their data dependencies and discrepancies. By using the SIMoN software, a modeler is able to join models with disparate geographic definitions together in various combinations, allowing models to run together and exchange data that have heterogeneous definitions of geography.

SIMoN currently integrates models of population, power systems, water systems, and climate change. These domains each have their own hierarchies of geography, which include political, topographical, regulatory, and latitude-longitude grid boundaries.

In order to translate data from its models across granularities, SIMoN uses shapefiles to define rigorous geographies in a partially ordered set of geographic partitions (e.g., counties, watersheds, power regions, and latitude-longitude squares). The sample shapefiles provided in the `graphs/shapefiles` directory were clipped to the land boundary of the contiguous United States, in order to have consistent scope. The geometries were compressed / simplified using a distance-based method (the Douglas-Peucker algorithm) with a tolerance of 1 kilometer. They use [EPSG:3085](https://epsg.io/3085-1901) NAD83(HARN) / Texas Centric Albers Equal Area as their coordinate reference system.

SIMoN creates a corresponding directed acyclic network graph representing all the granularities, their corresponding entities, and their relationships to each other. The individual models feed each other updated data inputs at synchronized time intervals, and traverse the network graph to translate their data from one granularity to another. A sample granularity graph is provided, but modelers can extend it or create a graph of their own, by modifying and using the `graphs/build.py` script.

The granularities in the provided granularity graph are:
    * `usa48` (a single region for the contiguous United States)
    * `state` (49 regions: the lower 48 states plus Washington, DC)
    * `county` (3108 counties, including Washington, DC)
    * `nerc` (22 North American Electric Reliability Corporation regions)
    * `huc8` (2119 HUC 8 regions)
    * `latlon` (209 latitude-longitude grid squares)

## Aggregators and Disaggregators

The modeler can choose transformation functions, called aggregators and disaggregators, to translate data between compatible geographic definitions in various ways. These aggregators and disaggregators must conform to a set of mathematical axioms, including a partial inverse property, which are designed to create a provable notion of data consistency and reduce the possibility of self-propagating errors.

Aggregators are functions used to combine data from sibling nodes to their parent node. Disaggregators are functions used to distribute data from a node to its children.

Aggregators:
* `simple_sum`: the values of the sibling nodes are added together. The sum is the new value of their parent.
* `simple_average`: the parent's new value is the mean of the children's values.
* `weighted_average: the parent's new value is the mean of the children's values, weighted by each child's geographic area.

Disaggregators:
* `distribute_identically`: the parent node's value is assigned to each one of its children.
* `distribute_uniformly`: the parent node's value is divided evenly among each of its children.
* `distribute_by_area`: each child node is assigned a portion of the parent's value, proportional to the child's geographic area.

## Basic Usage

This tool uses shapefiles to generate two JSON graphs: an abstract graph and an instance graph.

Run `make graph` from the top-level `simon` directory.

This will start the `simon-graph` Docker container, and create an abstract graph / instance graph pair in the `graphs/out` directory. The container will exit once the graph pair has been built. To use the generated graphs for the next SIMoN run, rename the abstract graph to abstract-graph.geojson, and the instance graph to instance-graph.geojson.

## Advanced Usage

Adjust these parameters in the `graphs/config.json` file:

* `projection` is the EPSG coordinate reference system code that all of the shapefile polygons will be translated to, in order to ensure consistency. For the most precise results, use the original EPSG of the shapefiles.
* `scale_factor` divides the area of each shapefile's polygons by a scalar, in order to use better units. For example, the provided shapefiles have length units of meters and area units of square meters. The default scale_factor is 1 million, in order to translate the area unit of the provided shapefiles from square meters to square kilometers. Change the scale factor to 1 to preserve the original units.
* `minimum_intersection_area` sets the minimum area of an instance wedge node (a node that results from intersecting nodes from two different branches of the granularity graph). Because of precision errors, a minimum intersection area of 0 could result in the creation of many tiny, spurious nodes that clutter the instance graph. The default minimum intersection area is set to 1 length unit, where length unit is the length unit of the shapefiles after any scaling from the `scale_factor`.
* `abstract_edges` is the list of edges in the abstract graph, where each edge is represented by a tuple in the form [source, target]. Adjust the items in this list to create a new abstract graph. The `build.py` script will generate the corresponding instace graph by finding the corresponding shapefiles in the `graphs/shapefiles` directory.
* `save_shapes` specifies whether to create a third file that saves the large polygon shapes of the instance graph nodes.
* `tag` is the suffix attached to the abstract graph and instance graph filenames.

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
