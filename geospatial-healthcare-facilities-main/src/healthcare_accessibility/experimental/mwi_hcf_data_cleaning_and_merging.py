"""
Script for cleaning and merging healthcare facility datasets (by Josh)

Uses multiple datasets from:
    data/

Run:
    src\polygon_data_cleaning.py
"""

# %%
# Import necessary libraries
from pathlib import Path

import pandas as pd
import geopandas as gpd
import numpy as np
import yaml

import healthcare_accessibility.geospatial_utils as geo_util
import healthcare_accessibility.osm_utils as osm_util
import healthcare_accessibility.data_processing_funcs as processing_funcs
import healthcare_accessibility.utils as utils

# %%
# Set path to data folder
config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

visualisation_crs = config.get("visualisation_crs")

data_dir = Path(config.get("data_dir"))

processed_output_dir = datasets.get("health_facility").get("processed")

processed_output_dir = utils.setup_sub_dir(data_dir, processed_output_dir)
# %%
# Load the dataset
elizabeth_foundatation_gdf = geo_util.load_georeferenced_csv_or_xlsx(
    file_path=config.get("data_dir") + datasets.get("health_facility").get("eliz_data"),
    lat_col="LATITUDE",
    lon_col="LONGITUDE",
    sheet_name="SITE LIST with COORDINATES",
    desired_crs=visualisation_crs,
)


# Rename column for consistency
elizabeth_foundatation_gdf = processing_funcs.rename_hc_fac_columns(
    elizabeth_foundatation_gdf
)


# %%
# Figshare dataset

figshare_file_path = datasets.get("health_facility").get("figshare")
malawi_figshare_gdf = processing_funcs.load_and_process_figshare_data(
    config, figshare_file_path, visualisation_crs
)


# %%
# Use import function to clean OSM gdf
health_facilities_points = osm_util.osm_gdf_clean(
    file_path=config.get("data_dir")
    + datasets.get("health_facility").get("hotosm_mwi_points")
)

health_facilities_points = processing_funcs.rename_hc_fac_columns(
    health_facilities_points
)

# %%
# Load dataframe
baobab_health_facilities_data_gdf = geo_util.load_georeferenced_csv_or_xlsx(
    file_path=config.get("data_dir") + datasets.get("health_facility").get("baobab"),
    lat_col="latitude",
    lon_col="longitude",
    sheet_name="csv",
    desired_crs=visualisation_crs,
)

# %%
# Check for null values in the dataset
baobab_health_facilities_data_gdf.info()

# %%
# Drop unnecessary columns
# Catchment Population (2018), Unnamed: 11, Unnamed: 12, Unnamed: 13, Unnamed: 14, Unnamed: 15, Unnamed: 16, Unnamed: 17
baobab_health_facilities_data_gdf.drop(
    columns=[
        "Catchment Population (2018)",
        "longitude",
        "latitude",
    ],
    inplace=True,
)

baobab_health_facilities_data_gdf = baobab_health_facilities_data_gdf.loc[
    :, ~baobab_health_facilities_data_gdf.columns.str.lower().str.contains("nnamed:")
]
# %% [markdown]
# Need to rename some columns so they are the same

# %% [markdown]
# malawi_figshare_gdf has `Facility name` and `Facility type`
# health_facilities_points has `name` and `amenity`
# baobab has `Facility Name` and `Facility Type`

# %%
# Load dataframe
MHF_2023 = gpd.read_file(
    config.get("data_dir") + datasets.get("health_facility").get("2023_malawai_hcf")
)
MHF_2023.head()

# %%
# Drop unnecessary columns
MHF_2023.drop(
    columns=["CODE", "LATITUDE", "LONGITUDE", "ZONE", "DATE OPENE", "COMMON NAM"],
    inplace=True,
)

# %%
# Rename columns for consistency
MHF_2023.rename(
    columns={
        "NAME": "Facility Name",
        "TYPE": "Facility Type",
        "OWNERSHIP": "Facility Ownership",
        "STATUS": "Status",
        "DISTRICT": "District",
    },
    inplace=True,
)

# %%
MHF_2023.head()

# %%
MHF_2023 = geo_util.general_df_or_gdf_clean(data=MHF_2023, df_or_gdf="gdf")

# %%
# Removed first row as contains useless info
MHF_2023 = MHF_2023[1 : len(MHF_2023)]

# %% [markdown]
# This dataset had facilities with polygons which centroid found for

# %%
# This data file was cleaned in `polygon_data_cleaning.py`

polygons_to_points_gdf = osm_util.convert_hcf_polygons_to_points(
    config, save_output=True
)


# %% [markdown]
# This dataset has no geometry but facility names

# %%
# This dataset has no geometry
master_health_list_csv = pd.read_csv(
    config.get("data_dir") + datasets.get("health_facility").get("master_health_list")
)

# %%
master_health_list_csv.info()

# %%
master_health_list_csv = geo_util.general_df_or_gdf_clean(
    data=master_health_list_csv, df_or_gdf="df"
)

# %%
# Rename column headers for consistency
master_health_list_csv.rename(
    columns={
        "Managing Authority": "Facility Ownership",
        "Urban/Rural": "Facility Location",
    },
    inplace=True,
)

# Drop Zone column
master_health_list_csv.drop(columns=["Zone"], inplace=True)

# %%
# Convert to GeoDataFrame without geometry
master_health_list_gdf = gpd.GeoDataFrame(master_health_list_csv)

# %% [markdown]
# CONCAT Datasets

# %% [markdown]
# Check if any geometries and/or facility names are the same in the 6 datasets

# %%
# Load the dataset
mhfr_facilities = geo_util.load_georeferenced_csv_or_xlsx(
    file_path=config.get("data_dir") + datasets.get("health_facility").get("zipatala"),
    lat_col="LATITUDE",
    lon_col="LONGITUDE",
    sheet_name="Facilities",
    desired_crs=visualisation_crs,
)

# %%
# Drop unneeded columns
mhfr_facilities.drop(
    columns=[
        "COMMON NAME",
        "DATE OPENED",
        "ZONE",
        "CODE",
        "DISTRICT",
        "LONGITUDE",
        "LATITUDE",
    ],
    inplace=True,
)

# Rename column for consistency
mhfr_facilities.rename(
    columns={
        "NAME": "Facility Name",
        "TYPE": "Facility Type",
    },
    inplace=True,
)

# %%
# Remove first row - contains irrelevant info
mhfr_facilities = mhfr_facilities[1:]

# Reset index after sorting
mhfr_facilities.reset_index(drop=True, inplace=True)

# %%
mhfr_facilities = geo_util.general_df_or_gdf_clean(
    data=mhfr_facilities, df_or_gdf="gdf"
)
# %%
# Has no facility names
MPSA = gpd.read_file(
    config.get("data_dir") + datasets.get("health_facility").get("MPSA")
)

MPSA.rename(
    columns={
        "SPAREGNA": "Region",
        "SPAMANGN": "Facility Ownership",
        "ADM1NAME": "District",
        "SPAFACID": "Unique ID",
        "SPAID": "Facility ID",
    },
    inplace=True,
)

# Drop unneeded columns
MPSA.drop(
    columns=[
        "DHSCC",
        "FIPSCC",
        "SPAYEAR",
        "ADM1CODE",
        "SPAREGCO",
        "SPATYPEC",
        "SPATYPEN",
        "SPAMANGC",
        "SOURCE",
        "DATUM",
        "LATNUM",
        "LONGNUM",
    ],
    inplace=True,
)

MPSA = geo_util.general_df_or_gdf_clean(data=MPSA, df_or_gdf="gdf")


# %%
WHO_gdf = geo_util.load_csv_or_xlsx_not_georeferenced(
    file_path=config.get("data_dir") + datasets.get("health_facility").get("WHO"),
    sheet_name=None,
    crs=visualisation_crs,
)

# %%
# Need to rename ID as Unique ID
# Drop unneeded columns
WHO_gdf.drop(columns=["ID", "Country"], inplace=True)

# Rename column for consistency
WHO_gdf.rename(
    columns={
        "Administrative location": "Region",
        "Owner": "Facility Ownership",
        "Type": "Facility Information",
    },
    inplace=True,
)

# %%
WHO_gdf = geo_util.general_df_or_gdf_clean(data=WHO_gdf, df_or_gdf="df")

# %%
# Order values alphabetically by Facility Name for better readability
WHO_gdf.sort_values(by="Facility Name", inplace=True)

# %%
# Reset index after sorting
WHO_gdf.reset_index(drop=True, inplace=True)

# %%
WHO_gdf.head()

# %% [markdown]
# - Join gdf by `Facility Name` and `geometry`

# %%
# Combine 8 gdf
complete_malawi_health_facilities = pd.concat(
    [
        malawi_figshare_gdf,
        health_facilities_points,
        MHF_2023,
        baobab_health_facilities_data_gdf,
        polygons_to_points_gdf,
        master_health_list_gdf,
        mhfr_facilities,
        MPSA,
        WHO_gdf,
    ],
    ignore_index=True,
)

# %%
# Do some initial cleaning on complete gdf
complete_malawi_health_facilities = geo_util.general_df_or_gdf_clean(
    data=complete_malawi_health_facilities, df_or_gdf="gdf"
)

# %% [markdown]
# Explore facility type

# %%
# Cleaning of facilty columns
complete_malawi_health_facilities = geo_util.gdf_facility_column_clean(
    gdf=complete_malawi_health_facilities
)

complete_malawi_health_facilities = geo_util.gdf_facility_name_clean(
    gdf=complete_malawi_health_facilities
)

# %%
# Check null values for facility names column
complete_malawi_health_facilities["Facility Name"].isnull().value_counts()

# %%
# Define the columns to clean
ownership_columns = ["Facility Ownership", "Ownership"]

# Define the replacements
ownership_replacements = {
    "Moh": "MoH",
    "Ngo": "NGO",
    "Fbo": "FBO",
    "Local Gvt": "Local Government",
    "Mission/ Faith-Based (Other Than Cham)": "Mission/Faith-Based (Other Than Cham)",
}

# Apply replacements to each column if it exists
for col in ownership_columns:
    if col in complete_malawi_health_facilities.columns:
        complete_malawi_health_facilities[col] = complete_malawi_health_facilities[
            col
        ].replace(ownership_replacements)

# %%
# Merge columns of Ownership into Facility Ownership as has more categories
complete_malawi_health_facilities["Facility Ownership"] = (
    complete_malawi_health_facilities["Facility Ownership"].combine_first(
        complete_malawi_health_facilities["Ownership"]
    )
)

# %% [markdown]
# Load admin boundaries

# %%
# Use imported function for ADM1
malawi_regions = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("geoboundaries_ADM1"),
    column_name_to_change="Region",
)

# Make upper case
malawi_regions["Region"] = malawi_regions["Region"].str.upper()

# %%
# Use imported function for ADM2
malawi_districts = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("geoboundaries_ADM2"),
    column_name_to_change="District",
)

# Make upper case
malawi_districts["District"] = malawi_districts["District"].str.upper()
# %%
# Use imported function for ADM3
malawi_authorities = geo_util.clean_gdf_boundaries(
    file_path=config.get("data_dir")
    + datasets.get("admin_boundary").get("geoboundaries_ADM3"),
    column_name_to_change="Authority",
)

# Make upper case
malawi_authorities["Authority"] = malawi_authorities["Authority"].str.upper()

# %% [markdown]
# Spatial join here to confirm Region, District and Authority

# %%
# Join Regions with complete malawai health care facilities
complete_malawi_health_facilities = gpd.sjoin(
    complete_malawi_health_facilities, malawi_regions, how="left", predicate="within"
)

# %%
# Drop unneeded columns
complete_malawi_health_facilities.drop(
    columns=["index_right", "Region_left"], inplace=True
)

# Change column name for Region
complete_malawi_health_facilities.rename(
    columns={"Region_right": "Region"}, inplace=True
)

# %%
# Join Districts with complete malawai health care facilities
complete_malawi_health_facilities = gpd.sjoin(
    complete_malawi_health_facilities, malawi_districts, how="left", predicate="within"
)

# %%
# Drop unneeded columns
complete_malawi_health_facilities.drop(
    columns=["index_right", "District_left"], inplace=True
)

# Change column name for District
complete_malawi_health_facilities.rename(
    columns={"District_right": "District"}, inplace=True
)

# %%
# Join Authorities with complete malawai health care facilities
complete_malawi_health_facilities = gpd.sjoin(
    complete_malawi_health_facilities,
    malawi_authorities,
    how="left",
    predicate="within",
)

# %%
# Drop unneeded columns
complete_malawi_health_facilities.drop(columns=["index_right"], inplace=True)

# %%
complete_malawi_health_facilities.head()

# %%
# Change POINT EMPTY to None to prepare for back/forward fill
complete_malawi_health_facilities["geometry"] = complete_malawi_health_facilities[
    "geometry"
].apply(geo_util.geometry_to_none)
# %% [markdown]
# Look for duplicates

# %%
# Find only duplicate facility names (includes null facility names)
pre_imputed_duplicate_facility_names = complete_malawi_health_facilities[
    complete_malawi_health_facilities.duplicated(subset=["Facility Name"])
]
pre_imputed_duplicate_facility_names.to_csv(
    processed_output_dir / "pre_imputed_duplicate_facility_names.csv"
)
pre_imputed_duplicate_facility_names

# %%
# Find only duplicate geometries (includes null facility names)
pre_imputed_duplicate_geometries = complete_malawi_health_facilities[
    complete_malawi_health_facilities.duplicated(subset=["geometry"])
]
pre_imputed_duplicate_geometries.to_csv(
    processed_output_dir / "pre_imputed_duplicate_geometries.csv"
)
pre_imputed_duplicate_geometries

# %% [markdown]
# Need to backfill/forwardfill to get rid of null values for
# healthcare facilities with same name as geometries may be same

# %%
# Opt into the future behavior
pd.set_option("future.no_silent_downcasting", True)

# Create imputed values - group by 'Facility Name' and fill missing values of duplicates using forward and backward fill
df_imputed = complete_malawi_health_facilities.groupby("Facility Name").transform(
    lambda group: group.ffill().bfill()
)

# %%
# Update original DataFrame with imputed values and inplace true
complete_malawi_health_facilities.update(df_imputed)

# %%
# Save all including duplicates
complete_malawi_health_facilities.to_csv(
    processed_output_dir / "all_hcf_including_duplicates.csv"
)
complete_malawi_health_facilities.to_file(
    processed_output_dir / "all_hcf_including_duplicates.gpkg", driver="GPKG"
)

# %%
# Find only duplicate facility names now imputed (includes null facility names)
post_imputed_duplicate_facility_names = complete_malawi_health_facilities[
    complete_malawi_health_facilities.duplicated(subset=["Facility Name"])
]
post_imputed_duplicate_facility_names.to_csv(
    processed_output_dir / "post_imputed_duplicate_facility_names.csv"
)
post_imputed_duplicate_facility_names

# %%
# Find only duplicate geometries now imputed (includes null facility names)
post_imputed_duplicate_geometries = complete_malawi_health_facilities[
    complete_malawi_health_facilities.duplicated(subset=["geometry"])
]
post_imputed_duplicate_geometries.to_csv(
    processed_output_dir / "post_imputed_duplicate_geometries.csv"
)
post_imputed_duplicate_geometries

# %% [markdown]
# No difference in numbers of duplicates pre and post imputation

# %%
# Check unique values in healthcare column
complete_malawi_health_facilities["Healthcare"].value_counts()

# %%
# Remove healthcare column as it is not needed for the analysis
# More relevant info in Facility Type column
complete_malawi_health_facilities.drop(columns=["Healthcare"], inplace=True)

# %% [markdown]
# Are these close to any healthcare facilities?

# %%
# View rows where Facility Name null but geometry present post imputation
# (save to gdf or visualise?)
geometry_with_no_health_facility_name = post_imputed_duplicate_facility_names[
    post_imputed_duplicate_facility_names["Facility Name"].isnull()
    & post_imputed_duplicate_facility_names["geometry"].apply(
        lambda x: str(x) != "POINT (NaN NaN)"
    )
]

# %% [markdown]
# These have no Reg No. or Facility Code

# %%
# View rows where Facility Name present but geometry null (includes duplicates) post imputation
# These all have facility codes
# (save to gdf)
no_geometry_with_health_facility_name = post_imputed_duplicate_facility_names[
    post_imputed_duplicate_facility_names["Facility Name"].notnull()
    & post_imputed_duplicate_facility_names["geometry"].apply(
        lambda x: str(x) == "POINT (NaN NaN)"
    )
]
no_geometry_with_health_facility_name.to_csv(
    processed_output_dir / "no_geometry_with_health_facility_name.csv"
)
no_geometry_with_health_facility_name.head(10)

# %% [markdown]
# - Can't plot
# - Some have facility code and Reg No. so might be able to be identified

# %% [markdown]
# Complete Malawi Health Facilities

# %%
# Complete Malawi Health Facilities - only rows with both facility names and geometries present
# Only rows where Region, District and Authority not missing
complete_malawi_health_facilities_and_geometries = complete_malawi_health_facilities[
    (
        complete_malawi_health_facilities["geometry"].apply(
            lambda x: str(x) != "POINT (NaN NaN)"
        )
    )
    & (complete_malawi_health_facilities["Facility Name"].notnull())
    & (complete_malawi_health_facilities["Region"].notnull())
    & (complete_malawi_health_facilities["District"].notnull())
    & (complete_malawi_health_facilities["Authority"].notnull())
    & (complete_malawi_health_facilities["Facility ID"].notnull())
    & (complete_malawi_health_facilities["Unique ID"].notnull())
]

# %%
# If wanting duplicates and Facilities with no names
complete_malawi_health_facilities_and_geometries = complete_malawi_health_facilities

# %%
# View duplicated rows (contains both copies) in complete dataset
# Some geometries are slightly different but same Facility Name
duplicated_complete_malawi_health_facilities_and_geometries = (
    complete_malawi_health_facilities_and_geometries[
        complete_malawi_health_facilities_and_geometries.duplicated(
            subset=["Facility Name"], keep=False
        )
    ]
)

# Can use this to plot to see differences
duplicated_complete_malawi_health_facilities_and_geometries.to_csv(
    processed_output_dir / "no_geometry_with_health_facility_name.csv"
)

# Save duplicates to outputs_dir as a gpkg file
duplicated_complete_malawi_health_facilities_and_geometries.to_file(
    processed_output_dir / "duplicated_complete_malawi_health_facilities.gpkg",
    driver="GPKG",
)

duplicated_complete_malawi_health_facilities_and_geometries

# %%

# Keep only one row per unique Facility Name
named_facility = complete_malawi_health_facilities_and_geometries[
    complete_malawi_health_facilities_and_geometries["Facility Name"].notnull()
].drop_duplicates(subset=["Facility Name"])

# Keep rows that have Facility ID or Unique ID, regardless of name
has_id = complete_malawi_health_facilities_and_geometries[
    complete_malawi_health_facilities_and_geometries["Facility ID"].notnull()
    | complete_malawi_health_facilities_and_geometries["Unique ID"].notnull()
]

# Combine both sets and drop any duplicates
cleaned_complete_malawi_health_facilities_and_geometries = pd.concat(
    [named_facility, has_id]
).drop_duplicates()

# %% [markdown]
# Combine Facility Ownership and Ownership columns

# %%
# Filter rows where both 'Ownership' and 'Facility Ownership' are not null
both_facility_owners_present = cleaned_complete_malawi_health_facilities_and_geometries[
    cleaned_complete_malawi_health_facilities_and_geometries["Ownership"].notna()
    & cleaned_complete_malawi_health_facilities_and_geometries[
        "Facility Ownership"
    ].notna()
]

# Two facility owners saved to csv
both_facility_owners_present.to_csv(
    processed_output_dir / "two_facility_owners_comparison.csv"
)

# %%
# Merging the columns.
# Facility Ownership has more categories so will use that for now
cleaned_complete_malawi_health_facilities_and_geometries["Facility Ownership"] = (
    cleaned_complete_malawi_health_facilities_and_geometries[
        "Facility Ownership"
    ].combine_first(
        cleaned_complete_malawi_health_facilities_and_geometries["Ownership"]
    )
)

# %%
# Fill missing 'Unique ID' values with 'Facility Code' values
cleaned_complete_malawi_health_facilities_and_geometries["Unique ID"] = (
    cleaned_complete_malawi_health_facilities_and_geometries["Unique ID"].fillna(
        cleaned_complete_malawi_health_facilities_and_geometries["Facility Code"]
    )
)

# %%
# Drop unneeded column
cleaned_complete_malawi_health_facilities_and_geometries.drop(
    columns=["Ownership", "District Code", "Reg No.", "Country"],
    inplace=True,
)

# %%
# Yes value in Facility Type column.
# Replace 'Yes' with NaN
cleaned_complete_malawi_health_facilities_and_geometries.replace(
    "Yes", np.nan, inplace=True
)

# %%
# Reset index
cleaned_complete_malawi_health_facilities_and_geometries.reset_index(
    drop=True, inplace=True
)

# %%
# List of columns to convert to uppercase
columns_to_uppercase = [
    "Facility Name",
    "Facility Ownership",
    "Status",
    "Facility Location",
    "Facility Information",
    "Region",
    "District",
    "Authority",
]

# Apply uppercase transformation
cleaned_complete_malawi_health_facilities_and_geometries[columns_to_uppercase] = (
    cleaned_complete_malawi_health_facilities_and_geometries[
        columns_to_uppercase
    ].apply(lambda col: col.str.upper())
)

# %%
# Extract latitude and longitude from the geometry column
cleaned_complete_malawi_health_facilities_and_geometries["Longitude"] = (
    cleaned_complete_malawi_health_facilities_and_geometries.geometry.x
)
cleaned_complete_malawi_health_facilities_and_geometries["Latitude"] = (
    cleaned_complete_malawi_health_facilities_and_geometries.geometry.y
)
# Reset index
cleaned_complete_malawi_health_facilities_and_geometries.reset_index(
    drop=True, inplace=True
)

# %%
# Identify rows with missing 'Facility Name', these are from MPSA dataset most likely
missing_facility_names = cleaned_complete_malawi_health_facilities_and_geometries[
    cleaned_complete_malawi_health_facilities_and_geometries["Facility Name"].isnull()
]

# Save missing names to CSV
missing_facility_names.to_csv("missing_facility_names_mpsa.csv", index=False)

# Drop those rows from the original GeoDataFrame
cleaned_complete_malawi_health_facilities_and_geometries = (
    cleaned_complete_malawi_health_facilities_and_geometries.dropna(
        subset=["Facility Name"]
    )
)

# %%
# Recreate lat and long columns
cleaned_complete_malawi_health_facilities_and_geometries["Longitude"] = (
    cleaned_complete_malawi_health_facilities_and_geometries.geometry.centroid.x
)
cleaned_complete_malawi_health_facilities_and_geometries["Latitude"] = (
    cleaned_complete_malawi_health_facilities_and_geometries.geometry.centroid.y
)


# %%
# Create new Unique ID
cleaned_complete_malawi_health_facilities_and_geometries["Unique ID"] = (
    cleaned_complete_malawi_health_facilities_and_geometries.apply(
        lambda row: processing_funcs.generate_hashed_id(
            f"{row['Facility Name']}_{row['District']}_{row['Region']}", length=8
        ),
        axis=1,
    )
)

# %%
# Save complete gdf ready for data exploration
cleaned_complete_malawi_health_facilities_and_geometries.to_file(
    processed_output_dir / "cleaned_malawi_health_facilities.gpkg", driver="GPKG"
)

cleaned_complete_malawi_health_facilities_and_geometries.to_csv(
    processed_output_dir / "cleaned_malawi_health_facilities.csv"
)

# %%
