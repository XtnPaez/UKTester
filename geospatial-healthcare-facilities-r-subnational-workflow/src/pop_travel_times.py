"""
Currently the main workflow script for travel time estimation
(run data_cleaning_and_merging.py first to create relevant datasets)
"""

# %%
import importlib
import geopandas as gpd
import r5py
import matplotlib.pyplot as plt
import pandas as pd
import folium
import numpy as np
from pathlib import Path
import yaml
from datetime import datetime
import numpy as np

import healthcare_accessibility.geospatial_utils as geo_util
import healthcare_accessibility.osm_utils as osm_util
import healthcare_accessibility.data_processing_funcs as dp_funcs
from healthcare_accessibility.utils import setup_sub_dir

modules = [geo_util, osm_util, dp_funcs]

for module in modules:
    importlib.reload(module)

from function_script import compare_travel_time_stats

config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

analysis_crs = config.get("analysis_crs")
visualisation_crs = config.get("visualisation_crs")

output_dir = Path(config.get("outputs_dir"))

# %%
# Download the latest OSM data for Malawi if not already present
osm_util.acquire_latest_osm_data(
    country="malawi", continent="africa", data_dir=config.get("data_dir")
)

osm_file_path = config.get("data_dir") + datasets.get("osm_data").get(
    "malawi_latest_pbf"
)

# Build the transport network from OSM data
transport_network = r5py.TransportNetwork(osm_file_path)

# %%
health_fac_gdf = dp_funcs.load_and_process_hcf_data(
    config,  # existing_lookup="2025-10-29"
)

# %%
facility_type_col = "Facility Type"
hospitals_gdf = dp_funcs.select_fac_subset(
    health_fac_gdf, "hospital", facility_type_col
)

southern_hospitals = dp_funcs.select_fac_subset(hospitals_gdf, "southern", "Region")


maternity_gdf = dp_funcs.select_fac_subset(
    health_fac_gdf, "maternity", facility_type_col
)

lilongwe_hcf_gdf = dp_funcs.select_fac_subset(health_fac_gdf, "lilongwe", "District")

# %%
# Load population grid data
pop_grid_gdf = dp_funcs.load_population_grid(config, analysis_crs)


# %%
# Load administrative boundary data
districts_gdf = dp_funcs.load_administrative_boundaries(config, analysis_crs, "ADM2")
regions_gdf = dp_funcs.load_administrative_boundaries(config, analysis_crs, "ADM1")


# %%

# # Identify population grid cells and district boundaries within certain radius of the selected hospital.
# grids_within_radius, clipped_districts = geo_util.return_within_radius( # change clipped to surrounding
#     central_point=selected_hospital,
#     pop_grid_gdf=pop_grid_gdf,
#     districts_gdf=districts_gdf,
#     radius_in_km=50,
#     analysis_crs=analysis_crs,
#     preview=True
# )

# ## Travel times after filtering by radius

# # %%
# # Set id column
# grids_within_radius["id"] = grids_within_radius["Facility Name"] # add into function

# # %%
# # Takes a long time
# # Calculate travel times for all grids within radius to the random hospital
# travel_time_gdf = geo_util.evaluate_travel_times_to_facilities(
#     origin_grids=grids_within_radius,
#     destination_point=selected_hospital,
#     transport_network=transport_network,
#     pop_grid_gdf=pop_grid_gdf,
#     districts_gdf=clipped_districts,
#     analysis_crs=analysis_crs,
#     transport_mode=r5py.TransportMode.BICYCLE, # BICYCLE, CAR, WALK etc
#     travel_time=0.5,
#     unit_of_time="hours", # will convert to seconds
#     output_map=True
# )

# %% [markdown]
# #### Computing travel time by grids and hcf within a certain km range


def run_iterative_travel_times(
    hcf_gdf,
    pop_grid_gdf,
    districts_gdf,
    transport_network,
    radius_in_km=30,
    transport_mode=r5py.TransportMode.BICYCLE,
    save_output_data=True,
    output_dir=None,
):

    all_times = []

    # To know the facilities causing 'After snapping, no valid destination points remain'
    snapping_error_fac = []

    hcf_gdf.set_index("uid", inplace=True, drop=False)

    for idx, row in hcf_gdf.iterrows():
        # obtaining the grids with N km of an healthcare facility
        grids_within_radius, clipped_districts = geo_util.return_within_radius(
            hcf_gdf.loc[[idx]],
            pop_grid_gdf,
            districts_gdf=districts_gdf,
            radius_in_km=radius_in_km,
            analysis_crs=analysis_crs,
            preview=False,
        )

        print(idx, hcf_gdf.loc[[idx]]["Facility Name"])

        try:
            travel_gdf = geo_util.evaluate_travel_times_to_facilities(
                grids_within_radius,
                hcf_gdf.loc[[idx]],
                transport_network,
                pop_grid_gdf,
                clipped_districts,
                analysis_crs,
                transport_mode,
                travel_time=180,
                unit_of_time="minutes",  # will convert to seconds
                output_map=False,
            )
            if save_output_data:
                output_dir_path = setup_sub_dir(
                    Path(config.get("data_dir")), output_dir
                )
                travel_gdf.to_file(
                    output_dir_path.joinpath(f"travel_times_to_{idx}.gpkg"),
                    driver="GPKG",
                )

            all_times.append(travel_gdf)

        except ValueError:
            print("Position not able to snap to road network")
            snapping_error_fac.append(row["Facility Name"])
            continue

    return all_times, snapping_error_fac


def generate_folium_travel_map(
    travel_time_gdf,
    hcf_gdf,
    description,
    output_dir,
    visualisation_crs,
    add_pop_layer=False,
    pop_grid_gdf=None,
):
    travels_gdf_vis = travel_time_gdf.to_crs(visualisation_crs)
    fac_gdf_viz = hcf_gdf.to_crs(visualisation_crs)

    m = folium.Map(
        location=[
            travels_gdf_vis.geometry.centroid.y.mean(),
            travels_gdf_vis.geometry.centroid.x.mean(),
        ],
        tiles="OpenStreetMap",
        zoom_start=7,
    )

    geo_util.plot_interactive_travel_times_map(
        map=m,
        travels_gdf_vis=travels_gdf_vis,
        destination_hcf=fac_gdf_viz,
        fac_type=description,
        visualisation_crs=visualisation_crs,
    )

    if add_pop_layer:
        pop_grid_viz = pop_grid_gdf.to_crs(visualisation_crs)
        pop_grid_viz["population"] = pop_grid_viz.population.apply(
            lambda x: 0.1 if x < 0.5 else x
        ).sort_values(ascending=True)
        pop_grid_viz["log_population"] = pop_grid_viz.population.apply(np.log10)
        pop_grid_viz
        folium.Choropleth(
            geo_data=pop_grid_viz.to_json(),
            data=pop_grid_viz,
            name="Population estimates",
            columns=["id", "log_population"],
            key_on="feature.properties.id",
            legend_name="Population estimates (log10)",
            fill_opacity=0.7,
            line_weight=0.2,
            fill_color="OrRd",
            show=False,
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    todays_datetime = datetime.now().strftime("%Y-%m-%d")

    m.save(output_dir / f"{description.lower()}_{todays_datetime}_travel_map.html")


# %%

description = "Northern Hospitals"
desired_radius = 110

print(f"Calculating travel times for {description}.")
hcf_gdf = dp_funcs.select_fac_subset(health_fac_gdf, "hospital", "Facility Type")
hcf_gdf = dp_funcs.select_fac_subset(hcf_gdf, "northern", "Region")
hcf_gdf = dp_funcs.clean_hcf_data(hcf_gdf)

all_times_facs, snapping_error_fac = run_iterative_travel_times(
    hcf_gdf,
    pop_grid_gdf,
    districts_gdf,
    transport_network,
    radius_in_km=desired_radius,
    transport_mode=r5py.TransportMode.CAR,
    save_output_data=True,
    output_dir=f"ind_travel_times_{description}/",
)

# dropping all nan travel times
dfs_travel = pd.concat(all_times_facs, ignore_index=True)

# dropping all nan travel times
dfs_travel = dfs_travel[~dfs_travel.travel_time.isna()].reset_index(drop=True)

hcf_sub = dp_funcs.save_data(
    mode_of_transport="car",
    facility=description,
    travel_gdf=dfs_travel,
    fac_sub=hcf_gdf,
    config=config,
)
# %%
min_travel_times_df = dfs_travel.loc[
    dfs_travel.groupby("from_id")["travel_time"].idxmin()
]

hcf_sub = dp_funcs.save_data(
    mode_of_transport="car",
    facility=f"{description}_min",
    travel_gdf=min_travel_times_df,
    fac_sub=hcf_gdf,
    config=config,
)

# %%
facility_map = {
    "Lilongwe": "lilongwe"
    # "Dispensary": "ispensary",
    # "Hospital": "hospital",
    # "Maternity": "maternity",
    # "Health Centre": "entre",
    # "Clinic": "linic",
}

# %%
# calculating for each facility type
all_facs_travel = {}
facilities_with_snapping_error = {}

for h_fac, sub in facility_map.items():
    print(f"Calculating travel times for {h_fac}.")
    if h_fac == "Lilongwe":
        facility_type_col = "District"
    else:
        facility_type_col = "Facility Type"
    fac_gdf = dp_funcs.select_fac_subset(health_fac_gdf, sub, facility_type_col)
    fac_gdf = dp_funcs.clean_hcf_data(fac_gdf)

    all_times_facs, snapping_error_fac = run_iterative_travel_times(
        fac_gdf,
        pop_grid_gdf,
        districts_gdf,
        transport_network,
        radius_in_km=30,
        transport_mode=r5py.TransportMode.BICYCLE,
        save_output_data=True,
        output_dir=f"ind_travel_times_{h_fac}/",
    )

    dfs_travel = pd.concat(all_times_facs, ignore_index=True)

    # dropping all nan travel times
    dfs_travel = dfs_travel[~dfs_travel.travel_time.isna()].reset_index(drop=True)

    all_facs_travel[h_fac] = dfs_travel
    facilities_with_snapping_error[h_fac] = snapping_error_fac


# %%
# all_times_facs, snapping_error_fac = geo_util.calculate_travel_times_to_sample_facilities(
#         hcf_gdf=fac_gdf,
#         transport_network=transport_network,
#         pop_grid_gdf=pop_grid_gdf,
#         districts_gdf=districts_gdf, # clipped_district or districts_gdf
#         random_number_of_facilities="NO",
#         radius_in_km=30,
#         analysis_crs=analysis_crs,
#         transport_mode=r5py.TransportMode.BICYCLE,
#         travel_time=3,
#         unit_of_time="hours", # will convert to seconds
#         output_map=False
#     )
# %%

filtered_all_facs_travel = {}
random_facs = {}

for h_fac, sub in facility_map.items():
    fac_gdf = dp_funcs.select_fac_subset(health_fac_gdf, sub, facility_type_col)
    fac_gdf = dp_funcs.clean_hcf_data(fac_gdf)

    filtered_data = all_facs_travel[h_fac].loc[
        all_facs_travel[h_fac].groupby("from_id")["travel_time"].idxmin()
    ]
    filtered_all_facs_travel[h_fac] = filtered_data

    hcf_sub = dp_funcs.save_data(
        mode_of_transport="bicycle",
        facility=h_fac.lower(),
        travel_gdf=filtered_data,
        fac_sub=fac_gdf,
        config=config,
    )

    random_facs[h_fac] = hcf_sub

# %%
# interactive plot
for h_fac, sub in facility_map.items():
    print(h_fac)
    travel_time_gdf = filtered_all_facs_travel[h_fac]
    fac_gdf = dp_funcs.select_fac_subset(health_fac_gdf, sub, facility_type_col)
    fac_gdf = dp_funcs.clean_hcf_data(fac_gdf)
    generate_folium_travel_map(
        travel_time_gdf, fac_gdf, h_fac, output_dir, visualisation_crs
    )


# %%

for h_fac, sub in facility_map.items():
    data = filtered_all_facs_travel[h_fac]
tt_df = data.groupby(by="to_id", axis=0).first()
joined_df = pd.merge(fac_gdf, tt_df, left_on="id", right_index=True, how="left")


# %% [markdown]
# #### Population Estimate

# %% [markdown]
# ###### This can be run without recalculating travel time

# %%
# Load travel time results for each Facility Type from CSV

# %%

hcf_time_gdfs = {}

transport_mode = "bicycle"
health_facility = "Hospital"

# %%
# gdf = geo_util.load_georeferenced_csv_or_xlsx(
#     file_path=config.get("outputs_dir")
#     + f"{transport_mode}_travel_times_to_{health_facility}.csv",
#     lat_col="Latitude",
#     lon_col="Longitude",
#     desired_crs=analysis_crs,
# )

df = pd.read_csv("outputs/bicycle_travel_times_to_Hospital.csv")

from shapely import wkt

travel_time_gdfs = df.copy()
travel_time_gdfs["geometry"] = gpd.GeoSeries.from_wkt(travel_time_gdfs["geometry_grid"])
travel_time_gdfs = gpd.GeoDataFrame(travel_time_gdfs, geometry="geometry")
travel_time_gdfs = travel_time_gdfs.set_crs(analysis_crs)
travel_time_gdfs["id"] = travel_time_gdfs["from_id"]

hcf_gdf = df.copy()
hcf_gdf["geometry"] = gpd.GeoSeries.from_wkt(hcf_gdf["geometry_hcf"])
hcf_gdf = gpd.GeoDataFrame(hcf_gdf, geometry="geometry")
hcf_gdf = hcf_gdf.set_crs(analysis_crs)
hcf_gdf = hcf_gdf.drop_duplicates(subset=["uid"])

# %%
generate_folium_travel_map(
    travel_time_gdfs,
    hcf_gdf,
    "hospitals",
    output_dir,
    visualisation_crs,
    add_pop_layer=True,
    pop_grid_gdf=pop_grid_gdf,
)


# %%
# Check for grid cells with zero travel time to a Hospital
hcf_time_gdfs[health_facility][
    hcf_time_gdfs[health_facility]["travel_time"].isin([0.0])
]

# %%
# For Facility Name comparison

facility_name_stats = compare_travel_time_stats(
    gdf=hcf_time_gdfs[health_facility], column_of_interest="Facility Name"
)

# %%
# For Facility Type
facility_type_stats = compare_travel_time_stats(
    gdf=hcf_time_gdfs[health_facility], column_of_interest="Facility Type"
)

# %%
# Plot cumulative percentage of population by travel time for each Facility Type
for health_facility, data in hcf_time_gdfs.items():

    data = data.sort_values("travel_time")

    gdf = geo_util.calc_cumulative_percentage(data, pop_grid_gdf)

    plt.figure(figsize=(10, 8))
    # plt.step(gdf['travel_time'], gdf['cumulative_percentage'], where='post', color='red')
    plt.plot(gdf["travel_time"], gdf["cumulative_percentage"], linestyle="-")

    # for the markers
    max_time = gdf["travel_time"].max()
    time_points = np.arange(0, max_time, 30)

    # interpolating travel time at these quartiles
    markers = np.round(
        np.interp(time_points, gdf["travel_time"], gdf["cumulative_percentage"])
    )
    plt.scatter(time_points, markers, label="Every 30 minutes")

    for t, q in zip(time_points, markers):
        plt.text(t, q + 1, f"{q}%", ha="center", fontsize=9)

    plt.xlabel("Travel Time (minutes)")
    plt.ylabel("Cumulative Population (%)")
    plt.title(
        f"National Proportional distribution of population travel times to the nearest {health_facility} facility "
    )
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.show()


# %%


def split_population_grid_by_region(
    pop_grid_gdf,
    regions_gdf,
    analysis_crs,
    regions=["Central Region", "Northern Region", "Southern Region"],
):
    """
    Split population grid geodataframe by regions for later analysis.

    Parameters
    ----------
    pop_grid_gdf : geopandas.GeoDataFrame
        Geodataframe of population grid data.
    regions_gdf : geopandas.GeoDataFrame
        Geodataframe of regional boundaries.
    analysis_crs : str
        The desired CRS for the loaded data
    regions : list, optional
        List of region names to split the population grid by.

    Returns
    -------
    dict
        Dictionary containing geodataframes of population grids for each region.
    """

    # Create empty dictionary
    region_pop_grids = {}

    for reg in regions:
        region_boundary = regions_gdf[regions_gdf.ADM1 == reg]
        region_boundary = region_boundary.to_crs(analysis_crs)

        reg = reg.split(" ")[0]
        # Filter population grid centroids by the bounds of a region
        region_pop_grid = pop_grid_gdf.sjoin(region_boundary, how="inner")
        region_pop_grids[reg] = region_pop_grid

    return region_pop_grids


region_pop_grids = split_population_grid_by_region(
    pop_grid_gdf, regions_gdf, analysis_crs
)

# Plot cumulative percentage of population by travel time for each region and Facility Type
for health_facility, data in hcf_time_gdfs.items():
    if health_facility not in ["Maternity", "Clinic"]:

        # selecting subset for rural and urban areas
        central_df = data[data["Region"] == "Central"]
        northern_df = data[data["Region"] == "Northern"]
        southern_df = data[data["Region"] == "Southern"]

        central_df = central_df.sort_values("travel_time")
        northern_df = northern_df.sort_values("travel_time")
        southern_df = southern_df.sort_values("travel_time")

        central_gdf = geo_util.calc_cumulative_percentage(
            central_df, region_pop_grids["Central"]
        )
        northern_gdf = geo_util.calc_cumulative_percentage(
            northern_df, region_pop_grids["Northern"]
        )
        southern_gdf = geo_util.calc_cumulative_percentage(
            southern_df, region_pop_grids["Southern"]
        )

        plt.figure(figsize=(10, 8))
        # plt.step(gdf['travel_time'], gdf['cumulative_percentage'], where='post', color='red')
        plt.plot(
            central_gdf["travel_time"],
            central_gdf["cumulative_percentage"],
            linestyle="-",
        )
        plt.plot(
            northern_gdf["travel_time"],
            northern_gdf["cumulative_percentage"],
            linestyle="-",
        )
        plt.plot(
            southern_gdf["travel_time"],
            southern_gdf["cumulative_percentage"],
            linestyle="-",
        )

        # for the markers
        max_time = np.nanmax(
            [
                central_gdf["travel_time"].max(),
                southern_gdf["travel_time"].max(),
                northern_gdf["travel_time"].max(),
            ]
        )
        time_points = np.arange(0, max_time, 30)

        # interpolating travel time at these quartiles
        markers_c = np.round(
            np.interp(
                time_points,
                central_gdf["travel_time"],
                central_gdf["cumulative_percentage"],
            )
        )
        markers_n = np.round(
            np.interp(
                time_points,
                northern_gdf["travel_time"],
                northern_gdf["cumulative_percentage"],
            )
        )
        markers_s = np.round(
            np.interp(
                time_points,
                southern_gdf["travel_time"],
                southern_gdf["cumulative_percentage"],
            )
        )

        plt.scatter(time_points, markers_c, label="Central Region")
        plt.scatter(time_points, markers_n, label="Northern Region")
        plt.scatter(time_points, markers_s, label="Southern Region")

        for t, q in zip(time_points, markers_c):
            plt.text(t, q + 1, f"{q}%", ha="center", fontsize=9)
        for t, q in zip(time_points, markers_n):
            plt.text(t, q + 1, f"{q}%", ha="center", fontsize=9)
        for t, q in zip(time_points, markers_s):
            plt.text(t, q + 1, f"{q}%", ha="center", fontsize=9)

        plt.xlabel("Travel Time (minutes)")
        plt.ylabel("Cumulative Population (%)")
        plt.title(
            f"National Proportional distribution of population travel times to the nearest {health_facility} facility "
        )
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.show()

# %%
