# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


from datetime import datetime
start = datetime.now()
print(start)

from geopandas import read_file, sjoin
import networkx as nx
from networkx.readwrite import json_graph
import geojson

import itertools
from collections import defaultdict
import uuid
import os

# where to save the graphs
save_dir = os.path.join(os.path.dirname(__file__), "out")

# where the shapefiles are stored
shapefile_dir = os.path.join(os.path.dirname(__file__), "shapefiles")

# the coordinate reference system the shapefiles are defined on
projection = 3085

# scale the areas calculated for shapefile geometries from square kilometers to square meters
scale_factor = 10**6

# the minimum area of a meet node (a node formed by the interestion of two disparate geograophic granularities), in square kilometers
minimum_intersection_area = 1

# Define the abstract graph with a list of tuples with the form (source, destination), where source is a higher lower resolution granularity that encompasses destination, a higher resolution granularity.
abstract_edges = [("usa48", "state"), ("state", "county"), ("usa48", "nerc"), ("usa48", "huc8"), ("usa48", "latlon")]

# Save the instance graph with its geometries included. This will create a very large graph.
save_shapes = False

# open the shapefiles for each granularity
states = read_file(f"{shapefile_dir}/shapefiles/simple1000_clipped_state.shp").to_crs(epsg=projection)
counties = read_file(f"{shapefile_dir}/shapefiles/simple1000_clipped_county.shp").to_crs(epsg=projection)
nercs = read_file(f"{shapefile_dir}/shapefiles/simple1000_clipped_nerc.shp").to_crs(epsg=projection)
huc8s = read_file(f"{shapefile_dir}/shapefiles/simple1000_clipped_huc8.shp").to_crs(epsg=projection)
latlons = read_file(f"{shapefile_dir}/shapefiles/simple1000_clipped_latlon.shp").to_crs(epsg=projection)

# nerc regions
nercs['country'] = nercs.apply(lambda x: 1, axis=1)
nercs['area'] = nercs.apply(lambda row: row['geometry'].area, axis=1)

# nerc shapefile has the smallest scope, so it is used to define the scope of the USA
country = nercs.dissolve(by='country',aggfunc={'area': 'sum'})
country['NAME'] = "usa48"

# counties
counties['county_polygons'] = counties.geometry.copy()
counties.geometry = counties.geometry.representative_point()
counties = sjoin(counties, states, how="inner", op='within')
counties.geometry = counties['county_polygons']
counties.drop('index_right', axis=1, inplace=True)
counties.rename(columns={'ID_left': 'ID'}, inplace=True)
counties.rename(columns={'NAME_left': 'NAME'}, inplace=True)
counties.rename(columns={'ID_right': 'parent_ID'}, inplace=True)

# latitude-longitude grid squares
latlons["parent_ID"] = "usa48"
huc8s['parent_ID'] = 'usa48'
nercs['parent_ID'] = 'usa48'
states['parent_ID'] = 'usa48'

# each shapefile should have 4 attributes: ID, NAME, parent_ID, geometry
shapefiles = {}
shapefiles["state"] = states
shapefiles["county"] = counties
shapefiles["nerc"] = nercs
shapefiles["huc8"] = huc8s
shapefiles["latlon"] = latlons

for granularity, shapefile in shapefiles.items():
    for column in ['ID', 'NAME', 'geometry', 'parent_ID']:
        if column not in shapefile.columns:
            print(f"WARNING: required column {column} not in shapefile {granularity}")

# display the graph
def draw_graph(graph, display=False):
    
    if display:
        nx.draw(graph, labels={node: node for node in graph.nodes()})
    
    print("{} nodes:".format(len(graph.nodes())))
    print("{} edges:".format(len(graph.edges())))

# construct a graph from a list of edges
def build_graph(original_edges, is_abstract=False):
    graph = nx.DiGraph()
    graph.is_abstract = is_abstract
    for edge in original_edges:
        if is_abstract:
            graph.add_edge(*edge)
        else:
            graph.add_edge(*edge)
    return graph

# returns the name of a wedge node, based on its parents
def meet(a, b):
    sort = sorted((a, b))
    return "{}^{}".format(sort[0], sort[1])

# add wedge nodes to an abstact graph
def add_abstract_wedges(abstract_graph, original_nodes):
    for combo in list(itertools.combinations(original_nodes, 2)):
        if not (nx.has_path(abstract_graph, combo[0], combo[1]) or nx.has_path(abstract_graph, combo[1], combo[0])):
            new_node = meet(combo[0], combo[1])
            abstract_graph.add_edge(combo[0], new_node)
            abstract_graph.add_edge(combo[1], new_node)

# add wedge nodes to an instance graph
def add_instance_wedges(graph, combos, instance_graph_types):

    for combo in combos:

        check_intersection = graph.nodes[combo[0]]['shape'].intersects(graph.nodes[combo[1]]['shape']) and not graph.nodes[combo[0]]['shape'].touches(graph.nodes[combo[1]]['shape'])
        if not check_intersection:
            continue
        
        try:

            shape = graph.nodes[combo[1]]['shape'].intersection(graph.nodes[combo[0]]['shape'])
            area = shape.area/scale_factor
            
            new_node = meet(combo[0], combo[1])
            if area >= minimum_intersection_area:
                graph.add_edge(combo[0], new_node)
                graph.add_edge(combo[1], new_node)
                instance_graph_types[meet(graph.nodes[combo[0]]['type'], graph.nodes[combo[1]]['type'])].append(new_node)
                graph.nodes[new_node]['shape'] = shape
                graph.nodes[new_node]['area'] = area
                graph.nodes[new_node]['type'] = meet(graph.nodes[combo[0]]['type'], graph.nodes[combo[1]]['type'])

            else:
                pass
                #print(f"{new_node} is too small to be added. area = {area}")
 
        except Exception as e:
            print("ERROR: could not calculate intersection of {} with {}: {}".format(combo[0], combo[1], e))
            if not graph.nodes[combo[0]]['shape'].is_valid:
                print(f"WARNING: {combo[0]} has invalid geometry, area = {graph.nodes[combo[0]]['shape'].area/scale_factor}")
                #graph.remove_node(combo[0])
                #print(f"removed {combo[0]} from graph")
            if not graph.nodes[combo[1]]['shape'].is_valid:
                print(f"WARNING: {combo[1]} has invalid geometry, area = {graph.nodes[combo[1]]['shape'].area/scale_factor}")
                #graph.remove_node(combo[1])
                #print(f"removed {combo[1]} from graph")

    return instance_graph_types


# construct an instance graph
def build_instance_graph(root):
    instance_graph_types = defaultdict(list)
    instance_graph = build_graph([])
    instance_graph.add_node(root, name=root, type=root, shape=None, area=None)

    abstract_nodes_bfs = [root] + [v for u, v in nx.bfs_edges(abstract_graph, root)]
    for node in abstract_nodes_bfs:
        for child in (abstract_graph.successors(node)):
            shapefile = shapefiles[child]
            for index, row in shapefile.iterrows():
                ID = str(row['ID'])
                shape = row['geometry']
                area = row['geometry'].area / scale_factor
                name = row['NAME']
                if not shape.is_valid:
                    print(f"WARNING: instance node {name} has invalid geometry. area = {area}")
                if area < minimum_intersection_area:
                    print(f"WARNING: instance node {name} is smaller than minimum intersection area. area = {area}")
                instance_graph.add_node(ID, name=name, type=child, shape=shape, area=area)
                instance_graph_types[child].append(ID)
                instance_graph.add_edge(str(row['parent_ID']), ID)
    
    instance_graph.add_node(root, name=root, type=root, shape=None, area=float(country.area)/scale_factor)
    return instance_graph, instance_graph_types

# build the abstract graph
abstract_graph = build_graph(abstract_edges, is_abstract=True)
root = list(nx.topological_sort(abstract_graph))[0]
abstract_nodes = [root] + [v for u, v in nx.bfs_edges(abstract_graph, root)]

# build the instance graph
instance_graph, instance_graph_types = build_instance_graph(root)

# add wedges to the abstract graph
add_abstract_wedges(abstract_graph, abstract_nodes)

# iterate through the abstract graph wedges, in BFS order
abstract_graph_wedges = [v for u, v in nx.bfs_edges(abstract_graph, root) if v not in abstract_nodes]
for wedge in (abstract_graph_wedges):
    l, r = wedge.split('^')

    parents = [parent for parent in abstract_graph.predecessors(wedge) if parent in abstract_graph_wedges]

    if parents:
        parent = sorted(parents, key=lambda node: len(instance_graph_types[node]))[0]

        ll, rr = parent.split('^')
        combos = []
        
        for instance in instance_graph_types[parent]:
            instance_l, instance_r = instance.split('^')
        
            if l == instance_graph.nodes[instance_l].get('type'):
                for element in instance_graph.successors(instance_r):
                    if instance_graph.nodes[element].get('type') == r:
                        combos.append((instance_l, element))
            
            elif r == instance_graph.nodes[instance_r].get('type'):
                for element in instance_graph.successors(instance_l):
                    if instance_graph.nodes[element].get('type') == l:
                        combos.append((element, instance_r))
            
            elif l == instance_graph.nodes[instance_r].get('type'):
                for element in instance_graph.successors(instance_l):
                    if instance_graph.nodes[element].get('type') == r:
                        combos.append((element, instance_r))
            
            elif r == instance_graph.nodes[instance_l].get('type'):
                for element in instance_graph.successors(instance_r):
                    if instance_graph.nodes[element].get('type') == l:
                        combos.append((instance_l, element))
            
            else:
                print(f"ERROR: no match for instance {instance}")

    else:
        combos = list(itertools.product(*[instance_graph_types[l], instance_graph_types[r]]))
    
    instance_graph_types = add_instance_wedges(instance_graph, combos, instance_graph_types)

# remove nodes without neighbors
no_neighbors = set([node[0] for node in instance_graph.nodes(data=True) if node[1]['type'] in abstract_nodes and not list(instance_graph.neighbors(node[0]))])
if no_neighbors:
    print(f"removing non-wedge nodes without children: {no_neighbors}")
for node in no_neighbors:
    print(f"removing {node}")
    instance_graph.remove_node(node)

# add metadata to the graphs
meets = ["^".join(sorted(combo)) for combo in list(itertools.combinations(abstract_nodes, 2))]
granularities = abstract_nodes + meets
counts = {granularity: len([node[1]['area'] for node in instance_graph.nodes(data=True) if node[1]['type'] == granularity]) for granularity in granularities}
areas = {granularity: sum([node[1]['area'] for node in instance_graph.nodes(data=True) if node[1]['type'] == granularity]) for granularity in granularities}
metadata = {'id': str(uuid.uuid4()), 'projection': projection, 'granularities': abstract_nodes, 'minimum_intersect_area': minimum_intersection_area, 'nodes': len(instance_graph.nodes()), 'links': len(instance_graph.edges()), 'counts': counts, 'areas': areas}
abstract_graph.graph = metadata
instance_graph.graph = metadata
print(metadata)

# save the instance graph with its geometries (very large)
if save_shapes:
    with open("{}/{}-official-instance-graph-{}-shapes_{}km_simple1km.geojson".format(save_dir, "-".join(abstract_nodes), projection, minimum_intersection_area), mode='w') as outfile:
        geojson.dump(json_graph.node_link_data(instance_graph), outfile)

# remove geometries from the instance graph (much smaller)
instance_graph_noshapes = json_graph.node_link_data(instance_graph)
for node in instance_graph_noshapes['nodes']:
    if 'shape' in node:
        del node['shape']

# save graphs to JSON files
with open("{}/abstract-graph_{}_{}_{}km_simple1km.geojson".format(save_dir, "-".join(abstract_nodes), projection, minimum_intersection_area), mode='w') as outfile:
    geojson.dump(json_graph.node_link_data(abstract_graph), outfile)
with open("{}/instance-graph_{}_{}_{}km_simple1km.geojson".format(save_dir, "-".join(abstract_nodes), projection, minimum_intersection_area), mode='w') as outfile:
    geojson.dump(instance_graph_noshapes, outfile)

print("done building graphs")
end = datetime.now()
print(end)
print(end - start)
