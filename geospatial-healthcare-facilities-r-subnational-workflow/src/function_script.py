# %%
# Import packages
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import geopandas as gpd
from pathlib import Path
import folium
from sklearn.cluster import DBSCAN


# %%
# Function for cleaning OSM geopandas dataframe - assumes columns are the same
def osm_gdf_clean(data_dir, file_name):
    """
    Cleans an OpenStreetMap (OSM) GeoDataFrame by removing unnecessary columns,
    renaming key columns, and standardizing text formatting.

    Parameters:
    -----------
    file_name : str
        The name of the file (with extension) containing the OSM GeoDataFrame to be cleaned.
        The file is expected to be located in the `data_dir` directory.

    Returns:
        --------
    geopandas.GeoDataFrame
        A cleaned GeoDataFrame with selected columns removed, renamed, and formatted for consistency.

    Cleaning Steps:
    ---------------
    - Loads the GeoDataFrame from the specified file.
    - Drops columns with excessive missing values or irrelevant metadata.
    - Renames 'name' to 'Facility Name' and 'amenity' to 'Facility Type'.
    - Strips leading/trailing whitespace and capitalizes each word in the renamed columns.

    Further cleaning may need to be done
    """

    # Load gdf
    gdf = gpd.read_file(data_dir.joinpath(file_name))

    # Drop unnecessary columns with lots of NaN values
    # name:en, building, healthcare:speciality, capacity:persons, addr:full, addr:city, source, name:ny
    gdf.drop(
        columns=[
            "name:en",
            "building",
            "healthcare:speciality",
            "capacity:persons",
            "addr:full",
            "addr:city",
            "source",
            "name:ny",
            "osm_id",
            "osm_type",
            "operator:type",
        ],
        inplace=True,
    )

    # Change column names
    # name to Facility name and amenity to Facility type
    gdf.rename(
        columns={"name": "Facility Name", "amenity": "Facility Type"}, inplace=True
    )

    # Remove leading whitespace from column
    gdf["Facility Name"] = gdf["Facility Name"].str.strip()
    gdf["Facility Type"] = gdf["Facility Type"].str.strip()

    # Capitalize first letter of each word
    # Remove leading whitespace from column
    gdf["Facility Name"] = gdf["Facility Name"].str.title()
    gdf["Facility Type"] = gdf["Facility Type"].str.title()

    # Final cleaned gdf
    cleaned_osm_gdf = gdf

    return cleaned_osm_gdf


# %%
def clean_roads_from_osm(file_name, file_info):
    """
    Cleans and standardizes column names and string values
    in a GeoDataFrame loaded from a GeoJSON file. More specific
    cleaning may need to be done after however

    Parameters:
    ----------
    file_name : str
        The name of the GeoJSON file to be loaded.
    file_info : str
        A string indicating the type of data in the file.
        Accepts "road" or "surface" to determine which columns to clean and retain.

    Returns:
    -------
    gdf : geopandas.GeoDataFrame
        A cleaned GeoDataFrame with:
        - Selected columns renamed to sentence case.
        - Irrelevant columns removed.
    """

    # Load gdf
    gdf = gpd.read_file(data_dir.joinpath(file_name))

    # Make empty list
    cols_to_capitalise = []

    # Distinguish between gdf's
    if file_info == "road":

        # Loop through column headers
        for col in gdf:
            if (
                isinstance(col, str)
                and "name:" not in col
                and type(col) is str
                and "geometry" not in col
                and "osm" not in col
                and "source" not in col
                and "layer" not in col
            ):

                cols_to_capitalise.append(col)

    elif file_info == "surface":
        # Sentence case for headers
        for col in gdf:
            if (
                isinstance(col, str)
                and "name:" not in col
                and "geometry" not in col
                and "osm" not in col
                and "continent" not in col
                and "country" not in col
                and "urban" not in col
                and "pred" not in col
                and "source" not in col
                and "time" not in col
                and "layer" not in col
                and "combined" not in col
                and "layer" not in col
            ):

                cols_to_capitalise.append(col)

    # Apply sentence case to selected columns
    gdf.rename(
        columns={col: col.capitalize() for col in cols_to_capitalise}, inplace=True
    )

    # Capitalise column names in list
    cols_to_keep = [word.title() for word in cols_to_capitalise]

    # Append geometry column to list as needs to be kept
    cols_to_keep.append("geometry")

    # Filter out irrelevant coloumns from gdf
    gdf = gdf[cols_to_keep]

    # Loop through str columns to remove white space and cap first letter of each word
    for col in gdf:
        if col != "geometry" and gdf[col].dtype == "object":
            gdf[col] = gdf[col].str.strip()
            gdf[col] = gdf[col].str.title()

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


# %%
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


# %%
def clean_gdf_boundaries(file_name, column_name_to_change):
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
    gdf = gpd.read_file(data_dir.joinpath(file_name))

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

        # Drop irrelevant columns is OSM gdf
        gdf.drop(
            columns=["shapeISO", "shapeID", "shapeGroup", "shapeType"], inplace=True
        )

    else:
        print("Update function to work with your geopandas dataframe...")

    # Final cleaned gdf
    cleaned_gdf = gdf

    return cleaned_gdf


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

    else:
        print("Column not found or try `to_id` if Facility Name didn't work")

    return stats_df


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
