"""
Functionality for exploring and comparing duplicate healthcare facilities in Malawi dataset.

This includes generation of an interactive map clustering facilities at similar locations

Requires duplicated_hcf dataset from src\healthcare_accessibility\data_cleaning_and_merging.py
"""

# %%
import geopandas as gpd
import healthcare_accessibility.geospatial_utils as geo_util
import yaml
from pathlib import Path
import geopandas as gpd
import folium
from sklearn.cluster import DBSCAN

import healthcare_accessibility.data_processing_funcs as dp_funcs

# %%
# Set path to data folder
config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

visualisation_crs = config.get("visualisation_crs")

analysis_crs = config.get("analysis_crs")

data_dir = Path(config.get("data_dir"))

output_dir = Path(config.get("outputs_dir"))

# %%
# Load dataframe
duplicated_gdf = gpd.read_file(
    config.get("data_dir")
    + datasets.get("health_facility").get("processed")
    + datasets.get("health_facility").get("duplicated_hcf"),
)

# %%
duplicated_gdf["Facility Name"].value_counts()

# %%
namasalima_hc = geo_util.create_distance_matrix(
    gdf=duplicated_gdf,
    facility_name="Namasalima Health Centre",
    analysis_crs=analysis_crs,
)

# %%
chilipa_gdf, chilipa_map = geo_util.compare_facility_types(
    gdf=duplicated_gdf, facility_name="Chilipa Health Centre", analysis_crs=analysis_crs
)

# %%
chilipa_map

# %% [markdown]
# Add regions

# %%
# Load OSM district boundary
openstreetmap_ADM1 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir") + datasets.get("admin_boundary").get("OSM_ADM2"),
    column_name_to_change="ADM1",
)

# Change column name for consistency
openstreetmap_ADM1.rename(columns={"name": "ADM1"}, inplace=True)

# %%
chilipa_gdf

# %%
# Create FeatureGroup for OpenStreetMap
openstreetmap_group_ADM1 = folium.FeatureGroup(name="OpenStreetMap")

for _, row in openstreetmap_ADM1.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["ADM1"],
        tooltip=row["ADM1"],  # remove potentially
        style_function=lambda x: {
            "color": "Green",  # Border color
            "weight": 1,
            "fillOpacity": 0.1,
        },
    ).add_to(openstreetmap_group_ADM1)
openstreetmap_group_ADM1.add_to(chilipa_map)

# Add layer control
folium.LayerControl().add_to(chilipa_map)

# Display the updated map
chilipa_map

# %%
# Load dataframe
duplicated_cleaned_gdf = gpd.read_file(
    config.get("data_dir")
    + datasets.get("health_facility").get("processed")
    + datasets.get("health_facility").get("cleaned_hcf")
)

# %%
compare_similar_hcf_names = dp_funcs.compare_similar_facility_names(
    gdf=duplicated_cleaned_gdf,
    desired_analysis_crs=analysis_crs,
    desired_visualisation_crs=visualisation_crs,
    radius=100,
    metric="euclidean",
    latitude=-13.2543,
    longitude=34.3015,
    output_dir=output_dir,
)
# %%
