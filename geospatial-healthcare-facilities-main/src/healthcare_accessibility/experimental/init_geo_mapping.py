"""This script covers Ola's early exploratory work."""

# %%
# Import necessary libraries
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import yaml
from pyrosm import OSM
import os
import folium
from shapely.geometry import Point, Polygon, MultiPolygon

# import pyproj
import healthcare_accessibility.geospatial_utils as geo_util

# %
# %%
# Set path to folder

config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

analysis_crs = config.get("analysis_crs")
visualisation_crs = config.get("visualisation_crs")


# %%
# Loading figshare data set

figshare_gdf = geo_util.load_georeferenced_csv_or_xlsx(
    file_path=config.get("data_dir") + datasets.get("health_facility").get("figshare"),
    lat_col="Lat",
    lon_col="Long",
    sheet_name="SSA MFL",
    desired_crs=visualisation_crs,
)
# %%
# Selecting Malawi dataset from figshare df
malawi_figshare_gdf = figshare_gdf[figshare_gdf["Country"] == "Malawi"].reset_index(
    drop=True
)
malawi_figshare_gdf.head(2)

# %%
malawi_figshare_gdf["geometry"][0]

# %%
malawi_figshare_gdf.info()

# %%
malawi_figshare_gdf.isnull().sum()  # checking the null values

# %%
malawi_figshare_gdf.dropna(axis=0, inplace=True)
malawi_figshare_gdf.isnull().sum()

# %%
# visualize the health facilities points
malawi_figshare_gdf.plot()

# %%
fig, ax = plt.subplots(figsize=(8, 25))
malawi_figshare_gdf.plot(ax=ax, color="red", markersize=50)
plt.title("Health Facilities points in Malawi", fontsize=16)
plt.show()

# %%
# Loading baobab health facilities data
baobab_df = geo_util.load_georeferenced_csv_or_xlsx(
    file_path=config.get("data_dir") + datasets.get("health_facility").get("baobab"),
    lat_col="LATITUDE",
    lon_col="LONGITUDE",
    sheet_name="csv",
    desired_crs=visualisation_crs,
)
baobab_df.head(2)

# %%
baobab_df.info()

# %%
# Drop unnecessary columns
# Catchment Population (2018), Unnamed: 11, Unnamed: 12, Unnamed: 13, Unnamed: 14, Unnamed: 15, Unnamed: 16, Unnamed: 17
baobab_df.drop(
    columns=[
        "Catchment Population (2018)",
        "Unnamed: 12",
        "Unnamed: 13",
        "Unnamed: 14",
        "Unnamed: 15",
        "Unnamed: 16",
        "Unnamed: 17",
        "Unnamed: 18",
    ],
    inplace=True,
)


# %%
# Loading Malawi health facilities master list
# This data has no geometry point
master_health_data = pd.read_csv(
    config.get("data_dir") + datasets.get("health_facility").get("master_health_list")
)
master_health_data.head(2)

# %% [markdown]
# Need to rename some columns so they are the same

# %% [markdown]
# malawi_figshare_gdf has 'Facility name', 'Facility type', 'Lat' and 'Long'
# baobab_df has 'Facility Name', 'Facility Type', 'LATiTUDE' and 'LONGITUDE' so we need to rename the columns to be consistent across datasets

# %%
malawi_figshare_gdf.rename(
    columns={
        "Facility name": "Facility Name",
        "Facility type": "Facility Type",
        "Lat": "LATITUDE",
        "Long": "LONGITUDE",
    },
    inplace=True,
)
malawi_figshare_gdf.head(0)

# %%
# joining the baobab_df and malawi_figshare_gdf dataframes on each other by concatenating them
concatenated_df = pd.concat([baobab_df, malawi_figshare_gdf], axis=0, ignore_index=True)
concatenated_df[
    [
        "Facility Name",
        "Facility Type",
        "Facility Ownership",
        "Facility Location",
        "District",
        "LATITUDE",
        "LONGITUDE",
        "geometry",
    ]
]  # to returm the columns of interest


# %%
# Check for missing values in the concatenated DataFrame
concatenated_df.isnull().sum()

# %%
# Drop rows with missing values in 'Facility Name', 'LATITUDE', and 'LONGITUDE' columns
concatenated_df = concatenated_df.dropna(
    subset=["Facility Name", "LATITUDE", "LONGITUDE"]
)
concatenated_df.isnull().sum()

# %%
concatenated_df.info()

# %%
# Check for duplicates in the concatenated DataFrame
duplicates = concatenated_df[concatenated_df.duplicated()]

# Count the number of duplicate rows
num_duplicates = concatenated_df.duplicated().sum()

# Display the duplicate rows and their count
print("Number of duplicate rows:", num_duplicates)
print("Duplicate rows:")
print(duplicates)

# %%
# Check for duplicate values across specific columns
duplicate_values = concatenated_df[
    concatenated_df[["District", "Facility Name", "LATITUDE", "LONGITUDE"]].duplicated()
]
print("Duplicate values in the specified columns:")
print(duplicate_values)

# %%
duplicate_values

# %%
# Drop duplicate values across specific columns, keeping the first occurrence
concatenated_df = concatenated_df.drop_duplicates(
    subset=["District", "Facility Name", "LATITUDE", "LONGITUDE"], keep="first"
)

# Reset the index after dropping duplicates (optional)
concatenated_df.reset_index(drop=True, inplace=True)

# Display the cleaned DataFrame
print("DataFrame after dropping duplicates:")
print(concatenated_df)

# %%
concatenated_df

# %%
concatenated_df.isna().sum()

# %%
concatenated_df.columns

# %%
master_health_data.columns

# %%
master_health_data.info()

# %%
master_health_data.isna().sum()

# %% [markdown]
# There are no missing data in the Malawa Master Facility List Data

# %%
# Check for duplicates in the master_health_data DataFrame
master_health_data.duplicated().sum()

# %%
# Check for duplicate rows in the master_health_data DataFrame
dup = master_health_data[master_health_data.duplicated()]
dup

# %%
# Filter the master_data DataFrame for a specific facility name
filtered_data = master_health_data[
    master_health_data["Facility name"] == "Thandizo Private Clinic, Semak"
]
filtered_data

# %%
# Drop duplicate rows in the master_health_data DataFrame, keeping the first occurrence
master_health_data = master_health_data.drop_duplicates(keep="first")
master_health_data.duplicated().sum()


# %%
# Rename 'Facility name' to 'Facility Name' in master_health_data for consistency
master_health_data = master_health_data.rename(
    columns={"Facility name": "Facility Name"}
)
master_health_data.head(0)

# %%
# Perform the join on 'Facility Name' from concatenated_df and 'Facility name' from master_data
merged_gdf = pd.merge(
    concatenated_df[
        [
            "District",
            "Facility Name",
            "Facility Type",
            "Facility Ownership",
            "Facility Location",
            "LATITUDE",
            "LONGITUDE",
            "geometry",
        ]
    ],
    master_health_data[
        [
            "Region",
            "Zone",
            "District",
            "Facility Name",
            "Facility type",
            "Managing authority",
            "Urban/Rural",
        ]
    ],
    on="Facility Name",
    how="inner",  # Use 'inner' join to keep only matching rows
)

# Drop duplicate 'Facility name' column if needed
# merged_df.drop(columns=['Facility name'], inplace=True)

# Display the merged DataFrame
print("Merged DataFrame:")
print(merged_gdf)

# %%
merged_gdf

# %%
merged_gdf = concatenated_df.merge(master_health_data, on="Facility Name", how="inner")
len(merged_gdf)

# %%
merged_gdf = merged_gdf.drop(["geometry"], axis=1)

# %%
merged_gdf.head(0)

# %%
# Convert LATITUDE and LONGITUDE to geometry by importing function from geospatial_utils

merged_gdf = geo_util.convert_to_geometry(
    merged_gdf, latitude_col="LATITUDE", longitude_col="LONGITUDE"
)
merged_gdf = merged_gdf.set_crs(visualization_crs, inplace=True)
merged_gdf.head(2)


# %%
# Load Malawi administrative boundaries from geoBoundaries
boundary_level_0 = gpd.read_file(
    config.get("data_dir") + datasets.get("admin_boundary").get("geoboundaries_ADM0")
)
boundary_level_1 = gpd.read_file(
    config.get("data_dir") + datasets.get("admin_boundary").get("geoboundaries_ADM1")
)
boundary_level_2 = gpd.read_file(
    config.get("data_dir") + datasets.get("admin_boundary").get("geoboundaries_ADM2")
)
boundary_level_3 = gpd.read_file(
    config.get("data_dir") + datasets.get("admin_boundary").get("geoboundaries_ADM3")
)
print("Administrative Boundary Level0", boundary_level_0)
print("Administrative Boundary Level1", boundary_level_1.head(2))
print("Administrative Boundary Level2", boundary_level_2.head(2))
print("Administrative Boundary Level3", boundary_level_3.head(2))

# %%
boundary_level_1

# %%
boundary_level_2.head(3)

# %%
boundary_level_3.head(3)

# %%
boundary_level_2.columns

# %%
boundary_level_2.rename(columns={"shapeName": "District"}, inplace=True)
boundary_level_2.head(0)

# %%
boundary_level_1.rename(columns={"shapeName": "Region"}, inplace=True)
boundary_level_1.head(0)

# %%
# Ensure the geometry column contains valid shapely objects for merged_gdf
if not isinstance(merged_gdf["geometry"].iloc[0], Point):
    merged_gdf["geometry"] = merged_gdf.apply(
        lambda row: Point(row["LONGITUDE"], row["LATITUDE"]), axis=1
    )

# Ensure the geometry column contains valid shapely objects for boundary_level_1 and boundary_level_2
boundary_level_1["geometry"] = boundary_level_1["geometry"].apply(
    lambda geom: (
        Polygon(geom) if not isinstance(geom, (Polygon, MultiPolygon)) else geom
    )
)
boundary_level_2["geometry"] = boundary_level_2["geometry"].apply(
    lambda geom: (
        Polygon(geom) if not isinstance(geom, (Polygon, MultiPolygon)) else geom
    )
)

# Convert to GeoDataFrames
merged_gdf = gpd.GeoDataFrame(merged_gdf, geometry=merged_gdf["geometry"])
boundary_level_1_gdf = gpd.GeoDataFrame(
    boundary_level_1, geometry=boundary_level_1["geometry"]
)
boundary_level_2_gdf = gpd.GeoDataFrame(
    boundary_level_2, geometry=boundary_level_2["geometry"]
)

# Set CRS (Coordinate Reference System) for all GeoDataFrames
merged_gdf = merged_gdf.set_crs(visualization_crs)  # Assuming WGS84

# %%
# Plot the layers
fig, ax = plt.subplots(figsize=(12, 15))

# Plot boundary_level_1 polygons
boundary_level_1_gdf.plot(
    ax=ax, color="lightblue", edgecolor="blue", alpha=0.5, label="Boundary Level 1"
)

# Plot boundary_level_2 polygons
boundary_level_2_gdf.plot(
    ax=ax, color="lightgreen", edgecolor="green", alpha=0.5, label="Boundary Level 2"
)

# Plot concatenated_df points
merged_gdf.plot(ax=ax, color="red", markersize=10, label="Facilities (Points)")

# Add legend, title, and labels
plt.legend(loc="upper right")
plt.title("Map Visualization with Layers")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Show the map
plt.show()

# %% [markdown]
# To map coordinates for specific facilites to their administrative areas (Regions and District), spatial join would be done to check weather the coordinates are contained within a boundary polygon.

# %%
# Mapping the Facilities to their respective boundaries (Regions and Districts)
# Perform spatial join with boundary_level_1_gdf
merged_with_boundary_level_1 = gpd.sjoin(
    merged_gdf,
    boundary_level_1_gdf[["Region", "geometry"]],
    how="left",
    predicate="within",
    lsuffix="left",
    rsuffix="boundary1",
)

# Perform spatial join with boundary_level_2_gdf
merged_with_boundaries = gpd.sjoin(
    merged_with_boundary_level_1,
    boundary_level_2_gdf[["District", "geometry"]],
    how="left",
    predicate="within",
    lsuffix="left",
    rsuffix="boundary2",
)

# Inspect the result
print(merged_with_boundaries.head())

# %%
merged_with_boundaries.head(2)

# %%
complete_gdf = merged_with_boundaries[
    [
        "Facility Name",
        "Facility Type",
        "Facility Ownership",
        "District",
        "Region_boundary1",
        "LATITUDE",
        "LONGITUDE",
        "geometry",
    ]
]
complete_gdf.head(5)

# %%
complete_gdf = complete_gdf.rename(columns={"Region_boundary1": "Region"})
complete_gdf.head(2)

# %%
complete_gdf.info()

# %%
complete_gdf.explore()

# %%
# Create a folium map centered on the data
center_lat = complete_gdf["LATITUDE"].mean()
center_lon = complete_gdf["LONGITUDE"].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=8)

# Define a color mapping for regions
region_colors = {
    "Southern Region": "blue",
    "Central Region": "green",
    "Northern Region": "orange",
}

# Add boundary_level_1 (regions) as a GeoJSON layer with dynamic colors
folium.GeoJson(
    boundary_level_1_gdf,
    name="Regions",
    style_function=lambda x: {
        "fillColor": region_colors.get(
            x["properties"]["Region"], "gray"
        ),  # Default to gray if region not in mapping
        "color": region_colors.get(x["properties"]["Region"], "gray"),
        "weight": 1,
        "fillOpacity": 0.3,
    },
    tooltip=folium.GeoJsonTooltip(fields=["Region"], aliases=["Region:"]),
).add_to(m)

# Add boundary_level_2 (districts) as a GeoJSON layer
folium.GeoJson(
    boundary_level_2_gdf,
    name="Districts",
    style_function=lambda x: {
        "fillColor": "lightgray",
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.3,
    },
    tooltip=folium.GeoJsonTooltip(fields=["District"], aliases=["District:"]),
).add_to(m)

# Add facilities as markers with popups
for _, row in complete_gdf.iterrows():
    folium.Marker(
        location=[row["LATITUDE"], row["LONGITUDE"]],
        popup=f"Facility Name: {row['Facility Name']}<br>Facility Type: {row['Facility Type']}<br>Region: {row['Region']}<br>District: {row['District']}",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)

# Add layer control to toggle layers
folium.LayerControl().add_to(m)

# Display the map
m.save("map.html")
m

# %% [markdown]
# The map shows the health facilities in distrticts and regions of Malawi
#

# %%
