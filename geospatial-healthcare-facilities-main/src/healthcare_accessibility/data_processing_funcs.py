import geopandas as gpd
import pandas as pd
import yaml
import string
import random
from datetime import datetime
import janitor
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import re
from rapidfuzz import process, fuzz
import hashlib
import folium
from sklearn.cluster import DBSCAN
import zipfile
import requests

import healthcare_accessibility.geospatial_utils as geo_util
import healthcare_accessibility.utils as utils


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


def save_data(
    travel_time_matrix,
    mode_of_transport,
    facility,
    output_dir,
    output_file_format="csv",
):
    """
    Saves travel time results to a CSV file or parquet file.

    Parameters
    ----------
    travel_time_matrix : pd.DataFrame
        DataFrame containing travel time results from origin points to facilities.
    mode_of_transport : str
        Transport mode used for travel time calculation (e.g., 'bicycle', 'car').
    facility : str
        Name or type of the healthcare facility (e.g., 'Hospital').

    """
    if output_file_format == "csv":
        # Output full travel time matrix to CSV
        travel_time_matrix.to_csv(
            output_dir.joinpath(f"{mode_of_transport}_travel_times_to_{facility}.csv"),
            index=False,
        )
    elif output_file_format == "parquet":
        # Output full travel time matrix as parquet file
        # (useful for car travel which can be large and slow to read/write as CSV)
        travel_time_matrix_tbl = pa.Table.from_pandas(travel_time_matrix)
        pq.write_table(
            travel_time_matrix_tbl,
            output_dir.joinpath(
                f"{mode_of_transport}_travel_times_to_{facility}.parquet"
            ),
            compression="GZIP",
        )


def return_population_path(config, pop_grid="wp_2025_1km"):
    """
    Load and vectorize population grid raster into geodataframe.

    Parameters
    ----------
    config : dict
        Configuration dictionary from loading config YAML file

    Returns
    -------
    str
        Path to the population grid data.
    """

    with open(config.get("datasets_config")) as file:
        datasets = yaml.safe_load(file)

    pop_grid_path = Path(
        config.get("data_dir") + datasets.get("population").get(pop_grid)
    )
    return pop_grid_path


def process_population_data(pop_grid_path):
    """
    Load, vectorize, and standardize a population raster for routing analysis.

    Parameters
    ----------
    pop_grid_path : str or pathlib.Path
        Path to a population raster file (typically GeoTIFF) to be loaded.

    Returns
    -------
    geopandas.GeoDataFrame
        Vectorized population grid with cleaned column names and an `id` column
        (string type) suitable for downstream r5py travel-time functions.
    """
    print(f"Loading population grid data {pop_grid_path.stem}...")
    pop_grid_gdf = geo_util.load_and_vectorize_grid_tif(grid_tif_path=pop_grid_path)

    # Add "id" column as required for r5py
    pop_grid_gdf["id"] = pop_grid_gdf.index.astype(str)

    pop_grid_gdf = pop_grid_gdf.clean_names()

    return pop_grid_gdf


def load_population_grid(config, pop_file_path=None, pop_grid="wp_2025_1km"):
    """
    Load and vectorize population grid raster into geodataframe.

    Parameters
    ----------
    config : dict
        Configuration dictionary from loading config YAML file
    pop_file_path: Path or str, optional
        Path to the population grid data file. If None, the path will be determined from the
    pop_grid: str, optional
        Key in the datasets config for the population grid data, by default "wp_2025_1km"

    Returns
    -------
    geopandas.GeoDataFrame
        Geodataframe of population grid data.
    """

    if pop_file_path is None:
        pop_file_path = return_population_path(config, pop_grid)

    pop_grid_gdf = process_population_data(pop_file_path)

    return pop_grid_gdf


def load_administrative_boundaries(file_path, admin_level, message=True):
    """
    Load administrative boundaries (districts and regions) as geodataframes.

    Parameters
    ----------
    file_path : dict
        File path to the admin datasets
    admin_level : str
        Administrative level to load, usually either "ADM1" for regions or "ADM2"
    message : bool, optional
        Whether to print a message when loading the administrative boundaries, by default True

    Returns
    -------
    tuple
        Tuple containing geodataframes of districts and regions.
    """
    if message:
        print(f"Loading {admin_level} administrative boundaries...")

    if admin_level not in ["ADM1", "ADM2"]:
        raise ValueError("Admin_level must be either 'ADM1' or 'ADM2'")

    # Load administrative boundaries (districts)
    geoboundaries_gdf = geo_util.clean_gdf_boundaries(
        file_path=file_path,
        column_name_to_change=admin_level,
    )
    # Change column name for consistency
    geoboundaries_gdf.rename(columns={"name": admin_level}, inplace=True)

    return geoboundaries_gdf


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


def recombine_travel_matrix_with_pop_data(
    travel_time_matrix_df: pd.DataFrame,
    pop_grid_gdf: gpd.GeoDataFrame,
    join_type="right",
) -> gpd.GeoDataFrame:
    """
    Merges travel time matrix with grid population data.

    Parameters
    ----------
    travel_time_matrix_df : pd.DataFrame
        Travel time matrix dataframe.
    pop_grid_gdf : geopandas.GeoDataFrame
        Population grid geodataframe.
    join_type : str, optional
        Type of join to perform (e.g., "left", "right", "inner", "outer"), by
        default "right".

    Returns
    -------
    geopandas.GeoDataFrame
        Merged geodataframe of travel times, population grid, and healthcare facilities.
    """

    # Merge travel time results with population grid data
    ttm_gdf = pop_grid_gdf.merge(
        travel_time_matrix_df,
        left_on="id",
        right_on="to_id",
        how=join_type,
    )

    return ttm_gdf


def return_nearest_travel_outcome(
    travel_gdf: gpd.GeoDataFrame,
    grid_cell_id_column: str = "to_id",
    travel_outcome_column: str = "travel_time",
) -> gpd.GeoDataFrame:
    """Return the minimum travel outcome (time or distance) for each grid cell
    to the nearest healthcare facility."""
    min_travel_gdf = travel_gdf.loc[
        travel_gdf.groupby(grid_cell_id_column)[travel_outcome_column].idxmin()
    ]
    return min_travel_gdf


def generate_hashed_id(value, prefix="ID_", length=5):
    """
    Generates a uniform-length hashed identifier using SHA-256.

    This function takes an input value, hashes it using the SHA-256 algorithm,
    and returns a string identifier with a specified prefix and truncated hash
    of fixed length.

    Parameters:
    ----------
    value : any
        The input value to be hashed. Typically a string or a combination of values.
    prefix : str, optional
        A string prefix to prepend to the hashed ID (default is 'ID_').
    length : int, optional
        The number of characters to retain from the beginning of the hash (default is 5).

    Returns:
    -------
    str
        A unique identifier string in the format: prefix + truncated hash.
    """

    hash_object = hashlib.sha256(str(value).encode())
    return prefix + hash_object.hexdigest()[:length]


def compare_travel_time_stats(gdf, column_of_interest):
    """
    Computes mean, min, and max travel times grouped by a specified column.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame containing travel time data and facility metadata.
    column_of_interest : str
        Column to group by (e.g., 'Facility Name', 'Facility Type', etc.)

    Returns
    -------
    pd.DataFrame
        DataFrame with travel time statistics grouped by the specified column.
    """

    # Fallback to 'to_id' if 'Facility Name' is not in the DataFrame
    if column_of_interest == "Facility Name" and column_of_interest not in gdf.columns:
        column_of_interest = "to_id"

    if column_of_interest in ["Facility Name", "to_id"]:
        facility_name_stats = {}

        for _, row in gdf.iterrows():
            name = row[column_of_interest]
            time = row["travel_time"]

            if name not in facility_name_stats:
                facility_name_stats[name] = []
            facility_name_stats[name].append(time)

        stat_data = {
            column_of_interest: [],
            "Mean_travel_time": [],
            "Shortest_travel_time": [],
            "Longest_travel_time": [],
        }

        for name, times in facility_name_stats.items():
            stat_data[column_of_interest].append(name)
            stat_data["Mean_travel_time"].append(round(pd.Series(times).mean(), 1))
            stat_data["Shortest_travel_time"].append(round(min(times), 1))
            stat_data["Longest_travel_time"].append(round(max(times), 1))

        stats_df = pd.DataFrame(stat_data)
        return stats_df

    elif column_of_interest in [
        "Facility Type",
        "Facility Ownership",
        "Facility Information",
    ]:
        unique_values = gdf[column_of_interest].dropna().unique()

        stat_data = {
            column_of_interest: [],
            "Mean_travel_time": [],
            "Shortest_travel_time": [],
            "Longest_travel_time": [],
        }

        for unique_value in unique_values:
            filtered_df = gdf[gdf[column_of_interest] == unique_value]

            stat_data[column_of_interest].append(unique_value)
            stat_data["Mean_travel_time"].append(
                round(filtered_df["travel_time"].mean(), 1)
            )
            stat_data["Shortest_travel_time"].append(
                round(filtered_df["travel_time"].min(), 1)
            )
            stat_data["Longest_travel_time"].append(
                round(filtered_df["travel_time"].max(), 1)
            )

        stats_df = pd.DataFrame(stat_data)
        return stats_df

    else:
        print("Column not found or try `to_id` if Facility Name didn't work")


def fuzz_match(value, choices, scorer=fuzz.token_set_ratio, threshold=92):
    """
    Performs fuzzy match between a Facility and a list of other facilities.

    Parameters:
    - value (str): the value to match against the list of choices
    - choices (pd.Series or list): the list of facilities to compare with the query
    - scorer (callable): a scoring function that takes two strings and returns a similarity score
    - threshold: the minimum score a match should make to be returned

    Returns:
    - The highest matched facility
    """
    match = process.extractOne(value, choices, scorer=scorer)
    if match and match[1] >= threshold:
        return match[0]
    else:
        return None


def compare_similar_facility_names(
    gdf,
    desired_analysis_crs,
    desired_visualisation_crs,
    radius,
    metric,
    latitude,
    longitude,
    output_dir,
):
    """
    Identifies and visualizes clusters of facilities with similar names and close geographic proximity.

    Parameters:
    ----------
    gdf : GeoDataFrame
        A GeoDataFrame containing facility names and geometries.

    desired_analysis_crs : str or int
        The CRS (Coordinate Reference System) to use for spatial analysis (e.g., EPSG:20936 for Malawi Local Grid).

    desired_visualisation_crs : str or int
        The CRS to use for map visualization (e.g., EPSG:4326 for latitude/longitude).

    radius : float
        The clustering radius in meters for DBSCAN to group nearby facilities.

    metric : str
        The distance metric to use in DBSCAN (e.g., 'euclidean', 'manhattan', etc.).

    latitude : float
        Latitude coordinate to center the Folium map.

    longitude : float
        Longitude coordinate to center the Folium map.

    output_dir : Path or str
        Directory path where the HTML map will be saved.

    Returns:
    -------
    filtered_gdf : GeoDataFrame
        A filtered GeoDataFrame containing only facilities that are part of proximity groups with two or more members.

    Side Effects:
    ------------
    - Prints facility names grouped by proximity cluster.
    - Saves an interactive Folium map to the specified output directory.
    """
    # Normalize geometries to ensure duplicates correctly identified
    gdf["geometry"] = gdf.geometry.normalize()

    # Reproject to EPSG:20936 (Malawi Local Grid, units in meters)
    gdf = gdf.to_crs(desired_analysis_crs)

    # Remove rows with null geometries
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[gdf.Latitude.notnull()]

    # Extract coordinates for clustering
    coords = gdf.geometry.apply(lambda geom: (geom.x, geom.y)).tolist()

    # Apply DBSCAN clustering with 300 meter radius
    db = DBSCAN(eps=radius, min_samples=1, metric=metric)
    gdf["Proximity Group"] = db.fit_predict(coords)

    # Count facilities per cluster
    cluster_sizes = gdf["Proximity Group"].value_counts()

    # Filter clusters with 2 facilities that are close
    two_clusters_or_more = cluster_sizes[cluster_sizes >= 2]
    filtered_gdf = gdf[gdf["Proximity Group"].isin(two_clusters_or_more)]

    # Print the results
    for cluster_id in two_clusters_or_more.index:
        members = gdf[gdf["Proximity Group"] == cluster_id]["Facility Name"].tolist()
        print(f"Proximity Group {cluster_id} ({len(members)} facilities): {members}")

    # Convert to latitude/longitude for Folium display
    filtered_gdf = filtered_gdf.to_crs(desired_visualisation_crs)

    # Create a Folium map centered on the mean location
    map_of_potential_duplicates = folium.Map(
        location=[latitude, longitude], zoom_start=8
    )

    # Add markers with popups
    for _, row in filtered_gdf.iterrows():
        lat = row.geometry.y
        lon = row.geometry.x
        popup_text = f"Facility Name: {row['Facility Name']}"
        folium.Marker(location=[lat, lon], popup=popup_text).add_to(
            map_of_potential_duplicates
        )

    # Save the map
    map_of_potential_duplicates.save(output_dir / "clustered_facilities_map.html")

    return filtered_gdf


def assign_boundary_grids_by_area(pop_gdf_adm, admin_gdf, admin_id_col):
    """
    Assign grid cells that intersect multiple administrative areas to the area
    with which they have the largest overlap.

    Parameters
    ----------
    pop_gdf_adm : geopandas.GeoDataFrame
        GeoDataFrame containing the population grid cells with administrative area assignments.
    admin_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing the administrative boundaries.
    admin_id_col : str
        Column name in admin_gdf that contains the unique identifier for each administrative area.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame with grid cells assigned to the administrative area with the largest overlap.
    """
    boundary_grids = pop_gdf_adm[pop_gdf_adm.duplicated(subset=["id"], keep=False)]

    boundary_intersections = gpd.overlay(boundary_grids, admin_gdf, how="intersection")

    boundary_intersections["overlap_area"] = boundary_intersections.geometry.area

    boundary_intersections_sorted = boundary_intersections.sort_values(
        ["id", "overlap_area"], ascending=False
    )

    biggest_area_df = boundary_intersections_sorted.drop_duplicates(
        subset=["id"], keep="first"
    )

    resolved_boundary_grids = biggest_area_df.copy()
    resolved_boundary_grids[f"assigned_{admin_id_col}"] = resolved_boundary_grids[
        admin_id_col
    ]
    resolved_boundary_grids = resolved_boundary_grids.drop(
        columns=[admin_id_col, "overlap_area"]
    )

    pop_gdf_adm_deduplicated = pop_gdf_adm.drop_duplicates(subset="id", keep=False)
    pop_gdf_adm_deduplicated = pd.concat(
        [pop_gdf_adm_deduplicated, resolved_boundary_grids], ignore_index=True
    )

    return pop_gdf_adm_deduplicated


def assign_grids_to_admin_areas(
    file_path, grids_gdf, admin_id_col="ADM2", resolve_boundaries=True
):
    """
    Assign grid cells to administrative areas based on spatial join.

    Parameters
    ----------
    grids_gdf : geopandas.GeoDataFrame
        Geodataframe containing grid cell geometries and data.
    admin_id_col : str, optional
        Column name in admin_gdf that contains the unique identifier for each administrative area.
    resolve_boundaries : bool, optional
        Whether to resolve grid cells that intersect multiple administrative areas
        by assigning them to the area with the largest overlap. Default is True.

    Returns
    -------
    geopandas.GeoDataFrame
        Geodataframe of grid cells with an additional column for the assigned administrative area identifier.
    """

    admin_gdf = load_administrative_boundaries(file_path, admin_id_col)

    print(f"Spatially joining grid cells to administrative area {admin_id_col}...")
    assigned_gdf = gpd.sjoin(
        grids_gdf,
        admin_gdf[[admin_id_col, "geometry"]],
        how="left",
        predicate="intersects",
    )

    assigned_gdf = assigned_gdf.rename(
        columns={admin_id_col: f"assigned_{admin_id_col}"}
    )
    assigned_gdf = assigned_gdf.drop(columns=["index_right"])

    if resolve_boundaries:
        assigned_gdf = assign_boundary_grids_by_area(
            assigned_gdf, admin_gdf, admin_id_col
        )

    assigned_gdf = assigned_gdf.rename(
        columns={f"assigned_{admin_id_col}": f"{admin_id_col}"}
    )

    # assigned_gdf.drop(columns=["geometry"], inplace=True)
    assigned_gdf = assigned_gdf.merge(
        grids_gdf[["id", "geometry"]], on="id", how="left", suffixes=("_remove", "")
    ).drop(columns=["geometry_remove"])

    return assigned_gdf, admin_gdf


def list_matching_tifs(folder: Path, regex_pattern: str):
    """
    Return list of tif files in folder that match the given regex pattern.

    Parameters
    ----------
    folder : Path
        Directory to check for tif files in.
    regex_pattern : str
        Regular expression pattern to match file names against.

    Returns
    -------
    list of Path
        List of tif files that match the given regex pattern.
    """
    rx = re.compile(regex_pattern)
    return sorted([p for p in folder.glob("*.tif") if rx.match(p.name)])


def sum_population_rasters(files: list, config: dict = None, demographic: str = None):
    """
    Load individual population rasters and return a DataFrame with the summed population.

    Parameters
    ----------
    files : list
        List of population tif files to load and aggregate.
    config : dict, optional
        Configuration dictionary, by default None.
    demographic : str, optional
        Demographic group name (e.g. "female", "children"), by default None

    Returns
    -------
    pd.DataFrame
        DataFrame with summed population for each grid cell based on provided list
        of tif files.
    """
    list_of_dfs = []

    for filepath in files:
        pop_df = load_population_grid(config, pop_file_path=filepath)
        list_of_dfs.append(pop_df[["id", "population"]])

    summed_pop_df = (
        pd.concat(list_of_dfs, ignore_index=True)
        .groupby("id", as_index=False)["population"]
        .sum()
    )

    if demographic is not None:
        summed_pop_df = summed_pop_df.rename(columns={"population": demographic})

    return summed_pop_df


def get_data_from_web(url, output_path, output_filename, force_overwrite=False):
    """Utility function to download data from a web URL and save it to a specified output path.

    Parameters
    ----------
    url : str
        The URL to download data from.
    output_path : str or Path
        The directory where the downloaded data will be saved.
    output_filename : str
        The name of the file to save the downloaded data as.
    force_overwrite : bool, optional
        Whether to overwrite existing files, by default False

    Returns
    -------
    Path
        The path to the downloaded file.
    """

    output_path = Path(output_path)
    output_path = output_path.joinpath(output_filename)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not force_overwrite:
        generate_output_bool = utils.continue_confirmation(output_path)
    else:
        generate_output_bool = False

    if generate_output_bool or force_overwrite:
        with requests.get(url, stream=True, timeout=120) as download_response:
            download_response.raise_for_status()
            with open(output_path, "wb") as outfile:
                for chunk in download_response.iter_content(chunk_size=8192):
                    if chunk:
                        outfile.write(chunk)
            print("Saved file to:", output_path)
    return output_path


def define_wp_release_version() -> dict:
    """
    Return a dictionary of metadata for the desired release of WorldPop data.

    Returns
    -------
    dict
        A dictionary containing metadata for the desired release of WorldPop data.
    """
    wp_release_details = {
        "wp_population_data_year": "2025",
        "wp_data_release": "R2025A",
        "wp_data_version": "v1",
    }
    return wp_release_details


def download_wp_population_data(
    output_dir,
    country_iso_code,
    force_overwrite=False,
):
    """
    Download the national level gridded population estimates from WorldPop

    Parameters
    ----------
    output_dir : str or Path
        The directory where the downloaded data will be saved.
    country_iso_code : str
        The ISO code of the country for which to download data.
    force_overwrite : bool, optional
        Whether to overwrite existing files, by default False

    Returns
    -------
    Path
        The path to the downloaded tif file.
    """

    wp_release_details = define_wp_release_version()

    wp_population_data_year = wp_release_details["wp_population_data_year"]
    wp_data_release = wp_release_details["wp_data_release"]
    wp_data_version = wp_release_details["wp_data_version"]

    output_path = output_dir.joinpath("population_data")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_location = get_data_from_web(
        f"https://data.worldpop.org/GIS/Population/Global_2015_2030/{wp_data_release}/{wp_population_data_year}/{country_iso_code.upper()}/{wp_data_version}/1km_ua/constrained/{country_iso_code.lower()}_pop_{wp_population_data_year}_CN_1km_{wp_data_release}_UA_{wp_data_version}.tif",
        output_path=output_path,
        output_filename=f"{country_iso_code.lower()}_pop_{wp_population_data_year}_CN_1km_{wp_data_release}_UA_{wp_data_version}.tif",
        force_overwrite=force_overwrite,
    )
    return file_location


def download_geoboundaries_data(
    output_dir: Path or str,
    country_iso_code: str,
    adm_level: str,
    output_path: Path | None = None,
    force_overwrite: bool = False,
) -> Path:
    """
    Query a GeoBoundaries endpoint and download the referenced GeoJSON file.

    Parameters
    ----------
    output_dir : Path or str
        The directory where the downloaded data will be saved.
    country_iso_code : str
        The ISO code of the country for which to download data.
    adm_level : str
        The administrative level to download (e.g., "ADM1", "ADM2").
    output_path : Path, optional
        The path to save the downloaded GeoJSON file, by default None
    force_overwrite : bool, optional
        Whether to overwrite existing files, by default False

    Returns
    -------
    Path
        The path to the downloaded GeoJSON file.
    """
    api_url = f"https://www.geoboundaries.org/api/current/gbOpen/{country_iso_code}/{adm_level}/"
    response = requests.get(api_url, timeout=60)
    response.raise_for_status()
    metadata = response.json()

    geojson_url = metadata.get("gjDownloadURL") or metadata.get("staticDownloadLink")
    if not geojson_url:
        raise ValueError("GeoJSON URL not found in API response metadata.")

    if output_path is None:
        output_path = (
            output_dir
            / "admin_boundary_geom"
            / f"{country_iso_code}_{adm_level}_geoboundaries.geojson"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not force_overwrite:
        generate_output_bool = utils.continue_confirmation(output_path)
    else:
        generate_output_bool = False

    if generate_output_bool or force_overwrite:
        with requests.get(geojson_url, stream=True, timeout=120) as download_response:
            download_response.raise_for_status()
            with open(output_path, "wb") as outfile:
                for chunk in download_response.iter_content(chunk_size=8192):
                    if chunk:
                        outfile.write(chunk)
            print(f"Downloaded GeoJSON to: {output_path}")
    return output_path


def download_wp_demographic_pop_data(
    output_dir: str or Path,
    country_iso_code: str,
    force_overwrite: bool = False,
):
    """
    Download the age-sex demographic population estimates from WorldPop

    Parameters
    ----------
    output_dir : str or Path
        The directory where the downloaded data will be saved.
    country_iso_code : str
        The ISO code of the country for which to download data.
    force_overwrite : bool, optional
        Whether to overwrite existing files, by default False

    Returns
    -------
    Path
        The path to the downloaded zip-file.
    """
    wp_release_details = define_wp_release_version()

    wp_population_data_year = wp_release_details["wp_population_data_year"]
    wp_data_release = wp_release_details["wp_data_release"]
    wp_data_version = wp_release_details["wp_data_version"]

    output_path = output_dir.joinpath("population_data")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://data.worldpop.org/GIS/AgeSex_structures/Global_2015_2030/{wp_data_release}/{wp_population_data_year}/{country_iso_code.upper()}/{wp_data_version}/1km_ua/{country_iso_code.lower()}_agesex_structures_{wp_population_data_year}_CN_1km_{wp_data_release}_UA_{wp_data_version}.zip"

    file_location = get_data_from_web(
        url,
        output_path=output_path,
        output_filename=f"{country_iso_code.lower()}_agesex_structures_{wp_population_data_year}_CN_1km_{wp_data_release}_{wp_data_version}.zip",
        force_overwrite=force_overwrite,
    )
    return file_location


def download_and_extract_demographic_pop_data(
    output_dir,
    country_iso_code,
    force_overwrite=False,
):
    """
    Download and extract the age-sex demographic population estimates from WorldPop

    Parameters
    ----------
    output_dir : str or Path
        The directory where the downloaded data will be saved.
    country_iso_code : str
        The ISO code of the country for which to download data.
    force_overwrite : bool, optional
        Whether to overwrite existing files, by default False

    Returns
    -------
    Path
        The path to the extracted files from the zip-file.
    """
    zip_path = download_wp_demographic_pop_data(
        output_dir,
        country_iso_code,
        force_overwrite=force_overwrite,
    )

    demo_data_path = zip_path.with_suffix("")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(demo_data_path)
    return demo_data_path


def process_demographic_pop_data(
    raw_data_dir, processed_data_path, country_iso_code, force_overwrite=False
):
    """
    Process age-sex population data into a single dataframe.

    Parameters
    ----------
    raw_data_dir : str or Path
        The directory where the raw data is stored.
    processed_data_path : str or Path
        The directory where the processed data will be saved.
    country_iso_code : str
        The ISO code of the country for which to process data.
    force_overwrite : bool, optional
        _description_, by default False

    Returns
    -------
    pd.DataFrame
        A dataframe containing the processed demographic population data.
    """

    pop_demo_path = processed_data_path.joinpath(
        f"{country_iso_code.lower()}_demographic_population_data.csv"
    )

    pop_demo_path.parent.mkdir(parents=True, exist_ok=True)

    if not force_overwrite:
        generate_output_bool = utils.continue_confirmation(pop_demo_path)
    else:
        generate_output_bool = False

    if generate_output_bool or force_overwrite:

        demo_data_path = download_and_extract_demographic_pop_data(
            raw_data_dir, country_iso_code, force_overwrite=force_overwrite
        )

        demographic_dict = {
            "female": rf"^{country_iso_code.lower()}_f.*\.tif$",
            "male": rf"^{country_iso_code.lower()}_m.*\.tif$",
            "children": rf"^{country_iso_code.lower()}_t_(00|01|05|10).*\.tif$",
            "working_age": rf"^{country_iso_code.lower()}_t_(15|20|25|30|35|40|45|50|55|60).*\.tif$",
            "older_people": rf"^{country_iso_code.lower()}_t_(65|70|75|80|85|90).*\.tif$",
            "reproductive_age": rf"^{country_iso_code.lower()}_f_(15|20|25|30|35|40|45).*\.tif$",
        }

        demographic_pop_df = pd.DataFrame()
        for demographic, regex_pat in demographic_dict.items():
            print(f"Processing demographic group: {demographic}")
            files = list_matching_tifs(demo_data_path, regex_pat)
            demo_df = sum_population_rasters(files, demographic=demographic)
            if demographic_pop_df.empty:
                demographic_pop_df = demo_df
            else:
                demographic_pop_df = demographic_pop_df.merge(
                    demo_df, on="id", how="outer"
                )

        demographic_pop_df.to_csv(
            pop_demo_path,
            index=False,
        )

        return demographic_pop_df
    else:
        demographic_pop_df = pd.read_csv(pop_demo_path)
        demographic_pop_df.id = demographic_pop_df.id.astype(str)
        return demographic_pop_df


def combine_agesex_national_pop_data(
    raw_data_dir, processed_data_dir, pop_gdf, demographic_pop_df, country_iso_code
):
    """
    Combine age-sex population data with the national population dataset and save to geopackage.

    Parameters
    ----------
    raw_data_dir : str or Path
        The directory where the raw data is stored.
    processed_data_dir : str or Path
        The directory where the processed data will be saved.
    pop_gdf : gpd.GeoDataFrame
        The national population geodataframe.
    demographic_pop_df : pd.DataFrame
        The dataframe containing the processed demographic population data.
    country_iso_code : str
        The ISO code of the country for which to process data.

    Returns
    -------
    gpd.GeoDataFrame
        A geodataframe containing the combined age-sex population data with the national population dataset.
    """
    print(
        "Combining the age-sex population data with the national population grid geodataframe..."
    )

    wp_release_details = define_wp_release_version()

    wp_population_data_year = wp_release_details["wp_population_data_year"]
    wp_data_release = wp_release_details["wp_data_release"]
    wp_data_version = wp_release_details["wp_data_version"]

    demo_files_path = raw_data_dir.joinpath("population_data").joinpath(
        f"{country_iso_code.lower()}_agesex_structures_{wp_population_data_year}_CN_1km_{wp_data_release}_{wp_data_version}"
    )

    files = demo_files_path.glob("*.tif")

    dpop = load_population_grid(None, pop_file_path=[*files][0])

    pop_master_gdf = gpd.sjoin(
        dpop[["id", "geometry"]],
        pop_gdf,
        predicate="covers",
        how="right",
        lsuffix="demo",
        rsuffix="national",
    )

    pop_master_gdf = pop_master_gdf.merge(
        demographic_pop_df, left_on="id_demo", right_on="id"
    )

    pop_master_gdf = pop_master_gdf.drop(columns=["id", "index_demo"])

    pop_master_gdf = pop_master_gdf.rename(columns={"id_national": "id"})

    population_output_data_path = processed_data_dir.joinpath(
        "master_population_grid_data.gpkg"
    )

    pop_master_gdf.to_file(
        population_output_data_path,
        driver="GPKG",
    )

    return pop_master_gdf


def process_healthsites_hcf_data(health_fac_gdf):
    """Process healthsites.io data to extract relevant columns and clean the data."""
    health_fac_gdf = health_fac_gdf.rename(
        columns={
            "osm_id": "id",
            "name": "facility_name",
            "amenity": "facility_type",
            "operator": "facility_ownership",
        }
    )

    health_fac_gdf.drop_duplicates(subset="id", inplace=True)

    return health_fac_gdf


def save_hcf_data(processed_data_dir, health_fac_gdf):
    """Save the processed healthcare facility geodataframe to a GeoPackage."""
    hcf_output_data_path = processed_data_dir.joinpath("healthcare_facility_data.gpkg")

    health_fac_gdf.to_file(
        hcf_output_data_path,
        driver="GPKG",
    )
