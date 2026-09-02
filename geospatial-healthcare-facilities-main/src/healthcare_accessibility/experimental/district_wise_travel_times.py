"""Script for getting district-wise travel times to healthcare facilities (Ola)"""

# %%
import geopandas as gpd
import r5py
import matplotlib.pyplot as plt
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

health_fac_gdf = geo_util.load_georeferenced_csv_or_xlsx(
    config.get("data_dir") + datasets.get("health_facility").get("baobab"),
    "latitude",
    "longitude",
    desired_crs=analysis_crs,
)


health_fac_gdf["id"] = health_fac_gdf["Facility Name"]
# %%
# health_fac_gdf = health_fac_gdf[~health_fac_gdf.LATITUDE.isna()].drop_duplicates(
# subset=["id"]
# )

health_fac_gdf = health_fac_gdf.drop_duplicates(subset=["id"])

# %%

transport_network = r5py.TransportNetwork(osm_file_path)

# %%
## Population grid data to healthcare facility travel times ##

pop_grid_path = config.get("data_dir") + datasets.get("population").get("wp_2025_1km")
pop_grid_gdf = geo_util.load_and_vectorize_grid_tif(pop_grid_path)
pop_grid_gdf = geo_util.set_crs(pop_grid_gdf, analysis_crs)
pop_grid_gdf["id"] = pop_grid_gdf.index.astype(str)

pop_grid_centroids = geo_util.return_grid_centroids(pop_grid_gdf.copy())


# %%

geoboundaries_ADM2 = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("geoboundaries_ADM2"),
    column_name_to_change="ADM2",
)

# %%
# Calculate travel times to a random healthcare facility for all districts in Malawi
# Initialize a list to store travel time results for all districts
all_travel_times = []

# Loop through each district in geoboundaries_ADM2
for district in geoboundaries_ADM2.ADM2.unique():
    print(f"Processing district: {district}")

    # Filter district boundary
    district_boundary = geoboundaries_ADM2[geoboundaries_ADM2.ADM2 == district]
    district_boundary = district_boundary.to_crs(analysis_crs)

    # Filter population grid centroids by the bounds of the district
    district_pop_grid = pop_grid_gdf.sjoin(district_boundary, how="inner")
    district_pop_cent = geo_util.return_grid_centroids(district_pop_grid.copy())

    # Filter healthcare facility dataset by the bounds of the district
    hc_district_gdf = health_fac_gdf.to_crs(analysis_crs).sjoin(
        district_boundary, how="inner"
    )

    # Skip if no healthcare facilities are found in the district
    if hc_district_gdf.empty:
        print(f"No healthcare facilities found in district: {district}")
        continue

    # Set origins and destinations
    origin_grid = district_pop_grid
    origin_grid_centroids = geo_util.return_grid_centroids(origin_grid.copy())
    destination_hcf = hc_district_gdf.sample(1)  # Sample one healthcare facility

    # Calculate travel times
    travel_times = r5py.TravelTimeMatrix(
        transport_network,
        origins=origin_grid_centroids,
        destinations=destination_hcf,
        transport_modes=[
            r5py.TransportMode.CAR,
        ],
        snap_to_network=True,
    )

    # Add district name to travel times for identification
    travel_times["district"] = district
    all_travel_times.append(travel_times)

    # Plot the results for the current district
    ax = origin_grid.plot(figsize=(12, 12), label="Origins", column="population")
    district_boundary.to_crs(analysis_crs).boundary.plot(ax=ax)
    destination_hcf.plot(ax=ax, color="red", markersize=15, label="Destination")
    plt.title(f"Travel Times for District: {district}")
    plt.show()

# Combine all travel times into a single DataFrame
all_travel_times_df = pd.concat(all_travel_times, ignore_index=True)

# Save the results to a CSV file
all_travel_times_df.to_csv("travel_times_all_districts.csv", index=False)

print("Travel time calculations completed for all districts.")

# %%
all_travel_times_dfr = pd.merge(
    all_travel_times_df, pop_grid_gdf, left_on="from_id", right_on="id"
)
all_travel_times_dfr = gpd.GeoDataFrame(
    all_travel_times_dfr, geometry="geometry", crs="EPSG:20936"
)
all_travel_times_dfr.plot(column="travel_time_x")


# %%

plt.figure(figsize=(12, 12))
all_travel_times_dfr.plot(
    column="travel_time_x",  # Use travel time for coloring
    cmap="OrRd",  # Color map
    legend=True,
    legend_kwds={"label": "Travel Time (minutes)"},
)
plt.title("Travel Time to A Random Healthcare Facilities in Malawi", fontsize=14)
plt.axis("off")
plt.show()


# %%
# Extract unique healthcare facility points from the destination points (to_id)
sampled_health_facilities = all_travel_times_dfr[["to_id"]].drop_duplicates()
sampled_health_facilities = pd.merge(
    sampled_health_facilities, health_fac_gdf, left_on="to_id", right_on="id"
)
sampled_health_facilities = gpd.GeoDataFrame(
    sampled_health_facilities, geometry="geometry", crs="EPSG:20936"
)

# Plot the travel time map
plt.figure(figsize=(16, 18))
base = all_travel_times_dfr.plot(
    column="travel_time_x",  # Use travel time for coloring
    cmap="viridis",  # Color map
    legend=True,
    legend_kwds={"label": "Travel Time (minutes)"},
    # alpha=0.5,  # Transparency for better overlay visibility
)

# Overlay sampled healthcare facility points
sampled_health_facilities.plot(
    ax=base,  # Overlay on the base map
    color="red",  # Color for healthcare facilities
    markersize=1,  # Adjust marker size
    # label="Sampled Healthcare Facilities",
)

# Add title and legend
plt.title("Travel Time to Sampled Healthcare Facilities in Malawi", fontsize=12)
plt.axis("off")
plt.legend()
plt.show()


# %%
# Average travel times by districts in Malawi
average_travel_times = (
    all_travel_times_df.groupby("district")["travel_time"].mean().reset_index()
)
average_travel_times = average_travel_times.sort_values(
    by="travel_time", ascending=False
)

# Step 2: Plot a bar chart
plt.figure(figsize=(12, 8))
plt.barh(
    average_travel_times["district"],
    average_travel_times["travel_time"],
    color="skyblue",
)
plt.xlabel("Average Travel Time (minutes)", fontsize=12)
plt.ylabel("District", fontsize=12)
plt.title(
    "Average Travel Time to Healthcare Facilities by District in Malawi", fontsize=14
)
plt.gca().invert_yaxis()  # Invert y-axis for better readability
plt.grid(axis="x", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()

# %%
# Merge average travel times with district boundaries
district_boundaries = geoboundaries_ADM2.merge(
    average_travel_times, left_on="ADM2", right_on="district"
)

# Plot the map
plt.figure(figsize=(12, 10))
district_boundaries.plot(
    column="travel_time",  # Use average travel time for coloring
    cmap="OrRd",  # Color map
    legend=True,
    legend_kwds={"label": "Average Travel Time (minutes)"},
    edgecolor="black",
)
plt.title(
    "Average Travel Time to Healthcare Facilities by District in Malawi", fontsize=14
)
plt.axis("off")
plt.show()


# %%
# Step 1: Aggregate travel time data
# If not already combined, concatenate travel time data for all districts
# all_travel_times_df = pd.concat([district1_df, district2_df, ...], ignore_index=True)

# Step 2: Calculate cumulative distribution
# Sort travel times
all_travel_times_df = all_travel_times_df.sort_values(by="travel_time")

# Calculate cumulative percentage
all_travel_times_df["cumulative_percentage"] = (
    all_travel_times_df["travel_time"].rank(method="max") / len(all_travel_times_df)
) * 100

# Step 3: Plot the cumulative distribution
plt.figure(figsize=(10, 6))
plt.plot(
    all_travel_times_df["travel_time"],
    all_travel_times_df["cumulative_percentage"],
    label="Cumulative Travel Time Distribution",
    color="blue",
)

# Add labels and title
plt.title(
    "Cumulative Travel Time Distribution for All Districts in Malawi", fontsize=14
)
plt.xlabel("Travel Time (minutes)", fontsize=12)
plt.ylabel("Cumulative Percentage (%)", fontsize=12)
plt.grid(True, linestyle="--", alpha=0.7)
plt.legend()
plt.show()

# %%

# Interactive map using geopandas and folium

# Create an interactive map for travel times
m = all_travel_times_dfr.explore(
    column="travel_time_x",  # Use travel time for coloring
    cmap="viridis",  # Color map
    legend=True,  # Show legend
    tooltip=["travel_time_x", "to_id"],  # Show travel time on hover
    popup=True,  # Enable popups for more details
    tiles="CartoDB positron",  # Add a basemap
)

# Overlay healthcare facility points on the map
sampled_health_facilities.explore(
    m=m,  # Add to the existing map
    color="red",  # Color for healthcare facilities
    marker_kwds={"radius": 3},  # Adjust marker size
    tooltip=[
        "to_id",
        "District",
        "Facility Type",
    ],  # Show facility name on hover (if available)
    popup=True,  # Enable popups for more details
)
