import geopandas as gpd
import pandas as pd
import yaml
import string
import random
from datetime import datetime

import healthcare_accessibility.geospatial_utils as geo_util


def rename_hc_fac_columns(
    df,
    desired_facility_name_header="Facility Name",
    desired_facility_type_header="Facility Type",
    desired_ADM1_header="Region",
):
    """
    Rename columns in a DataFrame based on a common mappings.

    Parameters:
    - df: pandas DataFrame, the DataFrame whose columns need to be renamed.

    Returns:
    - pandas DataFrame with renamed columns.
    """

    column_mapping = {
        "SITE NAME": desired_facility_name_header,
        "Facility name": desired_facility_name_header,
        "Facility type": desired_facility_type_header,
        "Admin1": desired_ADM1_header,
        "name": desired_facility_name_header,
        "amenity": desired_facility_type_header,
    }
    return df.rename(columns=column_mapping)


def load_and_process_figshare_data(config, file_path, desired_crs, country="Malawi"):
    """
    Load and process the Figshare healthcare facility dataset.

    Returns:
    - geopandas GeoDataFrame containing Malawi's healthcare facilities with cleaned columns.
    """

    figshare_gdf = geo_util.load_georeferenced_csv_or_xlsx(
        file_path=config.get("data_dir") + file_path,
        lat_col="Lat",
        lon_col="Long",
        sheet_name="SSA MFL",
        desired_crs=desired_crs,
    )

    # Select Malawi's data
    malawi_figshare_gdf = figshare_gdf[figshare_gdf["Country"] == country].reset_index(
        drop=True
    )
    malawi_figshare_gdf.head()

    # Drop Lat and long columns
    malawi_figshare_gdf.drop(columns=["Lat", "Long", "LL source"], inplace=True)

    # Change column names
    # Facility name to Facility Name, Facility type to Facility Type and Admin1 to Region
    malawi_figshare_gdf = rename_hc_fac_columns(malawi_figshare_gdf)

    return malawi_figshare_gdf


def select_fac_subset(health_fac_gdf, filtering_str, filtering_col="Facility type"):
    """
    Filters a GeoDataFrame of health facilities to return only those facilities
    whose 'Facility Type' column contains the specified substring,
    regardless of case sensitivity.

    Parameters
    ----------
    health_fac_gdf : GeoDataFrame
        The input GeoDataFrame containing health facility data, including a 'Facility Type' column.
    filtering_str : str
        Substring to search for within the desired column.
    filtering_col : str, optional
        The name of the column in the GeoDataFrame that contains the desired
        information to filter on. Default is 'Facility type'.

    Returns
    -------
    sub_hcf_gdf : GeoDataFrame
        A subset of the input GeoDataFrame containing facilities that match the given type.
    """
    sub_hcf_gdf = health_fac_gdf[
        health_fac_gdf[filtering_col].str.contains(filtering_str, case=False, na=False)
    ]
    return sub_hcf_gdf


def save_data(mode_of_transport, facility, travel_gdf, fac_sub, config):
    """
    Saves travel time results to a CSV file and returns the subset of facilities used in the analysis.

    Parameters
    ----------
    mode_of_transport : str
        Transport mode used for travel time calculation (e.g., 'bicycle', 'car').
    facility : str
        Name or type of the healthcare facility (e.g., 'Hospital').
    travel_gdf : GeoDataFrame
        GeoDataFrame containing travel time results from origin points to facilities.
    fac_sub : GeoDataFrame
        Subset of healthcare facilities used in the travel time analysis.
    config : dict-like
        Configuration object containing output directory paths.

    Returns
    -------
    hcf_sub : DataFrame
        DataFrame containing the unique subset of facilities used, including their names and types.
    """

    output_df = pd.merge(
        travel_gdf,
        fac_sub,
        left_on="to_id",
        right_on="Facility Name",
        how="left",
        suffixes=["_grid", "_hcf"],
    )

    # Select desired columns from the merged DataFrame
    columns_to_keep = [
        "Facility Name",
        "Facility Type",
        "geometry_hcf",
        "Facility Ownership",
        "Status",
        "Facility Location",
        # "Facility Code",
        "Facility Information",
        "Region",
        "District",
        "Authority",
        "Longitude",
        "Latitude",
        "travel_time",
    ]

    # Drop duplicates based on facility name & type, using correct column names
    # from the merged DataFrame and rename columns for clarity
    hcf_sub = output_df.drop_duplicates(subset=["Facility Name", "Facility Type"])[
        columns_to_keep
    ].rename(columns={"geometry_hcf": "geometry"})

    # Convert to GeoDataFrame for spatial operations and mapping
    hcf_sub = gpd.GeoDataFrame(hcf_sub, geometry=hcf_sub["geometry"], crs=fac_sub.crs)

    # Save full merged output to CSV
    output_df.to_csv(
        config.get("outputs_dir")
        + f"{mode_of_transport}_travel_times_to_{facility}.csv",
        index=False,
    )

    return hcf_sub


def load_population_grid(config, analysis_crs, pop_grid="wp_2025_1km"):
    """
    Load and vectorize population grid raster into geodataframe.

    Parameters
    ----------
    config : dict
        Configuration dictionary from loading config YAML file
    analysis_crs : str
        The desired CRS for the loaded data

    Returns
    -------
    geopandas.GeoDataFrame
        Geodataframe of population grid data.
    """

    print("Loading population grid data...")

    with open(config.get("datasets_config")) as file:
        datasets = yaml.safe_load(file)

    pop_grid_path = config.get("data_dir") + datasets.get("population").get(pop_grid)

    pop_grid_gdf = geo_util.load_and_vectorize_grid_tif(grid_tif_path=pop_grid_path)
    pop_grid_gdf = geo_util.set_crs(pop_grid_gdf, analysis_crs)

    # Add "id" column as required for r5py
    pop_grid_gdf["id"] = pop_grid_gdf.index.astype(str)

    return pop_grid_gdf


def load_administrative_boundaries(config, analysis_crs, admin_level):
    """
    Load administrative boundaries (districts and regions) as geodataframes.

    Parameters
    ----------
    config : dict
        Configuration dictionary from loading config YAML file
    analysis_crs : str
        The desired CRS for the loaded data

    Returns
    -------
    tuple
        Tuple containing geodataframes of districts and regions.
    """
    print(f"Loading {admin_level} administrative boundaries...")

    with open(config.get("datasets_config")) as file:
        datasets = yaml.safe_load(file)

    if admin_level not in ["ADM1", "ADM2"]:
        raise ValueError("Admin_level must be either 'ADM1' or 'ADM2'")

    # Load administrative boundaries (districts)
    geoboundaries_gdf = geo_util.clean_gdf_boundaries(
        file_path=config.get("data_dir")
        + datasets.get("admin_boundary").get(f"geoboundaries_{admin_level}"),
        column_name_to_change=admin_level,
    )
    # Change column name for consistency
    geoboundaries_gdf.rename(columns={"name": admin_level}, inplace=True)
    geoboundaries_gdf_reproj = geoboundaries_gdf.copy().to_crs(analysis_crs)

    return geoboundaries_gdf_reproj


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """Generate a random unique string to be used as an identifier."""
    return "".join(random.choice(chars) for _ in range(size))


def clean_hcf_data(hcf_gdf):
    """Clean health facility geodataframe by removing invalid geometries and duplicates."""
    hcf_gdf["str_geom"] = hcf_gdf.geometry.apply(str)
    hcf_gdf_clean = hcf_gdf[~hcf_gdf.str_geom.str.contains("EMPTY")]
    hcf_gdf_clean = hcf_gdf_clean[hcf_gdf_clean.geometry.notnull()]
    hcf_gdf_clean = hcf_gdf_clean.drop_duplicates(subset=["str_geom"]).reset_index(
        drop=True
    )
    return hcf_gdf_clean


def attach_unique_id_column(gdf, save_lookup=False):
    """Generate a random unique identifier for each row in the geodataframe."""
    gdf["uid"] = 1
    gdf["uid"] = gdf["uid"].apply(lambda x: x * id_generator(10))
    if save_lookup:
        todays_date = datetime.now().strftime("%Y-%m-%d")
        gdf.to_csv(f"health_facility_uid_lookup_{todays_date}.csv")
    return gdf


def load_and_process_hcf_data(
    config, config_key="cleaned_hcf", id_column="Facility Name", existing_lookup=None
):
    """
    Load and process health facility data.

    Parameters
    ----------
    config : dict
        Configuration dictionary containing paths and settings.
    config_key : str, optional
        Key in the datasets config for the health facility data, by default "cleaned_hcf".
    id_column : str, optional
        Column name to use for unique identifiers, by default "Facility Name".

    Returns
    -------
    geopandas.GeoDataFrame
        Processed health facility geodataframe.
    """

    with open(config.get("datasets_config")) as file:
        datasets = yaml.safe_load(file)

    # Load health facility data with georeferenced coordinates
    health_fac_gdf = gpd.read_file(
        config.get("data_dir") + datasets.get("health_facility").get(config_key)
    )

    analysis_crs = config.get("analysis_crs")

    # r5py.TravelTimeMatrix expects origin and destination GeoDataFrames to have id column
    health_fac_gdf["id"] = health_fac_gdf[id_column]

    if existing_lookup:
        health_fac_lookup = pd.read_csv(
            f"health_facility_uid_lookup_{existing_lookup}.csv"
        )
        lookup_cols = health_fac_lookup.columns[1:-1]
        # health_fac_gdf = pd.merge(
        #     health_fac_gdf,
        #     health_fac_lookup,
        #     how="left",
        #     left_on=health_fac_gdf.columns,
        #     right_on=lookup_cols,
        # )
        health_fac_lookup.join(health_fac_gdf, on=[id_column, id_column])
    else:
        health_fac_gdf = attach_unique_id_column(health_fac_gdf, save_lookup=True)

    health_fac_gdf = clean_hcf_data(health_fac_gdf)

    health_fac_gdf = health_fac_gdf.to_crs(analysis_crs)

    return health_fac_gdf
