import requests
from pathlib import Path
import matplotlib.pyplot as plt
import geopandas as gpd
import osmnx as ox
import pandas as pd
import yaml

from healthcare_accessibility.utils import continue_confirmation


def acquire_latest_osm_data(country, continent, output_filepath, force_overwrite=False):
    """
    Uses the Geofabrik API to download the latest OSM data for a given country.

    Parameters
    ----------
    country : str
        The country of interest
    continent : str
        The continent in which the desired country is located
    output_filepath : str or pathlib.Path
        The path to the output file for the downloaded OSM data.
    """

    country = country.lower()
    continent = continent.lower()

    output_filepath = Path(output_filepath)

    if not force_overwrite:
        generate_output_bool = continue_confirmation(output_filepath)
    else:
        generate_output_bool = False

    if generate_output_bool or force_overwrite:
        url = f"https://download.geofabrik.de/{continent}/{country}-latest.osm.pbf"

        print(f"Connecting and downloading from {url}")
        print(
            "This can take a while, particularly for larger countries, so please be patient..."
        )

        response = requests.get(url, timeout=30, verify=False)

        print(f"File downloaded.")

        print(f"Saving to {output_filepath}")

        output_filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(output_filepath, "wb") as f:
            f.write(response.content)
    else:
        print("User has chosen to use pre-existing OSM data file.")


def get_osm_admin_boundaries(country, admin_level, boundary_area_list):
    """
    Retrieve and filter OpenStreetMap administrative boundaries for a given country and admin level.
    This can take a few minutes depending on the Overpass max query area size. If too big It will
    automatically be divided up into multiple sub-queries accordingly. This may take a long time.

    Parameters:
    ----------
    country : str
        The name of the country to query (e.g., "Malawi").
    admin_level : str
        The administrative level to filter by (e.g., 2 for country, 4 for districts).

    admin_level | Description	                       | Example (Malawi)
    2	        | Country	                           | Malawi
    4	        | Region / Province (if applicable)	   | Central Region
    6	        | District	                           | Lilongwe, Blantyre, Mzimba, etc.
    8	        | Sub-district / Traditional Authority | TA Kalolo, TA Mponela, etc.
    10	        | Village / Locality	               | Individual villages or towns

    boundary_area_list : list of str
        A list of area names (e.g., districts or regions) to include in the result.

    Returns:
    -------
    GeoDataFrame
        A GeoDataFrame containing the filtered administrative boundaries with columns:
        'geometry', 'admin_level', and 'name'. Only Polygon and MultiPolygon geometries are included.
    """

    # Define the place and tags
    place_name = country
    tags = {"boundary": "administrative", "admin_level": admin_level}

    # Get administrative boundaries
    gdf = ox.features_from_place(place_name, tags=tags)

    # Filter GeoDataFrame
    gdf = gdf[gdf["name"].isin(boundary_area_list)]

    # Reset index
    gdf = gdf.reset_index()

    # Select columns
    gdf = gdf[["geometry", "admin_level", "name"]]

    # Only want Polygons and Multipolygons
    gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]

    return gdf


def individual_osm_boundaries(country, boundary_type, boundary_area_list):
    """
    Retrieve and combine OpenStreetMap administrative boundaries for specified areas.

    Parameters
    ----------
    country : str
        The country in which the boundaries are located (e.g., "Malawi").
    boundary_type : str
        The type of administrative boundary to query (e.g., "District", "Region").
    boundary_area_list : list of str
        A list of area names (e.g., district names) to retrieve boundaries for.

    Returns
    -------
    GeoDataFrame
        A GeoDataFrame containing the geometries and names of successfully retrieved boundaries.
        Only includes Polygon and MultiPolygon geometries, and filters to the requested area names.

    Notes
    -----
    - Uses `osmnx.geocode_to_gdf()` to query boundaries from OpenStreetMap.
    - Prints success or failure messages for each area.
    - Filters

    """

    gdfs = []

    for boundary in boundary_area_list:
        try:
            gdf = ox.geocode_to_gdf(f"{boundary} {boundary_type}, {country}")
            gdf["name"] = boundary  # Optional: label each boundary
            gdfs.append(gdf)
            print(f"✅ Success: {boundary}")  # Can remove
        except Exception as e:
            print(f"❌ Failed: {boundary}: {e}")  # Can remove

    # Only concatenate if there are successful results
    if gdfs:
        combined_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
        combined_gdf = combined_gdf.set_crs("EPSG:4326")
        print("✅ Combined GeoDataFrame created.")
    else:
        print("⚠️ No valid boundaries found.")

    # Filter GeoDataFrame
    combined_gdf = combined_gdf[combined_gdf["name"].isin(boundary_area_list)]

    # Select columns
    combined_gdf = combined_gdf[["geometry", "name"]]

    # Only want Polygons and Multipolygons
    combined_gdf = combined_gdf[
        combined_gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    ]

    return combined_gdf


def osm_district_and_road_network(
    country, district_name, healthcare_facility, distance, network_type, gdf=None
):
    """
    Visualizes the district boundary, road network, and healthcare facility network using OpenStreetMap data.

    Parameters:
    ----------
    country : str
        Name of the country where the district is located.
    district_name : str
        Name of the district to be visualized.
    healthcare_facility : str
        Name of the healthcare facility to locate and visualize its surrounding network.
    distance : int or float
        Distance (in meters) for the network graph around the healthcare facility.
    network_type : str
        Type of road network to retrieve (e.g., 'drive', 'walk', 'bike', 'drive_service').
    gdf : geopandas.GeoDataFrame, optional
        GeoDataFrame containing healthcare facility geometries. Used as a fallback if geocoding fails.

    Returns:
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing the district boundary.
    networkx.MultiDiGraph
        The road network graph for the entire district.
    networkx.MultiDiGraph or None
        The road network graph around the healthcare facility, or None if not found.

    Notes:
    -----
    - Uses OSMnx to retrieve and visualize geographic data.
    - If geocoding the healthcare facility fails, attempts to locate it in the provided GeoDataFrame.
    - Displays three subplots: district boundary, road network, and healthcare facility network.
    - Handles
    """

    # Get district boundary
    district = ox.geocode_to_gdf(f"{district_name}, {country}")
    polygon = district["geometry"].iloc[0]

    # Road network in district
    roads = ox.graph_from_polygon(polygon, network_type="drive_service")

    # Try geocoding the healthcare facility
    network_dist = None

    try:
        network_dist = ox.graph_from_address(
            address=f"{healthcare_facility}, {district_name}, {country}",
            dist=distance,
            dist_type="network",
            network_type=network_type,
        )
    except Exception as e:
        print(
            f"Geocoding failed: {e} Looking through GeoDataFrame for {healthcare_facility} coordinates."
        )

        # Fallback: use geometry from gdf if facility is found
        if gdf is not None:
            # Looks for the healthcare facility match in the gdf
            match = gdf[gdf["Facility Name"].str.lower() == healthcare_facility.lower()]
            print(f"Match found will use geometry")

            if not match.empty:
                try:
                    geom = match.geometry.iloc[0]  # uses geometry from match
                    if geom.geom_type == "Point":
                        lat, lon = geom.y, geom.x

                    else:
                        centroid = geom.centroid
                        lat, lon = centroid.y, centroid.x

                    network_dist = ox.graph_from_point(
                        center_point=(lat, lon),
                        dist=distance,
                        dist_type="network",
                        network_type=network_type,
                    )
                except Exception as fallback_error:
                    print(f"Fallback using geometry failed: {fallback_error}")

    # Create subplots
    fig, axs = plt.subplots(1, 3, figsize=(18, 6))

    # Plot district boundary
    district.plot(ax=axs[0], facecolor="gray", edgecolor="black")
    axs[0].set_title(f"{district_name} District Boundary")
    axs[0].axis("off")

    # Plot road network with black background
    axs[1].set_facecolor("black")
    ox.plot_graph(
        roads,
        ax=axs[1],
        node_size=0,
        edge_color="white",
        edge_linewidth=0.3,
        show=False,
        close=False,
    )
    axs[1].set_title(f"{district_name} Road Network", color="black")

    # Plot healthcare facility network if available
    if network_dist and len(network_dist.edges) > 0:
        ox.plot_graph(
            network_dist,
            ax=axs[2],
            node_color="r",
            node_size=10,
            edge_color="gray",
            show=False,
            close=False,
        )
        axs[2].set_title(
            f"{distance}km Network from {healthcare_facility}-{network_type.title()}"
        )
    else:
        axs[2].text(
            0.5, 0.5, "Facility network not available", ha="center", va="center"
        )
        axs[2].set_title("Network Unavailable")
        axs[2].axis("off")

    plt.tight_layout()
    plt.show()

    return district, roads, network_dist


def convert_hcf_polygons_to_points(config, save_output=False):
    """Converts non-point healthcare facility geometry data from OSM into points"""

    with open(config.get("datasets_config")) as file:
        datasets = yaml.safe_load(file)

    # Set relative path to data folder for notebook
    data_dir = Path(config.get("data_dir"))

    # Use function for initial cleaning and loading dataframe
    polygon_gdf = osm_gdf_clean(
        data_dir.joinpath(datasets.get("health_facility").get("hotosm_mwi_polygons"))
    )

    print(polygon_gdf.head())

    # Capitalise every word
    polygon_gdf["healthcare"] = polygon_gdf["healthcare"].str.title()

    # Fill Facility Type column with healthcare if empty
    polygon_gdf["Facility Type"] = polygon_gdf["Facility Type"].combine_first(
        polygon_gdf["healthcare"]
    )

    # Drop healthcare column
    polygon_gdf.drop(columns=["healthcare"], inplace=True)

    # Calculate the centroid of each polygon
    polygon_gdf["centroid"] = polygon_gdf.geometry.centroid

    # Rename polygon column
    polygon_gdf.rename(columns={"geometry": "polygon_geometry"}, inplace=True)

    # Rename polygon column
    polygon_gdf.rename(columns={"centroid": "geometry"}, inplace=True)

    # Drop healthcare column
    polygon_gdf.drop(columns=["polygon_geometry"], inplace=True)

    # Save complete gdf (missing regions and districts for some still!)
    if save_output:
        polygon_gdf.to_file(
            data_dir / "polygon_to_centroids_malawi_health_facilities.geojson",
            driver="GeoJSON",
        )

    return polygon_gdf
