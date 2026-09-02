# %%
import importlib
import geopandas as gpd
from pathlib import Path
import yaml
import pyarrow

import healthcare_accessibility.data_processing_funcs as dp_funcs
import healthcare_accessibility.geospatial_utils as geo_util
import healthcare_accessibility.postprocessing as postpro

modules = [geo_util, dp_funcs, postpro]
for module in modules:
    importlib.reload(module)

# %%
config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

analysis_crs = config.get("analysis_crs").get(config.get("country"))


# %%
country = config.get("country")

travel_time_inputs_dir = Path(config.get("outputs_dir")).joinpath(country)

print("Loading cycle travel time matrix...")
bike_ttm_df = pyarrow.parquet.read_pandas(
    Path(travel_time_inputs_dir).joinpath(
        "bicycle_travel_times_to_All healthcare facilities.parquet"
    )
).to_pandas()
bike_ttm_df["to_id"] = bike_ttm_df["to_id"].astype(str)


walk_ttm_path = Path(travel_time_inputs_dir).joinpath(
    "walk_travel_times_to_All healthcare facilities.parquet"
)
if walk_ttm_path.exists():
    print("Loading walk travel time matrix...")
    walk_ttm_df = pyarrow.parquet.read_pandas(
        Path(travel_time_inputs_dir).joinpath(
            "walk_travel_times_to_All healthcare facilities.parquet"
        )
    ).to_pandas()
    walk_ttm_df["to_id"] = walk_ttm_df["to_id"].astype(str)


car_ttm_path = Path(travel_time_inputs_dir).joinpath(
    "car_travel_times_to_All healthcare facilities.parquet"
)
if car_ttm_path.exists():
    print("Loading car travel time matrix...")
    car_ttm_df = pyarrow.parquet.read_pandas(
        Path(travel_time_inputs_dir).joinpath(
            "car_travel_times_to_All healthcare facilities.parquet"
        )
    ).to_pandas()
    car_ttm_df["to_id"] = car_ttm_df["to_id"].astype(str)


processed_data_dir = (
    Path(config.get("data_dir")) / config.get("country") / "processed_data"
)

health_fac_gdf = gpd.read_file(
    processed_data_dir / datasets.get("health_facility").get("processed_hcf")
)

print("Loading healthcare facility data...")
health_fac_gdf = health_fac_gdf.to_crs(analysis_crs)

# convert any polygons to points by taking the centroid (some facilities are mapped as polygons in OSM)
health_fac_gdf["geometry"] = health_fac_gdf.geometry.centroid

print("Loading population data...")
pop_gdf = gpd.read_file(
    processed_data_dir / datasets.get("population").get("processed_master_grid")
)

pop_gdf = pop_gdf.rename(columns={"id_national": "id"})
pop_gdf = pop_gdf.to_crs(analysis_crs)

# %%

distance_matrix_bike_df = postpro.convert_travel_time_to_distance(
    bike_ttm_df, "bicycle"
)

distance_matrix_df = distance_matrix_bike_df.drop("travel_time", axis=1)


# %%
distance_threshold = 10


service_area_grids = postpro.filter_by_distance_threshold(
    distance_matrix_df, distance_threshold
)


nearest_service_area_grids = dp_funcs.return_nearest_travel_outcome(
    service_area_grids,
    grid_cell_id_column="to_id",
    travel_outcome_column="travel_distance",
)

nearest_service_area_grids = dp_funcs.recombine_travel_matrix_with_pop_data(
    nearest_service_area_grids, pop_gdf
)


pop_stats_result_df = postpro.return_population_within_threshold(
    nearest_service_area_grids, pop_gdf
)

postpro.plot_excluded_population_by_admin_areas(
    pop_stats_result_df, distance_threshold, "ADM2"
)
postpro.plot_excluded_population_by_admin_areas(
    pop_stats_result_df, distance_threshold, "ADM1"
)


# %%

nearest_service_area_grids = postpro.attach_travel_time(
    nearest_service_area_grids, bike_ttm_df, mode_of_transport="bike"
)

if walk_ttm_path.exists():
    nearest_service_area_grids = postpro.attach_travel_time(
        nearest_service_area_grids, walk_ttm_df, mode_of_transport="walk"
    )

if car_ttm_path.exists():
    nearest_service_area_grids = postpro.attach_travel_time(
        nearest_service_area_grids, car_ttm_df, mode_of_transport="car"
    )

# %%
# Plot cumulative percentage of population by travel distance for each Facility Type

postpro.plot_cumulative_population_by_travel_metric(
    distance_matrix_df,
    pop_gdf,
    travel_metric="travel_distance",
    aggregate_admin="ADM2",
    highlight_line=8,
)

# %%
