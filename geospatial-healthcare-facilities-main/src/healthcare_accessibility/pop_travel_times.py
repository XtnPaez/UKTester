"""
Currently the main workflow script for travel time estimation
"""

# %%
import importlib
import geopandas as gpd
import r5py
from pathlib import Path
import yaml
from janitor import clean_names
import pandas as pd
import pycountry

import healthcare_accessibility.geospatial_utils as geo_util
import healthcare_accessibility.osm_utils as osm_util
import healthcare_accessibility.data_processing_funcs as dp_funcs
import healthcare_accessibility.utils as utils

modules = [geo_util, osm_util, dp_funcs, utils]

for module in modules:
    importlib.reload(module)
# %%
config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

analysis_crs = config.get("analysis_crs").get(config.get("country"))
visualisation_crs = config.get("visualisation_crs")
country = config.get("country")

max_travel_time_mins = 120

transport_modes_dict = {
    "bicycle": r5py.TransportMode.BICYCLE,
    # "car": r5py.TransportMode.CAR,
    # "walk": r5py.TransportMode.WALK,
}

# %%
print(f"Preparing data for travel time estimation in {country}")

processed_data_dir = Path(config.get("data_dir")) / country / "processed_data"

health_fac_gdf = gpd.read_file(
    processed_data_dir / datasets.get("health_facility").get("processed_hcf")
)

health_fac_gdf = health_fac_gdf.to_crs(analysis_crs)

# convert any polygons to points by taking the centroid (some facilities are mapped as polygons in OSM)
health_fac_gdf["geometry"] = health_fac_gdf.geometry.centroid

pop_grid_gdf = gpd.read_file(
    processed_data_dir / datasets.get("population").get("processed_master_grid")
)

pop_grid_gdf = pop_grid_gdf.rename(columns={"id_national": "id"})
pop_grid_gdf = pop_grid_gdf.to_crs(analysis_crs)

# %%
output_dir, maps_dir = utils.setup_output_directory(config)


adm1_path = (
    Path(config.get("data_dir"))
    .joinpath(country.lower())
    .joinpath("raw_data")
    .joinpath("admin_boundary_geom")
    .joinpath(
        f"{pycountry.countries.get(name=country).alpha_3}_ADM1_geoboundaries.geojson"
    )
)

regions_gdf = dp_funcs.load_administrative_boundaries(adm1_path, "ADM1")
regions_gdf = regions_gdf.to_crs(analysis_crs)

clipped_health_fac_gdf = gpd.clip(health_fac_gdf, regions_gdf)

# %%
# Build the transport network from OSM data
raw_data_dir = Path(config.get("data_dir")) / country.lower() / "raw_data"

osm_file_path = raw_data_dir.joinpath(f"{country.lower()}-latest.osm.pbf")

transport_network = r5py.TransportNetwork(osm_file_path)

# %%
description = "All healthcare facilities"

for transport_mode, r5_trans_mode in transport_modes_dict.items():

    print(f"Calculating travel times via {transport_mode}.")

    travel_time_matrix_df = geo_util.evaluate_travel_times_to_facilities(
        population_grids=pop_grid_gdf,
        hcf_points=clipped_health_fac_gdf,
        transport_network=transport_network,
        analysis_crs=analysis_crs,
        transport_mode=r5_trans_mode,
        max_travel_time=max_travel_time_mins,
        unit_of_time="minutes",
        snap_to_network_bool=True,
    )

    dp_funcs.save_data(
        travel_time_matrix=travel_time_matrix_df,
        mode_of_transport=transport_mode,
        facility=description,
        output_dir=output_dir,
        output_file_format="parquet",
    )

    travel_gdf = dp_funcs.recombine_travel_matrix_with_pop_data(
        travel_time_matrix_df, pop_grid_gdf
    )

    min_travel_times_gdf = dp_funcs.return_nearest_travel_outcome(
        travel_gdf, grid_cell_id_column="to_id", travel_outcome_column="travel_time"
    )

    geo_util.generate_folium_travel_map(
        min_travel_times_gdf[
            min_travel_times_gdf["travel_time"] <= max_travel_time_mins
        ],
        clipped_health_fac_gdf,
        transport_mode,
        "healthcare facility of type 'any'",
        "all_hcfs_national",
        maps_dir,
        visualisation_crs,
        add_pop_layer=True,
        pop_grid_gdf=pop_grid_gdf,
    )

    for adm1 in regions_gdf.ADM1.values:
        print(adm1)
        tmp_ttm = min_travel_times_gdf[
            min_travel_times_gdf["travel_time"] <= max_travel_time_mins
        ]
        tmp_ttm = gpd.clip(tmp_ttm, regions_gdf[regions_gdf.ADM1 == adm1])
        tmp_hcf = gpd.clip(
            clipped_health_fac_gdf, regions_gdf[regions_gdf.ADM1 == adm1]
        )
        tmp_pop = gpd.clip(pop_grid_gdf, regions_gdf[regions_gdf.ADM1 == adm1])
        geo_util.generate_folium_travel_map(
            tmp_ttm,
            tmp_hcf,
            transport_mode,
            "healthcare facility of type 'any'",
            f"all_hcfs_{adm1.lower()}",
            maps_dir,
            visualisation_crs,
            add_pop_layer=True,
            pop_grid_gdf=tmp_pop,
        )

# %%
