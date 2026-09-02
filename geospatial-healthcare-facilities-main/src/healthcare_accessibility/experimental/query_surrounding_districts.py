"""Script for extracting road networks for a district and its neighbours"""

# %%
import osmnx as ox
import healthcare_accessibility.geospatial_utils as geo_util
import healthcare_accessibility.osm_utils as osm_util
import yaml
from pathlib import Path
import requests
import pyproj
import os

# %%
# Enable certificate verification explicitly
session = requests.Session()
session.verify = True

# Pass the session to osmnx
ox.settings.requests_kwargs = {"verify": True}

# %%
# Set path to data folder
config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

visualisation_crs = config.get("visualisation_crs")

data_dir = Path(config.get("data_dir"))

output_dir = Path(config.get("outputs_dir"))

pyproj.datadir.set_data_dir(os.environ["PROJ_DATA"])


# %%
# Load district boundaries
district_boundaries_gdf = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir") + datasets.get("admin_boundary").get("OSM_ADM2"),
    column_name_to_change="District",
)

# %%
# Change column name
district_boundaries_gdf.rename(columns={"name": "District"}, inplace=True)
district_boundaries_gdf = district_boundaries_gdf.drop_duplicates(
    subset=["District", "admin_level"]
)

# %%
dowa_with_neighbours = geo_util.get_roads_for_district_and_neighbours(
    district_name="Dowa",
    district_boundaries_gdf=district_boundaries_gdf,
    country="Malawi",
    network_type="drive_service",
)

# %%
lilongwe_with_neighbours = geo_util.get_roads_for_district_and_neighbours(
    district_name="Lilongwe",
    district_boundaries_gdf=district_boundaries_gdf,
    country="Malawi",
    network_type="drive_service",
)

# %%
cleaned_lilongwe_district_with_neighbours = osm_util.clean_queried_osm_roads(
    gdf=lilongwe_with_neighbours, keep_metadata="NO"
)
