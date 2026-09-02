"""This experimental script explores distance calculations along road networks"""

# %%
import geopandas as gpd
import r5py
import matplotlib.pyplot as plt
from pyrosm import OSM
import pandas as pd
from pathlib import Path
import yaml

import healthcare_accessibility.geospatial_utils as geo_util
import healthcare_accessibility.osm_utils as osm_util


config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

analysis_crs = config.get("analysis_crs")
visualisation_crs = config.get("visualisation_crs")

# %%

osm_util.acquire_latest_osm_data("malawi", "africa", config.get("data_dir"))

osm_file_path = config.get("data_dir") + datasets.get("osm_data").get(
    "malawi_latest_pbf"
)
# %%
# Read all drivable roads
# =======================
osm = OSM(osm_file_path)

drive_net = osm.get_network(network_type="driving")
plot_road_network = False
if plot_road_network:
    drive_net.plot()
    plt.show()


# %%

pop_grid_path = config.get("data_dir") + datasets.get("population").get("wp_2025_1km")
pop_grid_gdf = geo_util.load_and_vectorize_grid_tif(pop_grid_path)
pop_grid_gdf = geo_util.set_crs(pop_grid_gdf, "EPSG:20936")
pop_grid_gdf["id"] = pop_grid_gdf.index.astype(str)

pop_grid_centroids = geo_util.return_grid_centroids(pop_grid_gdf)

# %%

# Filter population grid centroids by the bounds of the drive network
pop_grid_cent_focus = geo_util.filter_by_bounds_of_dataset(
    pop_grid_centroids, drive_net, analysis_crs
)


# %%
transport_network = r5py.TransportNetwork(osm_file_path)

origin_grid = pop_grid_centroids.sample(1)
destination_grids = pop_grid_centroids.sample(100)

modes = [
    r5py.TransportMode.WALK,
    r5py.TransportMode.BICYCLE,
    r5py.TransportMode.CAR,
]

# iterate over each transport mode to calculate travel times
for mode in modes:
   print(f"Calculating travel times for transport mode: {mode}")

# Calculate the travel time matrix for the current mode
  travel_times = r5py.TravelTimeMatrix(
       transport_network,
       origins=origin_grid,
       destinations=destination_grids,
       transport_modes= [mode],
       snap_to_network=True,
      )


# Print the travel time matrix for the current mode
  print(f"Travel times for {mode}:")
  print(travel_times)


# %%
from geopy.distance import geodesic

origin_grid = pop_grid_centroids.sample(1)
destination_grids = pop_grid_centroids.sample(100)

print(geodesic(origin_grid, destination_grids).metres)


# %%
import osmnx as ox


# Define the area of interest (e.g., Malawi)
area_of_interest = "Malawi"

# Download the road network for driving
road_network = ox.graph_from_place(area_of_interest, network_type="drive")

# Save the road network to a file (optional)
ox.save_graphml(road_network, "malawi_road_network.graphml")


# %%
import networkx as nx
from geopy.distance import geodesic

# %%
# Define origin and destination points (latitude, longitude)
origin_point = (33.78051, -13.94131)  # Area 18 Health Centre
destination_point = (33.77561, -13.99164)  # Bwaila Hospital

# %%
nodes, edges = osm.extract_nodes_and_edges(road_network)

# Convert the road network to a NetworkX graph
G = osm.to_graph(nodes=drive_net, edges=drive_net, graph_type="networkx")


# Find the nearest nodes in the graph to the origin and destination points
origin_node = ox.distance.nearest_nodes(drive_net, X=origin_point[1], Y=origin_point[0])
destination_node = ox.distance.nearest_nodes(
    drive_net, X=destination_point[1], Y=destination_point[0]
)

# Compute the shortest path between the origin and destination nodes
shortest_path = nx.shortest_path(
    drive_net, source=origin_node, target=destination_node, weight="length"
)

# Compute the total travel distance (in meters) along the shortest path
travel_distance = sum(
    nx.get_edge_attributes(drive_net, "length")[edge]
    for edge in zip(shortest_path[:-1], shortest_path[1:])
)

# Print the travel distance in kilometers
print(f"Travel distance by car: {travel_distance / 1000:.2f} kilometers")


# %%

# Define origin and destination points (latitude, longitude)
origin_point = (-13.94131, 33.78051)  # Area 18 Health Centre
destination_point = (-13.99164, 33.77561)  # Bwaila Hospital

# Load the OSM data using pyrosm
osm = OSM(osm_file_path)

# Extract the road network for driving
road_network = osm.get_network(network_type="driving")
# Convert the road network to a NetworkX graph
G = osm.to_graph(nodes=road_network, edges=road_network, graph_type="networkx")


# Find the nearest nodes to the origin and destination points
def find_nearest_node(graph, point):
    nearest_node = None
    min_distance = float("inf")
    for node, data in graph.nodes(data=True):
        node_point = (data["y"], data["x"])  # Latitude, Longitude
        distance = geodesic(point, node_point).meters
        if distance < min_distance:
            min_distance = distance
            nearest_node = node
    return nearest_node


origin_node = find_nearest_node(G, origin_point)
destination_node = find_nearest_node(G, destination_point)

# Compute the shortest path and its distance
shortest_path = nx.shortest_path(
    G, source=origin_node, target=destination_node, weight="length"
)
travel_distance = sum(
    nx.get_edge_attributes(G, "length")[edge]
    for edge in zip(shortest_path[:-1], shortest_path[1:])
)

# Print the travel distance in kilometers
print(f"Travel distance by car: {travel_distance / 1000:.2f} kilometers")
# %%
