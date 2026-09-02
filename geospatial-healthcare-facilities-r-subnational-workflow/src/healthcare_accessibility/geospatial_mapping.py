# %%
# Import packages
import folium
import geopandas as gpd
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

# %%
# Load dataframe
geo_df = gpd.read_file(
    config.get("data_dir") + datasets.get("health_facility").get("cleaned_hcf")
)

# %%
# Add "_" to column names
geo_df.columns = geo_df.columns.str.replace(" ", "_")

# %% [markdown]
# # Folium Map

# %%
# Create base map OSM
# Location is Malawi
map = folium.Map(location=[-13.2543, 34.3015], tiles="OpenStreetMap", zoom_start=9)

# map

# %% [markdown]
# Add Regions

# %%
# Use imported function
malawi_regions = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("geoboundaries_ADM1"),
    column_name_to_change="Region",
)

# Remove the word "Region" from the 'location' column
malawi_regions["Region"] = (
    malawi_regions["Region"].str.replace("Region", "", regex=False).str.strip()
)

# %%
# Assign a color to each region
colours_for_region = ["red", "blue", "yellow"]

# Assign a color to each region
malawi_regions["colour"] = colours_for_region

# %%
# Add each region as a colored GeoJson layer

# Create FeatureGroup for regions
regions_group = folium.FeatureGroup(name="Regions")

for _, row in malawi_regions.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["Region"],
        style_function=lambda feature, colour=row["colour"]: {
            "fillColor": colour,
            "color": colour,
            "weight": 2,
            "fillOpacity": 0.5,
        },
        tooltip=row["Region"],  # remove potentially
    ).add_to(regions_group)
regions_group.add_to(map)

# map

# %% [markdown]
# Add Districts

# %%
# Use imported function to load geodataframe
districts_of_malawi = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("geoboundaries_ADM2"),
    column_name_to_change="District",
)

# %%
# Assign colours for districts

colours_for_districts = [
    "red",
    "blue",
    "green",
    "yellow",
    "orange",
    "purple",
    "pink",
    "cyan",
    "magenta",
    "lime",
    "teal",
    "indigo",
    "violet",
    "turquoise",
    "coral",
    "salmon",
    "gold",
    "silver",
    "bronze",
    "maroon",
    "navy",
    "olive",
    "aquamarine",
    "chartreuse",
    "crimson",
    "plum",
    "orchid",
    "azure",
]

# %%
# Assign a colour to each region
districts_of_malawi["colour"] = colours_for_districts

# %%
# Create FeatureGroup for districts
districts_group = folium.FeatureGroup(name="Districts")

# Add each district as a coloured GeoJson layer
for _, row in districts_of_malawi.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["District"],
        style_function=lambda feature, colour=row["colour"]: {
            "fillColor": colour,
            "color": colour,
            "weight": 2,
            "fillOpacity": 0.5,
        },
        tooltip=row["District"],  # remove potentially
    ).add_to(districts_group)
districts_group.add_to(map)

# map

# %% [markdown]
# Add Authority

# %%
# Use imported function to load geodataframe
authorities_of_malawi = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("geoboundaries_ADM3"),
    column_name_to_change="Authority",
)

# %%
# Create FeatureGroup for districts
authorities_group = folium.FeatureGroup(name="Authority")

# Add each district as a coloured GeoJson layer
for _, row in authorities_of_malawi.iterrows():
    folium.GeoJson(
        row["geometry"],
        name=row["Authority"],
        tooltip=row["Authority"],  # remove potentially
    ).add_to(authorities_group)
authorities_group.add_to(map)

# %% [markdown]
# Add colours for Facility Types

# %%
# Supported Folium marker colors
available_colours = [
    "red",
    "blue",
    "green",
    "purple",
    "orange",
    "darkred",
    "#5C5609",
    "violet",
    "darkblue",
    "darkgreen",
    "cadetblue",
    "#4B0082",
    "#930431",
    "pink",
    "lightblue",
    "lightgreen",
    "black",
    "orange",
]

# Get unique facility types
unique_types = geo_df["Facility_Type"].unique()

# Map each type to a color
colour_map_for_facility_type = {
    facility: available_colours[i % len(unique_types)]
    for i, facility in enumerate(unique_types)
}

# Create FeatureGroup for districts
facility_type_group = folium.FeatureGroup(name="Facility Type")

# Added more info to map
for _, row in geo_df.iterrows():
    colour = colour_map_for_facility_type.get(row["Facility_Type"], "gray")
    popup_content = f"""
    <b>Facility Name:</b> {row['Facility_Name']}<br>
    <b>Facility Type:</b> {row['Facility_Type']}<br>
    <b>Facility Ownership:</b> {row['Facility_Ownership']}<br>
    <b>Facility Region:</b> {row['Region']}<br>
    <b>Facility Status:</b> {row['Status']}
    """

    folium.Marker(
        location=[row.geometry.y, row.geometry.x],
        popup=folium.Popup(popup_content, max_width=300),
        icon=folium.Icon(color=colour),
        tooltip=f"""
        <b>District:<b> {row['District']}<br>
        <b>Locality:<b> {row['Authority']}<br>
        """,
        # tooltip={row['District']} # hover
    ).add_to(facility_type_group)
facility_type_group.add_to(map)

# Add legend
legend_html = """
<div style="
    position: fixed;
    bottom: 50px;
    left: 50px;
    width: auto;
    height: auto;
    background-color: white;
    border:2px solid grey;
    z-index:9999;
    font-size:14px;
    padding: 10px;
">
<b>Facility Type</b><br>
"""
for facility, color in colour_map_for_facility_type.items():
    legend_html += f'<i style="background:{color};width:10px;height:10px;display:inline-block;margin-right:5px;"></i>{facility}<br>'
legend_html += "</div>"

# Add legend to map
map.get_root().html.add_child(folium.Element(legend_html))

# Add layer control
folium.LayerControl().add_to(map)

# map

# %% [markdown]
# Save map to outputs

# %%
# Save map as html file
map.save(output_dir / "geospatial_map_with_two_layers_v10.html")
