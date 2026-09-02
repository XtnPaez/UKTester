# %%

import datetime
import geopandas as gpd
import r5py
import matplotlib.pyplot as plt
from pyrosm import OSM
import pandas as pd
from pathlib import Path
import yaml

import healthcare_accessibility.geospatial_utils as geo_util
import healthcare_accessibility.osm_utils as osm_utils

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
    "Lat",
    "Long",
    desired_crs=analysis_crs,
)


health_fac_gdf["id"] = health_fac_gdf["Facility Code"]

health_fac_gdf = health_fac_gdf[~health_fac_gdf.latitude.isna()].drop_duplicates(
    subset=["id"]
)

# %%
# osm = OSM(osm_file_path)

# drive_net = osm_utils.load_driving_network(osm)

# osm_healthcare_df = osm_util.return_points_of_interest(
#     osm, ["hospital", "doctors", "clinic", "pharmacy", "dentist"], plot_positions=True
# )

# ax = drive_net.plot(figsize=(12, 12), zorder=0)
# osm_healthcare_df.plot(
#     column="amenity",
#     markersize=12,
#     figsize=(12, 12),
#     legend=True,
#     legend_kwds=dict(loc="upper left", ncol=1, bbox_to_anchor=(1, 1)),
#     ax=ax,
#     zorder=1,
# )
# lilongwe_gdf.plot(ax=ax, zorder=2, color="red", markersize=15, label="Baobab")
# plt.show()

# %%

transport_network = r5py.TransportNetwork(osm_file_path)

# %%

hospitals_gdf = health_fac_gdf[
    health_fac_gdf["Facility Type"].str.contains("ospital", na=False)
]

random_hospital = hospitals_gdf.sample(1)

# %%


def return_sorted_nearest_points(
    origin_point, points_gdf, distance_km, distance_col="distance", preview=False
):
    """Return points within a certain distance of an origin point, sorted by distance"""

    distance_m = distance_km * 1000

    nearest_df = origin_point[["Facility Name", "geometry"]].sjoin_nearest(
        points_gdf, how="right", distance_col=distance_col, exclusive=True
    )

    ordered_within_distance = nearest_df[
        nearest_df[distance_col] < distance_m
    ].sort_values(by="distance")

    if preview:
        ax = (
            ordered_within_distance.reset_index()
            .reset_index()
            .plot(markersize="level_0")
        )
        origin_point.plot(color="red", marker="+", ax=ax)
        plt.show()

    return ordered_within_distance


ordered_within_100km = return_sorted_nearest_points(
    random_hospital, hospitals_gdf, 100, preview=True
)

ax = ordered_within_100km.reset_index().reset_index().plot(markersize="level_0")
random_hospital.plot(color="red", marker="+", ax=ax)

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
districts_gdf = geoboundaries_ADM2.copy().to_crs(analysis_crs)


# %%


def plot_travel_times_map(travel_gdf, districts_gdf, destination_point, savefig=False):
    ax = travel_gdf.plot(
        figsize=(12, 12),
        label="Origins",
        column="travel_time",
        cmap="viridis",
        legend=True,
        legend_kwds={
            "label": "Travel time (min)",
        },
        missing_kwds={
            "color": "lightgrey",
            "hatch": "///",
            "label": "Missing values",
        },
    )
    districts_gdf.to_crs(analysis_crs).boundary.plot(
        ax=ax, color="black", linestyle="--"
    )
    destination_point.plot(
        ax=ax, color="red", markersize=25, marker="P", label="Destination"
    )
    ax.set_axis_off()
    if savefig:
        plt.savefig("outputs/travel_time_map.png", dpi=300)
    plt.show()


def evaluate_travel_times_to_facilities(
    origin_grids,
    destination_point,
    transport_network,
    pop_grid_gdf,
    districts_gdf,
    analysis_crs,
    output_map=True,
):
    origin_grid_centroids = geo_util.return_grid_centroids(origin_grids.copy())

    print("Calculating travel times...")

    travel_times = r5py.TravelTimeMatrix(
        transport_network,
        origins=origin_grid_centroids,
        destinations=destination_point,
        transport_modes=[
            r5py.TransportMode.CAR,
        ],
        snap_to_network=True,
    )

    print("Processing and plotting travel times...")

    travel_df = pd.merge(
        pd.DataFrame(travel_times), pop_grid_gdf, left_on="from_id", right_on="id"
    )
    travel_gdf = gpd.GeoDataFrame(travel_df, geometry="geometry", crs=analysis_crs)

    if output_map:
        plot_travel_times_map(travel_gdf, districts_gdf, destination_point)
    return travel_gdf


def return_within_radius(central_point, pop_grid_gdf, radius_in_km, preview=False):
    """
    Return population grids and districts within a certain radius of an central point

    Parameters
    ----------
    central_point : point geometry
        The central point to measure distance from
    pop_grid_gdf : geopandas.GeoDataFrame
        The gridded population data in geodataframe format
    radius_in_km : int, optional
        The desired radius in kilometres.

    Returns
    -------
    _type_
        _description_
    """

    radius_in_metres = radius_in_km * 1000

    buffer_area = central_point.geometry.buffer(radius_in_metres)

    grids_within_radius = gpd.sjoin(
        pop_grid_gdf,
        buffer_area.to_frame(name="geometry"),
        how="inner",
    )

    clipped_districts = gpd.sjoin(
        districts_gdf,
        buffer_area.to_frame(name="geometry"),
        how="inner",
    )

    if preview:
        ax = grids_within_radius.plot(
            figsize=(12, 12), label="Origins", column="population"
        )
        clipped_districts.boundary.plot(ax=ax, color="black", linestyle="--")
        central_point.plot(ax=ax, color="red", markersize=15, label="Destination")
        plt.show()

    return grids_within_radius, clipped_districts


# %%

## Travel times after filtering by radius ##

grids_within_radius, clipped_districts = return_within_radius(
    random_hospital, pop_grid_gdf, radius_in_km=100, preview=True
)
# %%

travel_gdf = evaluate_travel_times_to_facilities(
    grids_within_radius,
    random_hospital,
    transport_network,
    pop_grid_gdf,
    clipped_districts,
    analysis_crs,
)

# %%

cols_to_drop = list(random_hospital.filter(regex="Unnamed"))


output_df = pd.merge(
    travel_gdf,
    random_hospital,
    left_on="to_id",
    right_on="Facility Code",
    how="left",
    suffixes=["_grid", "_hcf"],
).drop(columns=cols_to_drop)

hcf_name = output_df["Facility Name"].values[0]

output_df.to_csv(
    config.get("outputs_dir") + f"travel_times_to_{hcf_name.replace(' ', '_')}.csv",
    index=False,
)

# %%

## Travel times for a single district ##

district = "Mwanza"
district_boundary = districts_gdf[districts_gdf == district]
district_boundary = district_boundary.to_crs(analysis_crs)

# Filter population grid centroids by the bounds of a district
district_pop_grid = pop_grid_gdf.sjoin(district_boundary, how="inner")
district_pop_cent = geo_util.return_grid_centroids(district_pop_grid.copy())

# Filter healthcare facility dataset by the bounds of a district
hc_district_gdf = health_fac_gdf.sjoin(district_boundary, how="inner")


# %%


destination_hcf = hc_district_gdf.sample(1)

travel_gdf = evaluate_travel_times_to_facilities(
    district_pop_grid,
    destination_hcf,
    transport_network,
    pop_grid_gdf,
    district_boundary,
    analysis_crs,
)

travel_times = r5py.TravelTimeMatrix(
    transport_network,
    origins=origin_grid_centroids,
    destinations=destination_hcf,
    transport_modes=[
        r5py.TransportMode.CAR,
    ],
    snap_to_network=True,
)

ax = origin_grid.plot(figsize=(12, 12), label="Origins", column="population")
district_boundary.to_crs(analysis_crs).boundary.plot(ax=ax)
destination_hcf.plot(ax=ax, color="red", markersize=15, label="Destination")
plt.show()


# %%

travel_df = pd.merge(
    pd.DataFrame(travel_times), pop_grid_gdf, left_on="from_id", right_on="id"
)
travel_gdf = gpd.GeoDataFrame(travel_df, geometry="geometry", crs=analysis_crs)


ax = travel_gdf.plot(figsize=(12, 12), label="Origins", column="travel_time")
district_boundary.to_crs(analysis_crs).boundary.plot(ax=ax)
destination_hcf.plot(ax=ax, color="red", markersize=15, label="Destination")
plt.show()

# %%

## Travel times for a district and its neighbours ##

# code for finding neighbouring districts
districts = geoboundaries_ADM2.to_crs(analysis_crs)
neighbouring_districts = districts[
    districts.touches(district_boundary.geometry.iloc[0])
]

# %%


def deduplicate(gdf, id_col="id"):
    return gdf.drop_duplicates(subset=[id_col])


def return_centroids_and_deduplicate(gdf, id_col="id"):
    centroids = geo_util.return_grid_centroids(gdf.copy())
    centroids = deduplicate(centroids, id_col)
    return centroids


multi_districts_gdf = gpd.GeoDataFrame(
    pd.concat((district_boundary, neighbouring_districts), axis=0)
)

# Filter population grid centroids by the bounds of a district
multi_district_pop_grid = pop_grid_gdf.sjoin(multi_districts_gdf, how="inner")


multi_district_pop_cent = return_centroids_and_deduplicate(multi_district_pop_grid)

# Filter healthcare facility dataset by the bounds of a district
hc_districts_gdf = health_fac_gdf.sjoin(district, how="inner")
hc_districts_gdf = deduplicate(hc_districts_gdf)


# %%

origin_grid = multi_district_pop_grid
origin_grid_centroids = geo_util.return_grid_centroids(origin_grid.copy())
origin_grid_centroids = origin_grid_centroids.drop_duplicates(subset=["id"])

destination_hcf = hc_districts_gdf.sample(1)

travel_times = r5py.TravelTimeMatrix(
    transport_network,
    origins=origin_grid_centroids,
    destinations=destination_hcf,
    transport_modes=[
        r5py.TransportMode.CAR,
    ],
    snap_to_network=True,
    max_time=datetime.timedelta(seconds=10800),  # 3 hours
)

ax = origin_grid.plot(figsize=(12, 12), label="Origins", column="population")
district_boundary.to_crs(analysis_crs).boundary.plot(ax=ax)
destination_hcf.plot(ax=ax, color="red", markersize=15, label="Destination")
plt.show()


# %%


travel_df = pd.merge(
    pd.DataFrame(travel_times), pop_grid_gdf, left_on="from_id", right_on="id"
)
travel_gdf = gpd.GeoDataFrame(travel_df, geometry="geometry", crs=analysis_crs)

# %%
plot_travel_times_map(travel_gdf, multi_districts_gdf, destination_hcf, savefig=True)

# %%
