import folium
import rioxarray
import numpy as np
import osmnx as ox
import pandas as pd
import seaborn as sns
import geopandas as gpd
from geopy.distance import geodesic
from geocube.vector import vectorize
from rapidfuzz import process, fuzz
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix
import matplotlib.patches as mpatches
from shapely.geometry import Point
from folium.features import GeoJson, GeoJsonTooltip
from shapely import wkt
import healthcare_accessibility.geospatial_utils as geo_util
import r5py
import datetime
import time


def convert_to_georeferenced(df, lat_col, lon_col, project_crs):
    """
    Converts a pandas DataFrame with latitude and longitude columns and return a GeoDataFrame

    Parameters:
    - input_data: str, path to the CSV file / dataframe of the data
    - lat_col: str, name of the latitude column
    - lon_col: str, name of the longitude column
    - file_

    Returns:
    - GeoDataFrame with point geometries
    """

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs="EPSG:4326",
    )
    return gdf


def set_crs(pop_grid_gdf, crs):
    """Reproject geometry to desired CRS."""
    return pop_grid_gdf.to_crs(crs)


def load_georeferenced_csv_or_xlsx(
    file_path, lat_col, lon_col, desired_crs, sheet_name=None
):
    """
    Load a CSV file with latitude and longitude columns and return a GeoDataFrame.

    - file_path: str, path to the CSV or XLSX file
    - lat_col: str, name of the latitude column
    - lon_col: str, name of the longitude column
    - sheet_name: str, sheet name if using an XLSX file, Default is None.
    - desired_crs: str, desired coordinate reference system, Default is "EPSG:4326"

    Returns:
    - GeoDataFrame with point geometries
    """

    if "csv" in file_path:
        df = pd.read_csv(file_path)

    elif "xlsx" in file_path:
        if sheet_name == None:
            raise ValueError("A valid sheet name is required for loading Excel file")
        df = pd.read_excel(file_path, sheet_name=sheet_name)

    else:
        raise ValueError("File must be a CSV or XLSX")

    # Apply cleaning to relevant columns in case of white space
    df[lon_col] = df[lon_col].astype(str).str.replace(" ", "")
    df[lat_col] = df[lat_col].astype(str).str.replace(" ", "")

    gdf = convert_to_georeferenced(df, lat_col, lon_col, desired_crs)
    gdf = set_crs(gdf, desired_crs)
    return gdf


def load_csv_or_xlsx_not_georeferenced(file_path, sheet_name=None, crs="EPSG:4326"):
    """
    Loads a CSV or Excel file containing non-georeferenced data and converts it into a GeoDataFrame
    with placeholder geometry.

    This function reads tabular data from a CSV or XLSX file, adds a default geometry column
    using Point(0, 0) for each row, and converts the DataFrame into a GeoDataFrame with the specified
    coordinate reference system (CRS).

    Parameters:
    file_path (str): Path to the CSV or XLSX file.
    sheet_name (str): Name of the sheet to read (used only if the file is XLSX).
    crs (str): Coordinate Reference System to assign to the GeoDataFrame (default is 'EPSG:4326').

    Returns:
    geopandas.GeoDataFrame: A GeoDataFrame with placeholder geometry and the specified CRS.
    """

    if "csv" in file_path:
        df = pd.read_csv(file_path)

    elif "xlsx" in file_path:
        if sheet_name == None:
            raise ValueError("A valid sheet name is required for loading Excel file")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    else:
        raise ValueError("File must be a CSV or XLSX")

    # Add placeholder geometry (e.g., Point(0, 0)) as missing
    # df["geometry"] = [Point() for _ in range(len(df))]

    if "geometry" in df.columns:
        # Convert to GeoDataFrame

        df["geometry"] = df["geometry"].apply(wkt.loads)

        gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

        # Set CRS
        gdf.to_crs(crs, inplace=True)

        return gdf
    else:
        # return pandas dataframe
        return df


def load_and_vectorize_grid_tif(grid_tif_path):
    """
    Load a population grid from a raster file and vectorize it.

    Parameters:
    - grid_tif_path: str, path to the grid raster file

    Returns:
    - GeoDataFrame with population data
    """
    data = rioxarray.open_rasterio(grid_tif_path).squeeze()
    data.name = "population"
    return vectorize(data)


def return_grid_centroids(grid_gdf):
    """
    Return the centroids of a GeoDataFrame containing grid geometries.

    Parameters:
    - grid_gdf: GeoDataFrame with grid geometries

    Returns:
    - GeoSeries of centroids
    """
    centroids = grid_gdf.centroid
    grid_gdf["geometry"] = centroids
    return grid_gdf


def filter_by_bounds_of_dataset(gdf, bounding_gdf, crs="EPSG:4326"):
    """
    Filter a GeoDataFrame by the bounds of another GeoDataFrame.

    Parameters:
    - gdf: GeoDataFrame to filter
    - bounding_gdf: GeoDataFrame with bounds to filter by
    - crs: Coordinate Reference System to use for filtering

    Returns:
    - Filtered GeoDataFrame
    """
    bounding_gdf = bounding_gdf.to_crs(crs)
    xmin, ymin, xmax, ymax = bounding_gdf.total_bounds
    return gdf.cx[xmin:xmax, ymin:ymax]


def straight_path_distance(lat_orig, long_orig, lat_dest, long_dest):
    """
    This uses the geodesic distance to give a straight path distance between two locations
    on earth. It gives shortest arc length and accounts for the earth's shape.

    Parameters:
    - lat_orig (float): the latitude of the orgin's location.
    - long_orig (float): the longitude of the orgin's location.
    - lat_dest (float): the latitude of the destination's location.
    - long_dest (float): the longitude of the destination's location.

    Returns:
    - The distance in meters, kilometers or miles.
    """
    origin = (lat_orig, long_orig)
    dest = (lat_dest, long_dest)

    return geodesic(origin, dest).kilometers

    # if unit == 'meters':
    #     return geodesic(origin, dest).meters

    # elif unit == 'km':
    #     return geodesic(origin, dest).kilometers

    # else:
    #     return geodesic(origin, dest).miles


""" Map functions """


def get_admin_colors(data, adm_col, adm_level):
    """
    This maps each region to a color

    Parameters:
    - data (GeoDataFrame): adm boundary data
    - adm_col (str): the column that holds the names in the adm levels
    - adm_level (str): tells which admin level to get colours for

    Returns:
    - A dictionary of each adm level to its respective color
    """

    # Assign a color to each amd level
    if adm_level == "1":
        colours = ["red", "blue", "yellow"]

    elif adm_level == "2":
        colours = [
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

    # colour mapping
    adm_names = list(data[adm_col].unique())

    colours_map = {r: colours[i] for i, r in enumerate(adm_names)}

    return colours_map


def get_region_layer(region_data, region_colours):
    """
    This creates the region layer to be added to the Folium map.

    Parameters:
        region_colours (dict): a map of each region to a colour in hex form

    Returns:
        region_layer (GeoJson): The region layer to be added to the map
    """

    regions_layer = GeoJson(
        region_data.to_json(),
        name="Regions (ADM1)",
        style_function=lambda feat: {
            "fillColor": region_colours.get(feat["properties"]["Region"], "#999999"),
            "fillOpacity": 0.9,
            "weight": 2,
        },
        highlight_function=lambda feat: {"weight": 3, "color": "#08519c"},
        tooltip=GeoJsonTooltip(fields=["Region"], aliases=["Region:"], sticky=True),
    )

    return regions_layer


def get_district_layer(district_data, district_colours):
    """
    This creates the district layer to be added to the Folium map.

    Parameters:


    Returns:
        districts_layer (GeoJson): The district layer to be added to the map
    """
    districts_layer = GeoJson(
        district_data.to_json(),
        name="Districts (ADM2)",
        style_function=lambda feat: {
            "fillColor": district_colours.get(
                feat["properties"]["District"], "#999999"
            ),
            "fillOpacity": 0.9,
            "weight": 2,
            "color": "#1f78b4",
        },
        highlight_function=lambda feat: {
            "weight": 2,
            "color": "#000000",
            "fillOpacity": 0.3,
        },
        tooltip=GeoJsonTooltip(fields=["District"], aliases=["District:"], sticky=True),
    )

    return districts_layer


def plot_map(data, region_data, district_data, lat, long, tip, vis_crs):
    """
    This plots the map that shows all regions, districts and facilities.

    Parameters:
        data (GeoDataFrame): Data of all important information about each facility
        region_data (GeoDataFrame): Data of region boundaries
        district_data (GeoDataFrame): Data of district boundaries
        lat (str): The name of column contaning latitude values
        long (str): The name of column containing longitude values
        tip (str): The information to be shown when a facility is selected

    Returns:
        m (Folium.Map): Foilum map object with markers plotted at specified location
    """

    m = folium.Map(
        location=[data[lat].mean(), data[long].mean()],
        tiles="OpenStreetMap",
        zoom_start=3,
    )

    # regions outline
    region_colours = get_admin_colors(region_data, "Region", "1")
    regions_layer = get_region_layer(region_data, region_colours)
    regions_layer.add_to(m)

    # district outline
    district_colours = get_admin_colors(district_data, "District", "2")
    districts_layer = get_district_layer(district_data, district_colours)
    districts_layer.add_to(m)

    for _, row in data.iterrows():
        folium.CircleMarker(
            location=[row[lat], row[long]],
            tooltip=row[tip],
            radius=3,
            weight=2,
            fill=True,
            fill_opacity=0.6,
            opacity=1,
        ).add_to(m)

    # to better control map layers
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def get_maps(region_data, district_data, reg_col, dis_col, bound_col):
    """
    This maps each administrative unit to its respective boundary points.

    Parameters:
        region_data (GeoDataFrame): Data of region boundaries
        district_data (GeoDataFrame): Data of district boundaries
        reg_col (str): column name holding the region names
        dis_col (str): column name holding the district names
        bound_col (str): column name holding the boundaries

    Returns:
        region_map (dict) : Map of all 3 regions to their geometric boundaries
        district_map (dict) : Map of all 28 districts to their geometric boundaries
    """

    # regions
    region_map = {}
    regions = region_data[reg_col].tolist()

    for r in regions:
        idx = region_data.index[region_data[reg_col] == r][0]
        reg = r.split(" ")[0]
        region_map[reg] = region_data.iloc[idx][bound_col]

    # districts
    district_map = {}
    districts = district_data[dis_col].tolist()

    for r in districts:
        idx = district_data.index[district_data[dis_col] == r][0]
        district_map[r] = district_data.iloc[idx][bound_col]

    return region_map, district_map


def get_region(x, region_map):
    """
    This gives the region a facility falls under.

    Parameters:
        x (Geomerty Points) : Geometry coordinates of the facilities in Point form.
        region_map (dict) : Map of all 3 regions to their geometric boundaries

    Returns:
        reg (str) : the proposed region.
    """
    for reg, reg_poly in region_map.items():
        if reg_poly.contains(x):
            return reg
    return None


def get_district(x, district_map):
    """
    This gives the district a facility falls under.

    Parameters:
        x (Geomerty Points) : Geometry coordinates of the facilities in Point form
        district_map (dict) : Map of all 28 districts to their geometric boundaries

    Returns:
        reg (str) : the proposed district.
    """
    for dis, dis_poly in district_map.items():
        if dis_poly.contains(x):
            return dis
    return None


""" Data Cleaning"""


def clean_datasets(dataset_dir, dataset_name):
    """
    This cleans all the datasets.

    Parameters:
        dataset_dir (str): directory to the data sets

    Returns:
        df (DataFrame) : cleaned data
    """

    if dataset_name == "baobab":
        df = pd.read_csv(dataset_dir)

        df.drop(
            [
                "Unnamed: 11",
                "Unnamed: 12",
                "Unnamed: 13",
                "Unnamed: 14",
                "Unnamed: 15",
                "Unnamed: 16",
                "Unnamed: 17",
                "Catchment Population (2018)",
                "District Code",
            ],
            axis=1,
            inplace=True,
        )

        df["District"] = df["District"].str.strip()
        df.rename(
            columns={
                "Facility Name": "Facility name",
                "Facility Type": "Facility type",
                "Facility Ownership": "Facility ownership",
            },
            inplace=True,
        )

    if dataset_name == "figshare":
        fig_df = pd.read_excel(dataset_dir, engine="openpyxl")
        # selecting malawi's data
        df = fig_df[fig_df["Country"] == "Malawi"].reset_index(drop=True)
        df.rename(columns={"Admin1": "Region"}, inplace=True)
        df.drop(["Country", "LL source"], axis=1, inplace=True)
        df.rename(
            columns={
                "Lat": "latitude",
                "Long": "longitude",
                "Ownership": "Facility ownership",
            },
            inplace=True,
        )

    if dataset_name == "eliz":

        df = pd.read_excel(dataset_dir, engine="openpyxl")
        df.drop(["ZONE"], axis=1, inplace=True)

        df["REGION"] = df["REGION"].apply(filter_name)
        df["DISTRICT"] = df["DISTRICT"].apply(filter_name)

        df.rename(
            columns={
                "SITE NAME": "Facility name",
                "LATITUDE": "latitude",
                "LONGITUDE": "longitude",
                "DISTRICT": "District",
                "REGION": "Region",
            },
            inplace=True,
        )

    return df


def filter_name(x):
    """
    This cleans the region and district column of Elizabeth aids datasets.

    Parameters:
        x (str) : Region / District name

    Returns:
        (str) : the cleaned name
    """
    if not pd.isna(x):
        new = x.split(" ")
        if len(new) > 2:
            return (" ").join(new[:2])
        return new[0]
    return x


def compare_facility_types(gdf, facility_name, analysis_crs):
    """
    Analyze and visualize changes in facility types and geometries for a specific facility name.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        A GeoDataFrame containing facility data with columns including 'Facility Name', 'Facility Type',
        and 'geometry'. The geometry column should contain point geometries.

    facility_name : str
        The name of the facility to filter and analyze.

    Returns
    -------
    gdf : geopandas.GeoDataFrame
        A filtered and processed GeoDataFrame for the selected facility, including calculated distances
        between consecutive facility locations and cleaned geometry duplicates.

    map : folium.Map
        An interactive Folium map visualizing the facility locations, colored by 'Facility Name',
        with tooltips showing the distance between facilities.

    analysis_crs:
        CRS needed for analysis

    Notes
    -----
    - The function groups the input GeoDataFrame by 'Facility Name' and selects the group matching
      the provided facility_name.
    - It converts the CRS to a predefined analysis CRS (assumed to be defined globally).
    - Geometry normalization is applied to improve duplicate detection.
    - Facility type and geometry changes are tracked using boolean columns.
    - Duplicate geometries are dropped based on change detection logic.
    - Euclidean distances between consecutive facility points are calculated.
    - An interactive map is generated using geopandas.explore with customized styling.
    """
    # Standardize facility name to lowercase for matching
    facility_name = str.lower(facility_name)
    gdf["Facility Name"] = gdf["Facility Name"].str.lower()

    # Create dictionary
    gdf_dict = {
        Facility_Name: group for Facility_Name, group in gdf.groupby("Facility Name")
    }

    # Select Facility
    gdf = gdf_dict[facility_name]

    # Convert the GeoDataFrame CRS for analysis
    gdf = gdf.to_crs(analysis_crs)

    # Normalize geometries to ensure duplicates correctly identified
    gdf["geometry"] = gdf.geometry.normalize()

    # Create a boolean column indicating if the current row's value is different
    gdf["Facility Type Change"] = gdf["Facility Type"] != gdf["Facility Type"].shift(1)
    gdf["Geometry Change"] = gdf["geometry"] != gdf["geometry"].shift(1)

    if len(gdf) > 2:
        # Loop using the boolean columns, only need if gdf length > 2
        for geom_change, facility_type_change in zip(
            gdf["Geometry Change"], gdf["Facility Type Change"]
        ):
            if geom_change and not facility_type_change:

                # Drop rows where geometry duplicated, keeps last occurrence
                gdf = gdf.drop_duplicates(subset=["geometry"], keep="last").reset_index(
                    drop=True
                )

            else:
                # Drop rows where geometry duplicated, keeps first occurrence
                gdf = gdf.drop_duplicates(
                    subset=["geometry"], keep="first"
                ).reset_index(drop=True)

    # The .distance() method calculates Euclidean distance between corresponding points.
    gdf["distance_between_facilities(m)"] = (
        gdf["geometry"].distance(gdf["geometry"].shift()).round(2)
    )

    # Drop unneeded columns
    gdf.drop(
        columns=["Country", "Facility Type Change", "Geometry Change"],
        axis=1,
        inplace=True,
    )

    # Create and display an interactive map
    map = gdf.explore(
        column="Facility Name",
        tooltip=["distance_between_facilities(m)"],
        popup=True,
        cmap="inferno",
        marker_kwds={"radius": 10},  # Increase the radius to make points bigger
    )

    map

    return gdf, map


def create_distance_matrix(gdf, facility_name, analysis_crs):
    """
    Generates and visualizes a distance matrix for healthcare facilities with the same name.

    Parameters:
    ----------
    gdf : geopandas.GeoDataFrame
        A GeoDataFrame containing healthcare facility data, including geometry and attributes
        such as 'Facility Name', 'Ownership', and 'Facility Ownership'.

    facility_name : str
        The name of the facility to filter and analyze. Only facilities with this name will be included.

    analysis_crs : str
        The coordinate reference system (CRS) to which the geometries should be converted for accurate distance calculations.

    Returns:
    -------
    pandas.DataFrame
        A labeled distance matrix (in meters) between facilities with the specified name.

    Side Effects:
    ------------
    - Displays a heatmap of the distance matrix using seaborn.

    Notes:
    ------
    - The function normalizes geometries to ensure duplicates are correctly identified.
    - Labels in the matrix include ownership information and row indices for traceability.
    - Uses Euclidean distance based on projected coordinates

    """
    # Standardize facility name to lowercase for matching
    facility_name = str.lower(facility_name)
    gdf["Facility Name"] = gdf["Facility Name"].str.lower()

    # Convert the GeoDataFrame CRS for analysis
    gdf = gdf.to_crs(analysis_crs).reset_index(drop=True)

    # Create dictionary
    gdf_dict = {
        Facility_Name: group for Facility_Name, group in gdf.groupby("Facility Name")
    }

    # Select Facility
    gdf = gdf_dict[facility_name]

    # Normalize geometries to ensure duplicates correctly identified
    gdf["geometry"] = gdf.geometry.normalize()

    # Remove rows with missing geometry
    gdf = gdf[gdf.geometry.x.notnull()]

    # Create custom labels using Ownership and Facility Ownership
    labels = (
        gdf["Ownership"]
        + " and/or "
        + gdf["Facility Ownership"]
        + "-"
        + "Row Index: ("
        + gdf.index.astype(str)
        + ")"
    )

    # Extract coordinates
    coords = gdf.geometry.apply(lambda geom: (geom.x, geom.y)).tolist()

    # Compute the actual distance matrix
    matrix_values = distance_matrix(coords, coords)  # coords is a list of (x, y) tuples

    # Create a labeled DataFrame using the result
    matrix_df = pd.DataFrame(matrix_values, index=labels, columns=labels)

    # Plot heatmap
    plt.figure(figsize=(20, 10))
    sns.heatmap(matrix_df, annot=True, fmt=".1f", cmap="YlOrRd")
    plt.title(
        f"Distance(m) between Healthcare Facilities with same name - {facility_name}"
    )
    plt.tight_layout()
    plt.show()

    return gdf


# %%
def column_str_clean(gdf):
    """
    Cleans and standardizes string values in a GeoDataFrame.

    This function performs the following operations:
    1. Replaces specific characters ('_', ',', '*') in all columns except 'Name' and 'geometry'.
       - '_' is replaced with a space.
       - '*' is replaced with 'Unclassified'.
       - ',' is preserved.
    2. Fills null values with the string 'Not Known'.
    3. Replaces specific unwanted strings with 'Not Known':
       - 'Alexandrepsantos'
       - 'Unclassified'
    4. Standardizes surface types by replacing known variants of unpaved surfaces with 'Unpaved'.
    5. Cleans the 'Surface' column further by:
       - Replacing values shorter than 3 characters with 'Not Known'.
       - Replacing 3-character values (except 'Mud') with 'Not Known'.
       - Replacing 4-character values (except 'Wood' and 'Dirt') with 'Not Known'.

    Parameters:
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to be cleaned.

    Returns:
    -------
    geopandas.GeoDataFrame
        The cleaned GeoDataFrame.
    """

    # Replace certain words
    gdf = gdf.map(
        lambda x: (
            x.replace("Alexandrepsantos", "Not Known").replace(
                "Unclassified", "Not Known"
            )
            if isinstance(x, str)
            else x
        )
    )

    # Clean values in all columns - not name or geometry
    for col in gdf:
        if col != "Name" and col != "geometry":
            gdf[col] = gdf[col].replace(
                {"_": " ", ",": ",", r"\*": "Not Known"}, regex=True
            )

    # Replace null values with a string
    gdf = gdf.fillna("Not Known")

    # Replace these words with unpaved
    unpaved_words = [
        "Unp",
        "Unoaved",
        "Ongeplaveide",
        "Unpaved Path Leading To Some Houses",
        "Unpaved, Natural",
    ]

    gdf["Surface"] = gdf["Surface"].replace(unpaved_words, "Unpaved")

    for surface in gdf["Surface"]:
        if len(surface) < 3:
            gdf["Surface"] = gdf["Surface"].replace(surface, "Not Known")

        elif len(surface) == 3 and surface != "Mud":
            gdf["Surface"] = gdf["Surface"].replace(surface, "Not Known")

        elif len(surface) == 4 and surface != "Wood" and "Dirt":
            gdf["Surface"] = gdf["Surface"].replace(surface, "Not Known")

    return gdf


def clean_width_column(gdf):
    """
    Cleans and standardizes the 'Width' column in a GeoDataFrame.

    This function performs two main transformations on the 'Width' column:
    1. Prefixes values like '.8' with a '0' to become '0.8' for consistency.
    2. Appends '.0' to numeric strings with length ≤ 2 that do not contain a decimal point,
       converting values like '1' to '1.0'.

    Parameters:
    ----------
    gdf : geopandas.GeoDataFrame
        A GeoDataFrame containing a 'Width' column with string or numeric values.

    Returns:
    -------
    geopandas.GeoDataFrame
        The modified GeoDataFrame with a cleaned and standardized 'Width' column.
    """

    # Adds 0 to .8 etc for consistency
    gdf["Width"] = gdf["Width"].apply(
        lambda num: (
            f"0{num}"
            if isinstance(num, str) and len(num) == 2 and num.startswith(".")
            else num
        )
    )

    # Adds 0 end of number for consistency
    gdf["Width"] = gdf["Width"].apply(
        lambda num: (
            f"{num}.0"
            if isinstance(num, str) and len(num) <= 2 and "." not in num
            else num
        )
    )

    return gdf


def clean_gdf_boundaries(file_path, column_name_to_change):
    """
    Cleans and standardizes a GeoDataFrame containing administrative boundary data.

    This function reads a GeoDataFrame from a file, identifies the appropriate
    administrative level (ADM0 to ADM3), renames the relevant name column to a
    user-specified name, and drops all other non-essential columns except for
    geometry. This is for data from DIVA GIS, Geoboundaries and GADM.

    Parameters
    ----------
    file_name : str
        The name of the file containing the GeoDataFrame to be cleaned.
    column_name_to_change : str
        The new name to assign to the column representing the administrative boundary name.

    Returns
    -------
    cleaned_gdf : geopandas.GeoDataFrame
        A cleaned GeoDataFrame with only the renamed name column and geometry retained.

    Notes
    -----
    - The function handles multiple administrative levels based on the presence of specific columns.
    - If none of the expected ADM columns are found, it assumes the file is from OSM and drops known irrelevant columns.
    - The function assumes `data_dir` is a globally defined path object.
    """

    # Load gdf
    gdf = gpd.read_file(file_path)

    # Make empty list
    columns_to_drop = []

    # For ADM1 - DIVA GIS or GADM
    if (
        len(gdf.columns) != 6
        and "NAME_1"
        and "ID_1" in gdf
        or len(gdf.columns) != 6
        and "NAME_1"
        and "GID_1" in gdf
    ):

        # Add irrelevant columns to list
        for column in gdf:
            if column != "NAME_1" and column != "geometry":
                columns_to_drop.append(column)

        # Rename column
        gdf.rename(columns={"NAME_1": column_name_to_change}, inplace=True)

        # Drop irrelevant columns
        gdf.drop(columns=columns_to_drop, inplace=True)

    # For boundary ADM2 - DIVA GIS
    elif "NAME_2" and "TYPE_2" in gdf:

        # Add irrelevant columns to list
        for column in gdf:
            if column != "NAME_2" and column != "geometry":
                columns_to_drop.append(column)

        # Rename column
        gdf.rename(columns={"NAME_2": column_name_to_change}, inplace=True)

        # Drop irrelevant columns
        gdf.drop(columns=columns_to_drop, inplace=True)

    # For boundary ADM2 - GADM
    elif "NAME_1" and "GID_2" in gdf:

        # Add irrelevant columns to list
        for column in gdf:
            if column != "NAME_1" and column != "geometry":
                columns_to_drop.append(column)

        # Rename column
        gdf.rename(columns={"NAME_2": column_name_to_change}, inplace=True)

        # Drop irrelevant columns
        gdf.drop(columns=columns_to_drop, inplace=True)

    # For boundary ADM3 - DIVA GIS
    elif "NAME_2" and "TYPE_2" and "TYPE_3" in gdf:

        # Add irrelevant columns to list
        for column in gdf:
            if column != "NAME_2" and column != "geometry":
                columns_to_drop.append(column)

        # Rename column
        gdf.rename(columns={"NAME_2": column_name_to_change}, inplace=True)

        # Drop irrelevant columns
        gdf.drop(columns=columns_to_drop, inplace=True)

    # For boundary ADM3 - GADM
    elif "NAME_1" and "GID_3" in gdf:

        # Add irrelevant columns to list
        for column in gdf:
            if column != "NAME_2" and column != "geometry":
                columns_to_drop.append(column)

        # Rename column
        gdf.rename(columns={"NAME_2": column_name_to_change}, inplace=True)

        # Drop irrelevant columns
        gdf.drop(columns=columns_to_drop, inplace=True)

    # For Country wide boundary ADM0 - DIVA GIS
    elif "NAME_0" in gdf:

        # Add irrelevant columns to list
        for column in gdf:
            if column != "NAME_0" and column != "geometry":
                columns_to_drop.append(column)

        # Rename column
        gdf.rename(columns={"NAME_0": column_name_to_change}, inplace=True)

        # Drop irrelevant columns
        gdf.drop(columns=columns_to_drop, inplace=True)

    # For Country wide boundary ADM0 - GADM
    elif "GID_0" and "COUNTRY" in gdf:

        # Rename column
        gdf.rename(columns={"COUNTRY": column_name_to_change}, inplace=True)

        # Drop irrelevant columns
        gdf.drop(columns="GID_0", inplace=True)

    # For OSM
    elif "shapeName" and "shapeISO" in gdf:
        # Rename column
        gdf.rename(columns={"shapeName": column_name_to_change}, inplace=True)

        # Drop irrelevant columns if geoBoundaries gdf
        gdf.drop(
            columns=["shapeISO", "shapeID", "shapeGroup", "shapeType"], inplace=True
        )

    else:
        print(
            "May need to update function to work with your geopandas dataframe. Check column names"
        )

    # Remove 'Region'
    if column_name_to_change == "Region":
        gdf["Region"] = gdf["Region"].str.replace(" Region", "", case=False)

    # Final cleaned gdf
    cleaned_gdf = gdf

    return cleaned_gdf


def general_df_or_gdf_clean(data, df_or_gdf):
    """
    Cleans and standardizes a Pandas DataFrame or GeoPandas GeoDataFrame.

    This function performs the following operations:
    - Capitalizes column headers:
        - For GeoDataFrames, all column names except the geometry column are title-cased.
        - For regular DataFrames, all column names are title-cased.
    - For columns with object (string) data type and not the geometry column:
        - Strips leading and trailing whitespace from each cell.
        - Capitalizes each word in each cell.
        - If the column is named 'REGION' (case-insensitive), replaces exact matches:
            - 'Center' → 'Central'
            - 'North' → 'Northern'
            - 'South' → 'Southern'

    Parameters:
    data (DataFrame or GeoDataFrame): The input data to clean.
    df_or_gdf (str): A string indicating the type of input. Use "df" for DataFrame and "gdf" for GeoDataFrame.

    Returns:
    DataFrame or GeoDataFrame: The cleaned data.
    """

    geometry_col = None

    if df_or_gdf == "gdf":
        # Preserve geometry column name
        geometry_col = data.geometry.name

        # Title-case all other column names except geometry

        excluded_columns = ["Facility ID", "Unique ID", geometry_col]

        data.rename(
            columns={
                col: col.title() for col in data.columns if col not in excluded_columns
            },
            inplace=True,
        )

    elif df_or_gdf == "df":
        data.columns = data.columns.str.title()

    for col in data:

        # Skip geometry column if present
        if (
            data[col].dtype == object
            and col != geometry_col
            and col.upper() != "REG NO."
        ):

            # Remove leading whitespace from column
            # Capitalize first letter of each word for values
            data[col] = data[col].str.strip().str.upper()

        # Replace region names for consistency using exact match mapping
        if data[col].dtype == object and col.upper() == "REGION":
            region_map = {"Center": "Central", "North": "Northern", "South": "Southern"}
            data[col] = data[col].replace(region_map)

    return data


def gdf_facility_column_clean(gdf):
    """
    Cleans and standardizes facility-related columns in a GeoDataFrame.

    This function performs the following operations:
    - Standardizes values in the 'Facility Type' column:
        - Converts 'Health_Post' to 'Health Post'
        - Converts 'Health Center' to 'Health Centre'
    - Standardizes values in the 'Facility Location' column:
        - Converts 'R' to 'Rural'
        - Converts 'U' to 'Urban'
    - Sorts the DataFrame alphabetically by 'Facility Name' for readability.
    - Resets the index after sorting.

    Parameters:
    gdf (GeoDataFrame): A GeoPandas GeoDataFrame containing facility data.

    Returns:
    GeoDataFrame: The cleaned and sorted GeoDataFrame.
    """

    # Change these Facility Type values to a consistent format
    gdf["Facility Type"] = gdf["Facility Type"].str.replace("_", " ").str.title()

    # Change values
    gdf["Facility Type"] = gdf["Facility Type"].replace(
        {"Health Center": "Health Centre", "Yes": "Unclassified"}
    )

    # Convert back to upper case
    gdf["Facility Type"] = gdf["Facility Type"].str.upper()

    # Change Facility Location to a consistent format
    for location in gdf["Facility Location"].unique():
        if location == "R":
            gdf.loc[gdf["Facility Location"] == location, "Facility Location"] = "Rural"
        elif location == "U":
            gdf.loc[gdf["Facility Location"] == location, "Facility Location"] = "Urban"

    # Order values alphabetically by Facility Name for better readability
    gdf.sort_values(by="Facility Name", inplace=True)

    # Reset index after sorting
    gdf.reset_index(drop=True, inplace=True)

    # Replace string-based nulls with actual NaN
    gdf.replace(["null", "NaN", ""], np.nan, inplace=True)

    return gdf


def gdf_facility_name_clean(gdf):
    """
    Cleans and standardizes the 'Facility Name' column in a GeoDataFrame.

    This function performs the following transformations on the 'Facility Name' column:
    - Replaces the word 'Center' (case-insensitive) with 'CENTRE'
    - Collapses multiple consecutive spaces into a single space
    - Removes all full stops (periods)
    - Replaces occurrences of 'CLIN' with 'CLINIC'
    Add more as necessary

    Parameters:
    ----------
    gdf : pandas.DataFrame or geopandas.GeoDataFrame
        The input DataFrame containing a 'Facility Name' column to be cleaned.

    Returns:
    -------
    gdf : pandas.DataFrame or geopandas.GeoDataFrame
        The DataFrame with the cleaned 'Facility Name' column.
    """

    # Cleaning of facilty name column for consistency
    gdf["Facility Name"] = (
        gdf["Facility Name"]
        .str.replace(
            r"\bCenter\b", "CENTRE", case=False, regex=True
        )  # Replace Centre with Centre
        .str.replace("  ", " ", regex=False)  # Collapse multiple spaces
        .str.replace(".", "", regex=False)  # Remove full stops
        .str.replace("CLIN", "CLINIC", regex=False)  # Replace 'CLIN' with 'CLINIC'
        .str.replace(
            "CLINICIC", "CLINIC", regex=False
        )  # Replace 'CLINICIC' with 'CLINIC'
    )

    return gdf


def convert_to_geometry(df, latitude_col, longitude_col):
    """
    Converts latitude and longitude columns in a DataFrame to geometry points.

    Parameters:
        df (pd.DataFrame): The input DataFrame containing latitude and longitude columns.
        latitude_col (str): The name of the latitude column. Default is 'LATITUDE'.
        longitude_col (str): The name of the longitude column. Default is 'LONGITUDE'.

    Returns:
        gpd.GeoDataFrame: A GeoDataFrame with a geometry column created from latitude and longitude.
    """
    # Ensure latitude and longitude columns exist
    if latitude_col not in df.columns or longitude_col not in df.columns:
        raise ValueError(
            f"Columns '{latitude_col}' and '{longitude_col}' must exist in the DataFrame."
        )

    # Create geometry column
    geometry = gpd.points_from_xy(df[longitude_col], df[latitude_col])

    # Convert to GeoDataFrame
    geo_df = gpd.GeoDataFrame(df, geometry=geometry)

    return geo_df


def get_roads_for_district_and_neighbours(
    district_name, district_boundaries_gdf, country, network_type
):
    """
    Retrieves and visualizes the road networks for a specified district and its neighboring districts.

    Parameters
    ----------
    district_name : str
        The name of the district of interest.

    district_boundaries_gdf : geopandas.GeoDataFrame
        A GeoDataFrame containing the boundaries of all districts, including the 'District' column.

    country : str
        The country name used for geocoding district boundaries via OpenStreetMap.

    network_type : str
        The type of road network to retrieve (e.g., 'drive', 'walk', 'drive_service').

    Returns
    -------
    geopandas.GeoDataFrame
        A combined GeoDataFrame of road segments (edges) for the district of interest and its neighboring districts.

    Notes
    -----
    - Uses spatial operations to identify neighboring districts based on shared boundaries.
    - Visualizes district boundaries and road networks using matplotlib and osmnx.
    - Road networks are retrieved via OpenStreetMap geocoding and converted to GeoDataFrames.
    - The function includes multiple plots:
        - A map of the district and its neighbors.
        - A road network plot for the district of interest.
        - Individual road network plots for each neighboring district.
    - The final output is a merged GeoDataFrame of all road segments for analysis or further
    """

    # Empty list to make gdf later
    list_of_district_with_neighbours = []

    # Extract district of interest
    district_of_interest = district_boundaries_gdf[
        district_boundaries_gdf["District"] == f"{district_name}"
    ]

    # Get neighbouring districts
    neighbouring_districts = district_boundaries_gdf[
        district_boundaries_gdf.touches(district_of_interest.geometry.iloc[0])
    ]

    # Create custom legend handles
    legend_handles = [
        mpatches.Patch(color="red", label=f"{district_name}"),
        mpatches.Patch(
            color="orange", label=f"Neighboring Districts to {district_name}"
        ),
        mpatches.Patch(color="lightgray", label="Other Districts"),
    ]

    # Plot
    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot all districts
    district_boundaries_gdf.plot(ax=ax, color="lightgray", edgecolor="Black")
    # Plot neighboring districts
    neighbouring_districts.plot(ax=ax, color="orange", edgecolor="Black")
    # Plot district of interest
    district_of_interest.plot(ax=ax, color="red", edgecolor="Black")

    # Add title and legend
    plt.title(f"{district_name} and Surrounding Districts")
    ax.axis("off")
    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),
        title="District Classification",
    )

    plt.show()

    # Get district of interest boundary
    district_of_interest_boundary = ox.geocode_to_gdf(f"{district_name}, {country}")
    district_of_interest_polygon = district_of_interest_boundary["geometry"].iloc[0]

    # Road network for district of interest
    district_of_interest_roads = ox.graph_from_polygon(
        district_of_interest_polygon, network_type=network_type
    )

    # Convert to GeoDataFrame
    district_of_interest_nodes_gdf, district_of_interest_edges_gdf = ox.graph_to_gdfs(
        district_of_interest_roads
    )

    # Add to list
    list_of_district_with_neighbours.append(district_of_interest_edges_gdf)

    # Create subplots
    fig, axs = plt.subplots(figsize=(7, 7))

    # Plot road network with black background for district of interest
    axs.set_facecolor("black")
    ox.plot_graph(
        district_of_interest_roads,
        ax=axs,
        node_size=0,
        edge_color="white",
        edge_linewidth=0.3,
        show=False,
        close=False,
    )
    axs.set_title(f"{district_name} Road Network - district of interest", color="black")
    plt.tight_layout()
    plt.show()

    # Set up plot grid based on number of unique_neighbouring_districts
    unique_neighbouring_districts = neighbouring_districts["District"].unique()
    fig, axs = plt.subplots(
        nrows=1,
        ncols=len(unique_neighbouring_districts),
        figsize=(6 * len(unique_neighbouring_districts), 6),
    )

    # Ensure axs is iterable
    if len(unique_neighbouring_districts) == 1:
        axs = [axs]

    for i, district in enumerate(unique_neighbouring_districts):
        try:
            # Get district boundary
            boundary = ox.geocode_to_gdf(f"{district}, {country}")
            polygon = boundary.geometry.iloc[0]

            # Get road network
            neighbouring_district_roads = ox.graph_from_polygon(
                polygon, network_type=network_type
            )

            # Convert to GeoDataFrame
            neighbouring_district_nodes_gdf, neighbouring_district_edges_gdf = (
                ox.graph_to_gdfs(neighbouring_district_roads)
            )

            # Add to list
            list_of_district_with_neighbours.append(neighbouring_district_edges_gdf)

            # Plot
            axs[i].set_facecolor("black")
            ox.plot_graph(
                neighbouring_district_roads,
                ax=axs[i],
                node_size=0,
                edge_color="white",
                edge_linewidth=0.3,
                show=False,
                close=False,
            )
            axs[i].set_title(
                f"{district} Road Network - surrounding district", color="black"
            )
        except Exception as e:
            print(f"Failed for {district}: {e}")

    # Merge district and neighbours into GeoDataFrame
    combined_district_roads_gdf = gpd.GeoDataFrame(
        pd.concat(list_of_district_with_neighbours, ignore_index=True)
    )

    return combined_district_roads_gdf


def fix_geometry(geom):
    """
    Cleans a geometry object by replacing invalid or empty Point geometries with None.

    This function checks if the input geometry is:
    - Already empty (`geom.is_empty`)
    - A Shapely Point with NaN coordinates (i.e., `geom.x` or `geom.y` is NaN)

    If either condition is met, it returns None, which is treated as a missing geometry
    in GeoPandas. Otherwise, it returns the original geometry unchanged.

    Parameters
    ----------
    geom : shapely.geometry.base.BaseGeometry or None
        A geometry object, typically a Point, from a GeoPandas GeoSeries.

    Returns
    -------
    shapely.geometry.base.BaseGeometry or None
        The original geometry if valid, or None if the geometry is empty or invalid.
    """

    if geom is None:
        return None
    if geom.is_empty or (
        isinstance(geom, Point) and (geom.x != geom.x or geom.y != geom.y)  # NaN check
    ):
        return None
    return geom


def geometry_to_none(point_empty_geometry):
    """
    Converts 'POINT EMPTY' or None geometry values to None.

    This function is useful for cleaning geometry columns in tabular data
    (such as pandas DataFrames) where missing or invalid geometries are
    represented as the string 'POINT EMPTY' or as None. It standardizes
    these cases by returning None, which is recognized as a missing value
    by pandas and GeoPandas.

    Parameters
    ----------
    point_empty_geometry : str or None
        The geometry value to check, typically a string like 'POINT EMPTY'
        or a valid geometry string/object.

    Returns
    -------
    None or original value
        Returns None if the input is 'POINT EMPTY' or None; otherwise,
        returns the original value unchanged.
    """

    if point_empty_geometry == "POINT EMPTY":
        return None
    return point_empty_geometry


def plot_population_grid(pop_grid_gdf, column, title="Population Grid", cmap="viridis"):
    """
    Plots a population grid using a GeoDataFrame.

    Parameters:
        pop_grid_gdf (GeoDataFrame): GeoDataFrame containing the population grid data.
        column (str): The column in the GeoDataFrame to use for coloring the grid (e.g., population density).
        title (str): Title of the plot. Default is "Population Grid".
        cmap (str): Colormap to use for the plot. Default is "viridis".

    Returns:
        None
    """
    # Check if the GeoDataFrame has a geometry column
    if "geometry" not in pop_grid_gdf:
        raise ValueError("The GeoDataFrame must have a 'geometry' column.")

    # Plot the population grid
    plt.figure(figsize=(12, 10))
    pop_grid_gdf.plot(
        column="population",  # Column to color by
        cmap="viridis",  # Colormap
        legend=True,  # Show legend
        legend_kwds={"label": f"{column} values"},  # Customize legend label
        alpha=0.8,  # Transparency
    )

    # Add title and remove axis
    plt.title(title, fontsize=16)
    plt.axis("off")
    plt.show()


def plot_interactive_travel_times_map(
    map,
    travels_gdf_vis,
    destination_hcf,
    fac_type,
    transport_mode_desc,
    visualisation_crs,
):
    """
    Adds a choropleth layer and facility markers to a Folium map to visualize travel times
    to healthcare facilities of a specified type.

    Parameters
    ----------
    map : folium.Map
        The base Folium map object to which layers will be added.

    travels_gdf_vis : GeoDataFrame
        GeoDataFrame containing travel time data for each origin point, with a column
        'travel_time' and a unique 'id' for mapping.

    destination_hcf : GeoDataFrame
        GeoDataFrame of destination healthcare facilities to be marked on the map.

    fac_type : str
        The type of healthcare facility being visualized (e.g., "Hospital", "Clinic").

    Returns
    -------
    map : folium.Map
        The updated Folium map object with the travel time choropleth and facility markers added.
    """
    # Feature group for the time travel map and markers
    group = folium.FeatureGroup(name=fac_type.title()).add_to(map)

    folium.Choropleth(
        geo_data=travels_gdf_vis.to_json(),
        data=travels_gdf_vis,
        name=f"Travel times",
        columns=["id", "travel_time"],
        key_on="feature.properties.id",
        legend_name=f"Minutes to nearest {fac_type} by {transport_mode_desc}",
        fill_opacity=0.7,
        line_weight=0.2,
        fill_color="viridis",
    ).add_to(map)

    # Add facility markers
    destination_hcf = destination_hcf.to_crs(visualisation_crs)
    tooltip_fields = [
        ("facility_name", "Facility Name"),
        ("facility_type", "Facility Type"),
        ("facility_ownership", "Ownership"),
        ("status", "Status"),
    ]

    available_tooltip_fields = [
        (column, label)
        for column, label in tooltip_fields
        if column in destination_hcf.columns
    ]

    for _, row in destination_hcf.iterrows():
        # Build tooltip only from columns that exist in the GeoDataFrame.
        tooltip_lines = []
        for column, label in available_tooltip_fields:
            value = row[column]
            display_value = "Not available" if pd.isna(value) else value
            tooltip_lines.append(f"{label}: {display_value}")

        tooltip = (
            "<br>".join(tooltip_lines) if tooltip_lines else "No metadata available"
        )

        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            tooltip=tooltip,
            icon=folium.Icon(color="blue", icon="hospital", prefix="fa"),
        ).add_to(group)

    return map


def generate_folium_travel_map(
    travel_time_gdf,
    hcf_gdf,
    transport_mode,
    hcf_description,
    file_name_description,
    output_dir,
    visualisation_crs,
    add_pop_layer=False,
    pop_grid_gdf=None,
):
    """Generate and save an interactive folium map of travel times to healthcare facilities.

    Parameters
    ----------
    travel_time_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing travel time data.
    hcf_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing healthcare facility data.
    transport_mode : str
        Description of the transport mode used.
    hcf_description : str
        Description of the healthcare facility type.
    file_name_description : str
        Description to use in the output file name.
    output_dir : str or Path
        Directory to save the output map.
    visualisation_crs : CRS or str
        Coordinate reference system for visualization.
    add_pop_layer : bool, optional
        Whether to add a population layer, by default False.
    pop_grid_gdf : geopandas.GeoDataFrame, optional
        GeoDataFrame containing population grid data, required if add_pop_layer is True.

    Returns
    -------
    None
    """
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
        fac_type=hcf_description,
        transport_mode_desc=transport_mode,
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

    m.save(
        output_dir / f"{file_name_description.lower()}_{transport_mode}_travel_map.html"
    )


def return_sorted_nearest_points(
    origin_point,
    points_gdf,
    distance_km,
    analysis_crs,
    distance_col="distance",
    preview=False,
):
    """
    Returns points within a specified distance from an origin point, sorted by proximity.

    Parameters
    ----------
    origin_point : GeoDataFrame
        A GeoDataFrame containing the origin point(s) to measure distances from.
    points_gdf : GeoDataFrame
        A GeoDataFrame containing the candidate points to search for nearest neighbors.
    distance_km : float
        The search radius in kilometers.
    analysis_crs : CRS or str
        The coordinate reference system to use for distance calculations.
    distance_col : str, optional
        The name of the column to store computed distances (default is "distance").
    preview : bool, optional
        If True, generates a plot preview of the filtered points and origin.

    Returns
    -------
    GeoDataFrame
        A GeoDataFrame of points within the specified distance, sorted by proximity.
    """
    import matplotlib.pyplot as plt

    # Convert distance to meters
    distance_m = distance_km * 1000

    # Reproject both GeoDataFrames to the analysis CRS
    origin_point = origin_point.to_crs(analysis_crs)
    points_gdf = points_gdf.to_crs(analysis_crs)

    # Perform spatial join to find nearest points
    nearest_df = origin_point[["Facility Name", "geometry"]].sjoin_nearest(
        points_gdf, how="right", distance_col=distance_col, exclusive=True
    )

    # Filter points within the specified distance and sort by proximity
    ordered_within_distance = nearest_df[
        nearest_df[distance_col] < distance_m
    ].sort_values(by=distance_col)

    # Optional preview plot
    if preview and not ordered_within_distance.empty:
        ax = ordered_within_distance.reset_index().plot(markersize=15)

        # Set plot title
        ax.set_title(f"Nearby Points within {distance_km} km of Origin", fontsize=14)

        # Hide axis ticks and labels for cleaner visualization
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel("")
        ax.set_ylabel("")

        # Overlay origin point in red
        origin_point.plot(color="red", marker="+", ax=ax)

        plt.show()

    return ordered_within_distance


def plot_travel_times_map(
    travel_gdf, destination_point, analysis_crs, overlay_admin_gdf=None, savefig=False
):
    """
    Plots a static map showing travel times from origin points to a destination facility.

    Parameters
    ----------
    travel_gdf : GeoDataFrame
        GeoDataFrame containing origin points with a 'travel_time' column representing
        travel time to the destination.

    destination_point : GeoDataFrame
        GeoDataFrame containing the destination facility as a point geometry.

    analysis_crs : str or pyproj.CRS
        The coordinate reference system to which all geometries should be projected for consistent plotting.

    overlay_admin_gdf : GeoDataFrame
        (Optional) GeoDataFrame of administrative boundaries (e.g., districts)
        to overlay on the map. If None, no boundaries are plotted.

    savefig : bool, optional (default=False)
        If True, saves the plot as a PNG image to 'outputs/travel_time_map.png'.

    Returns
    -------
    None
        Displays the map and optionally saves it to disk.
    """

    ax = travel_gdf.plot(
        figsize=(12, 12),
        label="Origins",
        column="travel_time",
        cmap="viridis",
        legend=True,
        legend_kwds={"label": "minutes", "orientation": "horizontal"},
        missing_kwds={
            "color": "lightgrey",
            "hatch": "///",
            "label": "Missing values",
        },
    )
    if overlay_admin_gdf is not None:
        overlay_admin_gdf.to_crs(analysis_crs).boundary.plot(
            ax=ax, color="black", linestyle="--"
        )
    destination_point.plot(
        ax=ax, color="red", markersize=25, marker="P", label="Destination"
    )
    ax.set_title("Travel time from origin to destination")
    ax.set_axis_off()
    if savefig:
        plt.savefig("outputs/travel_time_map.png", dpi=300)
    plt.show()


def return_within_radius(
    central_point,
    pop_grid_gdf,
    districts_gdf,
    radius_in_km,
    analysis_crs,
    preview=False,
):
    """
    Identifies population grid cells and administrative districts within a specified radius
    of a central point, and optionally visualizes the result.

    Parameters
    ----------
    central_point : GeoDataFrame
        A GeoDataFrame containing a single point geometry representing the central location
        from which the radius is measured.

    pop_grid_gdf : GeoDataFrame
        GeoDataFrame containing gridded population data with polygon geometries.

    districts_gdf : GeoDataFrame
        GeoDataFrame containing administrative district boundaries.

    radius_in_km : int
        Radius around the central point, in kilometers, used to filter nearby grids and districts.

    analysis_crs : CRS or str
        The coordinate reference system used for spatial operations and distance calculations.

    preview : bool, optional (default=False)
        If True, displays a static map showing the population grids, district boundaries,
        and the central point.

    Returns
    -------
    grids_within_radius : GeoDataFrame
        Subset of the population grid GeoDataFrame containing only cells within the radius.

    clipped_districts : GeoDataFrame
        Subset of the districts GeoDataFrame containing only districts intersecting the radius.
    """

    # Reproject all GeoDataFrames to the analysis CRS for consistent spatial operations
    central_point = central_point.to_crs(analysis_crs)
    pop_grid_gdf = pop_grid_gdf.to_crs(analysis_crs)
    districts_gdf = districts_gdf.to_crs(analysis_crs)

    # Convert radius from kilometers to meters
    radius_in_metres = radius_in_km * 1000

    # Create a buffer zone around the central point
    buffer_area = central_point.geometry.buffer(radius_in_metres)

    # Spatial join to find population grid cells within the buffer
    grids_within_radius = gpd.sjoin(
        pop_grid_gdf,
        buffer_area.to_frame(name="geometry"),
        how="inner",
    )

    # Spatial join to find districts intersecting the buffer
    clipped_districts = gpd.sjoin(
        districts_gdf,
        buffer_area.to_frame(name="geometry"),
        how="inner",
    )

    # Drop 'index_right' if it exists to prepare for next join
    if "index_right" in grids_within_radius.columns:
        grids_within_radius = grids_within_radius.drop(columns=["index_right"])

    if "index_right" in clipped_districts.columns:
        clipped_districts = clipped_districts.drop(columns=["index_right"])

    # Optional visualization of the results
    if preview:
        ax = grids_within_radius.plot(
            figsize=(12, 12), label="Population Grid", column="population"
        )
        clipped_districts.boundary.plot(
            ax=ax, color="black", linestyle="--", label="District Boundaries"
        )
        central_point.plot(ax=ax, color="red", markersize=15, label="Central Point")

        # Add title and clean up axes
        ax.set_title(
            f"Population Grids and Districts within {radius_in_km} km", fontsize=14
        )
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.legend()

        plt.show()

    return grids_within_radius, clipped_districts


def evaluate_travel_times_to_facilities(
    population_grids,
    hcf_points,
    transport_network,
    analysis_crs,
    transport_mode,
    max_travel_time,
    unit_of_time,
    snap_to_network_bool=False,
):
    """
    Calculates travel times from population grid centroids to a healthcare facility
    using a specified transport mode.

    Parameters
    ----------
    population_grids : GeoDataFrame
        GeoDataFrame containing population grid cell geometries.
    hcf_points : GeoDataFrame
        GeoDataFrame containing the healthcare facility (or facilities) positions.
    transport_network : r5py.TransportNetwork
        The transport network object used for routing and travel time calculations.
    pop_grid_gdf : GeoDataFrame
        The full population grid GeoDataFrame, used for merging travel time results.
    analysis_crs : str or int
        The coordinate reference system used for spatial analysis.
    transport_mode : r5py.TransportMode
        The mode of transport to use for travel time calculations (e.g., WALK, BICYCLE, CAR).
    max_travel_time : int or float
        The maximum travel time allowed, expressed in the unit specified by `unit_of_time`.
    unit_of_time : str
        Unit of time for `max_travel_time`. Must be either "minutes" or "hours".

    Returns
    -------
    travel_gdf : GeoDataFrame
        A GeoDataFrame containing travel times joined with population grid geometries.
    """

    # Convert travel time to seconds based on the specified unit
    if unit_of_time == "minutes":
        seconds = max_travel_time * 60
    elif unit_of_time == "hours":
        seconds = max_travel_time * 3600
    else:
        raise ValueError("unit_of_time must be either 'minutes' or 'hours'")

    # Reproject all GeoDataFrames to the analysis CRS for consistent spatial operations
    population_grids = population_grids.to_crs(analysis_crs)
    hcf_points = hcf_points.to_crs(analysis_crs)

    # Generate centroids from origin grid polygons
    population_grid_centroids = geo_util.return_grid_centroids(population_grids.copy())

    print("Calculating travel times, please wait...")

    start_time = time.time()

    # Compute travel times using r5py
    travel_times = r5py.TravelTimeMatrix(
        transport_network,
        origins=hcf_points,
        destinations=population_grid_centroids,
        transport_modes=[transport_mode],
        snap_to_network=snap_to_network_bool,
        max_time=datetime.timedelta(seconds=seconds),
        max_bicycle_traffic_stress=4,  # most permissive option
    )
    print(
        f"Travel time calculations running time: {round(time.time() - start_time, 2)} seconds"
    )

    print(
        "Finished calculating travel times. Processing travel times and plotting if selected"
    )

    ttm_df = pd.DataFrame(travel_times)

    # dropping all nan travel times from invalid origin-destination pairs
    ttm_df = ttm_df[~ttm_df.travel_time.isna()].reset_index(drop=True)

    return ttm_df


def calculate_travel_times_to_sample_facilities(
    hcf_gdf,
    transport_network,
    pop_grid_gdf,
    random_number_of_facilities,
    districts_gdf,
    radius_in_km,
    analysis_crs,
    transport_mode,
    travel_time,
    unit_of_time,
    output_map=False,
):
    """
    Calculates travel times from population grid cells to a sample of healthcare facilities.

    This function selects a subset of healthcare facilities (either randomly or all), identifies nearby
    population grid cells within a specified radius, and computes travel times using a transport network.

    Parameters
    ----------
    hcf_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing the locations and attributes of healthcare facilities.

    transport_network : networkx.Graph or custom network object
        The transport network used for calculating travel times. Must support snapping and routing.

    pop_grid_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing population grid cells with spatial and demographic information.

    random_number_of_facilities : str
        If "YES", randomly selects up to 100 facilities from `hcf_gdf` (if more than 100 exist).
        If "NO", uses all facilities in `hcf_gdf`.

    radius_in_km : int
        The search radius (in kilometers) around each facility to identify relevant population grids.

    analysis_crs : str or int
        Coordinate reference system used for spatial analysis and travel time computation.

    Returns
    -------
    all_times : list of geopandas.GeoDataFrame
        A list of GeoDataFrames, each containing travel time results from nearby population grids
        to a sampled healthcare facility.

    snapping_error_fac : list of str
        List of facility names for which travel time calculation failed due to snapping errors
        (e.g., no valid destination points after network snapping).
    """

    all_times = []

    # To know facilities 'After snapping, no valid destination points remain'
    snapping_error_fac = []

    print(f"Total input facilities: {len(hcf_gdf)}")

    if random_number_of_facilities == "YES":
        if len(hcf_gdf) > 100:
            random_hcfs = hcf_gdf.sample(100, random_state=42)
            print("Randomly selected 100 facilities.")
        else:
            random_hcfs = hcf_gdf
            print("Using all facilities (<=100).")
    elif random_number_of_facilities == "NO":
        random_hcfs = hcf_gdf
        print("Using all facilities (no random sampling).")
    else:
        raise ValueError("random_number_of_facilities must be 'YES' or 'NO'")

    # Reproject all GeoDataFrame to analysis CRS for consistent spatial operations
    random_hcfs = random_hcfs.to_crs(analysis_crs)

    print(f"Number of facilities to process: {len(random_hcfs)}")

    for idx, row in random_hcfs.iterrows():
        print(
            f"\nProcessing facility: {row.get('Facility Name', 'Unknown')} (Index: {idx})"
        )

        grids_within_radius, clipped_districts = geo_util.return_within_radius(
            central_point=random_hcfs.loc[[idx]],
            pop_grid_gdf=pop_grid_gdf,
            districts_gdf=districts_gdf,
            radius_in_km=radius_in_km,
            analysis_crs=analysis_crs,
            preview=False,
        )

        print(f"Grids found within {radius_in_km}km: {len(grids_within_radius)}")

        if grids_within_radius.empty:
            print("No grids found. Skipping this facility.")
            continue

        try:
            travel_gdf = geo_util.evaluate_travel_times_to_facilities(
                origin_grids=grids_within_radius,
                destination_point=random_hcfs.loc[[idx]],
                transport_network=transport_network,
                pop_grid_gdf=pop_grid_gdf,
                analysis_crs=analysis_crs,
                transport_mode=transport_mode,
                travel_time=travel_time,
                unit_of_time=unit_of_time,
                overlay_admin_gdf=clipped_districts,
                output_map=False,
            )
        except ValueError as e:
            print(
                f"Snapping error for facility '{row.get('Facility Name', 'Unknown')}': {e}"
            )
            snapping_error_fac.append(row.get("Facility Name", "Unknown"))
            continue

        print(f"Travel time results: {len(travel_gdf)} rows")
        all_times.append(travel_gdf)

    print(f"\nTotal successful travel time results: {len(all_times)}")
    print(f"Facilities with snapping errors: {len(snapping_error_fac)}")

    return all_times, snapping_error_fac
