"""
Data acquisition and preprocessing script.

Includes following data:
- population
- healthcare facilities
- transport network (from OSM)
- administrative boundaries
"""

# %%
import importlib
import geopandas as gpd
from importlib_metadata import files
from pathlib import Path
import requests
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

country = config.get("country")
country_iso_code = pycountry.countries.get(name=country).alpha_3

visualisation_crs = config.get("visualisation_crs")

# %%

country_continent_dict = {
    "Malawi": "africa",
    "Rwanda": "africa",
    "Switzerland": "europe",
    "Nepal": "asia",
    "Bangladesh": "asia",
}

# initialise folder structure
raw_data_dir = Path(config.get("data_dir")) / country.lower() / "raw_data"
raw_data_dir.mkdir(parents=True, exist_ok=True)
raw_data_dir.joinpath("health_facility_data").mkdir(parents=True, exist_ok=True)


processed_data_dir = (
    Path(config.get("data_dir"))
    .joinpath(config.get("country").lower())
    .joinpath("processed_data")
)
# %%
osm_file_path = raw_data_dir.joinpath(f"{country.lower()}-latest.osm.pbf")

# Download the latest OSM data for the specified country if not already present
osm_util.acquire_latest_osm_data(
    country=country,
    continent=country_continent_dict.get(country),
    output_filepath=osm_file_path,
)


# %%
# Load population grid data

population_data_path = dp_funcs.download_wp_population_data(
    raw_data_dir, country_iso_code, force_overwrite=False
)

pop_grid_gdf = dp_funcs.load_population_grid(config, pop_file_path=population_data_path)

# %%

adm1_path = dp_funcs.download_geoboundaries_data(raw_data_dir, country_iso_code, "ADM1")
adm2_path = dp_funcs.download_geoboundaries_data(raw_data_dir, country_iso_code, "ADM2")


# %%
pop_gdf_adm, districts_gdf = dp_funcs.assign_grids_to_admin_areas(
    adm2_path, pop_grid_gdf, admin_id_col="ADM2"
)
pop_gdf_adm, regions_gdf = dp_funcs.assign_grids_to_admin_areas(
    adm1_path, pop_gdf_adm, admin_id_col="ADM1"
)

# %%

# Demographic population data processing
demographic_pop_df = dp_funcs.process_demographic_pop_data(
    raw_data_dir, processed_data_dir, country_iso_code
)

# %%

pop_master_gdf = dp_funcs.combine_agesex_national_pop_data(
    raw_data_dir, processed_data_dir, pop_gdf_adm, demographic_pop_df, country_iso_code
)

# %%


health_data_source = "healthsites.io"  # "mwi_MHFR"

if health_data_source == "mwi_MHFR":

    health_fac_gdf = dp_funcs.load_and_process_hcf_data(
        config,  # existing_lookup="2025-10-29"
    )
    health_fac_gdf = health_fac_gdf.clean_names()

    id_column = "uid"
    health_fac_gdf["id"] = health_fac_gdf[id_column]

    dp_funcs.save_hcf_data(processed_data_dir, health_fac_gdf)


elif health_data_source == "healthsites.io":
    hcf_path = Path(
        rf"data/{country.lower()}/raw_data/health_facility_data/{country.lower()}.geojson"
    )
    hcf_path.parent.mkdir(parents=True, exist_ok=True)
    health_fac_gdf = gpd.read_file(hcf_path)

    health_fac_gdf = dp_funcs.process_healthsites_hcf_data(health_fac_gdf)

    dp_funcs.save_hcf_data(processed_data_dir, health_fac_gdf)
