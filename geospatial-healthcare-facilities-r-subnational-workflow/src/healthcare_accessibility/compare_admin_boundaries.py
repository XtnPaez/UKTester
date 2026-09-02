# %%
# Packages
import folium
import matplotlib.pyplot as plt
from pathlib import Path
import yaml
import healthcare_accessibility.geospatial_utils as geo_util


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


# %% [markdown]
# Load boundaries - ADM0

# %%
diva_gis_ADM0 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("diva_gis_ADM0"),
    column_name_to_change="Country",
)

gadm_ADM0 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("gadm41_ADM0"),
    column_name_to_change="Country",
)

geoboundaries_ADM0 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("geoboundaries_ADM0"),
    column_name_to_change="Country",
)

# %%
# Create subplots
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Plot each GeoDataFrame
diva_gis_ADM0.plot(ax=axes[0], edgecolor="Black", color="Purple")
axes[0].set_title("Diva GIS ADM0")
axes[0].axis("off")

geoboundaries_ADM0.plot(ax=axes[1], edgecolor="black", color="Blue")
axes[1].set_title("GeoBoundaries ADM0")
axes[1].axis("off")

gadm_ADM0.plot(ax=axes[2], edgecolor="black", color="Red")
axes[2].set_title("GADM ADM0")
axes[2].axis("off")

# Adjust layout
plt.tight_layout()
plt.show()

# %%
# Create base map geoboundaries, location is Malawi
map_ADM0 = folium.Map(location=[-13.2543, 34.3015], tiles="OpenStreetMap", zoom_start=9)

# %%
# Create FeatureGroup for ADM0 DIVA GIS
diva_gis_group = folium.FeatureGroup(name="DIVA GIS")

for _, row in diva_gis_ADM0.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["Country"],
        tooltip=row["Country"],  # remove potentially
        style_function=lambda x: {  # Light blue
            "color": "purple",  # Border color
            "weight": 1,
            "fillOpacity": 0.1,
        },
    ).add_to(diva_gis_group)
diva_gis_group.add_to(map_ADM0)

# Create FeatureGroup for ADM0 DIVA GIS
geoboundaries_group = folium.FeatureGroup(name="Geoboundaries")

for _, row in geoboundaries_ADM0.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["Country"],
        tooltip=row["Country"],  # remove potentially
        style_function=lambda x: {
            "color": "blue",  # Border color
            "weight": 1,
            "fillOpacity": 0.1,
        },
    ).add_to(geoboundaries_group)
geoboundaries_group.add_to(map_ADM0)

# Create FeatureGroup for ADM0 DIVA GIS
gadm_group = folium.FeatureGroup(name="GADM")

for _, row in gadm_ADM0.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["Country"],
        tooltip=row["Country"],  # remove potentially
        style_function=lambda x: {
            "color": "Orange",  # Border color
            "weight": 1,
            "fillOpacity": 0.1,
        },
    ).add_to(gadm_group)
gadm_group.add_to(map_ADM0)

# Add layer control
folium.LayerControl().add_to(map_ADM0)

map_ADM0

# %% [markdown]
# Load boundaries - ADM1

# %%
diva_gis_ADM1 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("diva_gis_ADM1"),
    column_name_to_change="ADM1",
)

gadm_ADM1 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("gadm41_ADM1"),
    column_name_to_change="ADM1",
)

geoboundaries_ADM1 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get(
        "geoboundaries_ADM2"
    ),  # ADM2 in geoboundaries not ADM1
    column_name_to_change="ADM1",
)

openstreetmap_ADM1 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir") + datasets.get("admin_boundary").get("OSM_ADM2"),
    column_name_to_change="ADM1",
)

# %%
# Change column name for consistency
openstreetmap_ADM1.rename(columns={"name": "ADM1"}, inplace=True)

# Drop unneeded column for consistency
# openstreetmap_ADM1.drop(columns=['admin_level'], axis=1, inplace=True)

# %%
# Create subplots
fig, axes = plt.subplots(1, 4, figsize=(24, 6))

# Plot each GeoDataFrame
diva_gis_ADM1.plot(ax=axes[0], edgecolor="Black", color="Purple")
axes[0].set_title("Diva GIS ADM1")
axes[0].axis("off")

geoboundaries_ADM1.plot(ax=axes[1], edgecolor="black", color="Blue")
axes[1].set_title("GeoBoundaries ADM1")
axes[1].axis("off")

gadm_ADM1.plot(ax=axes[2], edgecolor="black", color="Red")
axes[2].set_title("GADM ADM1")
axes[2].axis("off")

openstreetmap_ADM1.plot(ax=axes[3], edgecolor="black", color="Green")
axes[3].set_title("OSM ADM1")
axes[3].axis("off")

# Adjust layout
plt.tight_layout()
plt.show()

# %% [markdown]
# ADM1 is different for geoboundaries...is more Regions

# %%
# Create base map geoboundaries, location is Malawi
map_ADM1 = folium.Map(location=[-13.2543, 34.3015], tiles="OpenStreetMap", zoom_start=9)

# %%
# Create FeatureGroup for DIVA GIS
diva_gis_group_ADM1 = folium.FeatureGroup(name="DIVA GIS")

for _, row in diva_gis_ADM1.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["ADM1"],
        tooltip=row["ADM1"],  # remove potentially
        style_function=lambda x: {  # Light blue
            "color": "purple",  # Border color
            "weight": 1,
            "fillOpacity": 0.1,
        },
    ).add_to(diva_gis_group_ADM1)
diva_gis_group_ADM1.add_to(map_ADM1)

# Create FeatureGroup for geoboundaries
geoboundaries_group_ADM1 = folium.FeatureGroup(name="Geoboundaries")

for _, row in geoboundaries_ADM1.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["ADM1"],
        tooltip=row["ADM1"],  # remove potentially
        style_function=lambda x: {
            "color": "blue",  # Border color
            "weight": 1,
            "fillOpacity": 0.1,
        },
    ).add_to(geoboundaries_group_ADM1)
geoboundaries_group_ADM1.add_to(map_ADM1)

# Create FeatureGroup for DIVA GIS
gadm_group_ADM1 = folium.FeatureGroup(name="GADM")

for _, row in gadm_ADM1.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["ADM1"],
        tooltip=row["ADM1"],  # remove potentially
        style_function=lambda x: {
            "color": "Orange",  # Border color
            "weight": 1,
            "fillOpacity": 0.1,
        },
    ).add_to(gadm_group_ADM1)
gadm_group_ADM1.add_to(map_ADM1)

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
openstreetmap_group_ADM1.add_to(map_ADM1)

# Add layer control
folium.LayerControl().add_to(map_ADM1)

map_ADM1

# %% [markdown]
# Load boundaries ADM2

# %%
diva_gis_ADM2 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("diva_gis_ADM2"),
    column_name_to_change="ADM2",
)

gadm_ADM2 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("gadm41_ADM2"),
    column_name_to_change="ADM2",
)

geoboundaries_ADM2 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get(
        "geoboundaries_ADM3"
    ),  # ADM3 in geoboundaries not ADM2
    column_name_to_change="ADM2",
)

# %%
# Create subplots
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Plot each GeoDataFrame
diva_gis_ADM2.plot(ax=axes[0], edgecolor="Black", color="Purple")
axes[0].set_title("Diva GIS ADM2")
axes[0].axis("off")

geoboundaries_ADM2.plot(ax=axes[1], edgecolor="black", color="Blue")
axes[1].set_title("GeoBoundaries ADM2 (named ADM3)")
axes[1].axis("off")

gadm_ADM2.plot(ax=axes[2], edgecolor="black", color="Red")
axes[2].set_title("GADM ADM2")
axes[2].axis("off")

# Adjust layout
plt.tight_layout()
plt.show()

# %%
# Create base map geoboundaries, location is Malawi
map_ADM2 = folium.Map(location=[-13.2543, 34.3015], tiles="OpenStreetMap", zoom_start=9)

# %%
# Create FeatureGroup for DIVA GIS
diva_gis_group_ADM2 = folium.FeatureGroup(name="DIVA GIS")

for _, row in diva_gis_ADM2.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["ADM2"],
        tooltip=row["ADM2"],  # remove potentially
        style_function=lambda x: {  # Light blue
            "color": "purple",  # Border color
            "weight": 1,
            "fillOpacity": 0.1,
        },
    ).add_to(diva_gis_group_ADM2)
diva_gis_group_ADM2.add_to(map_ADM2)

# Create FeatureGroup for Geoboundaries
geoboundaries_group_ADM2 = folium.FeatureGroup(name="Geoboundaries")

for _, row in geoboundaries_ADM2.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["ADM2"],
        tooltip=row["ADM2"],  # remove potentially
        style_function=lambda x: {
            "color": "blue",  # Border color
            "weight": 1,
            "fillOpacity": 0.1,
        },
    ).add_to(geoboundaries_group_ADM2)
geoboundaries_group_ADM2.add_to(map_ADM2)

# Create FeatureGroup for GADM
gadm_group_ADM2 = folium.FeatureGroup(name="GADM")

for _, row in gadm_ADM2.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["ADM2"],
        tooltip=row["ADM2"],  # remove potentially
        style_function=lambda x: {
            "color": "Orange",  # Border color
            "weight": 1,
            "fillOpacity": 0.1,
        },
    ).add_to(gadm_group_ADM2)
gadm_group_ADM2.add_to(map_ADM2)

# Add layer control
folium.LayerControl().add_to(map_ADM2)

map_ADM2

# %% [markdown]
# Load boundaries ADM3

# %%
diva_gis_ADM3 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("diva_gis_ADM3"),
    column_name_to_change="ADM3",
)

gadm_ADM3 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("gadm41_ADM3"),
    column_name_to_change="ADM3",
)

# %%
# Create subplots
fig, axes = plt.subplots(1, 2, figsize=(12, 6))

# Plot each GeoDataFrame
diva_gis_ADM3.plot(ax=axes[0], edgecolor="Black", color="Purple")
axes[0].set_title("Diva GIS ADM3")
axes[0].axis("off")

gadm_ADM3.plot(ax=axes[1], edgecolor="black", color="Red")
axes[1].set_title("GADM ADM3")
axes[1].axis("off")

# Adjust layout
plt.tight_layout()
plt.show()

# %%
# Create base map geoboundaries, location is Malawi
map_ADM3 = folium.Map(location=[-13.2543, 34.3015], tiles="OpenStreetMap", zoom_start=9)

# %%
# Create FeatureGroup for ADM3 DIVA GIS
diva_gis_group_ADM3 = folium.FeatureGroup(name="DIVA GIS")

for _, row in diva_gis_ADM3.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["ADM3"],
        tooltip=row["ADM3"],  # remove potentially
        style_function=lambda x: {  # Light blue
            "color": "blue",  # Border color
            "weight": 2,
            "fillOpacity": 0.1,
        },
    ).add_to(diva_gis_group_ADM3)
diva_gis_group_ADM3.add_to(map_ADM3)

# Create FeatureGroup for ADM3 GADM
gadm_group_ADM3 = folium.FeatureGroup(name="GADM")

for _, row in gadm_ADM3.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["ADM3"],
        tooltip=row["ADM3"],  # remove potentially
        style_function=lambda x: {
            "color": "red",  # Border color
            "weight": 2,
            "fillOpacity": 0.1,
        },
    ).add_to(gadm_group_ADM3)
gadm_group_ADM3.add_to(map_ADM3)

# Add layer control
folium.LayerControl().add_to(map_ADM3)

map_ADM3
