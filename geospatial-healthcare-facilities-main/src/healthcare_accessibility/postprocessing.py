import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd

import healthcare_accessibility.data_processing_funcs as dp_funcs


def convert_travel_time_to_distance(travel_time_df, mode_of_transport):
    """
    Convert travel time to distance using average speeds for different modes of transport.

    Parameters
    ----------
    travel_time_df : pandas.DataFrame
        DataFrame containing travel time data with a 'travel_time' column.
    mode_of_transport : str
        The mode of transport (e.g., 'bicycle', 'car', 'walk').

    Returns
    -------
    pandas.DataFrame
        DataFrame with an additional 'travel_distance' column representing distance in kilometers.
    """

    # Define average speeds in km/h for different modes of transport
    average_speeds = {
        "walk": 3.6,  # Average walking speed in km/h (r5py default = 3.6 km/h)
        "bicycle": 12,  # Average cycling speed in km/h (r5py default = 12 km/h)
    }

    if mode_of_transport not in average_speeds:
        raise ValueError(
            f"Mode of transport '{mode_of_transport}' not recognized. Please add it to the average_speeds dictionary."
        )

    # Get the average speed for the specified mode of transport
    speed_kmh = average_speeds[mode_of_transport]

    travel_dist_time_df = travel_time_df.copy()

    # Convert travel time from minutes to hours and calculate distance
    travel_dist_time_df["travel_distance"] = (
        travel_dist_time_df["travel_time"].div(60.0).multiply(speed_kmh)
    )

    return travel_dist_time_df


def filter_by_distance_threshold(distance_matrix_df, distance_threshold):
    """
    Filter the distance matrix to include only grid cells within a specified distance threshold.

    Parameters
    ----------
    distance_matrix_df : pandas.DataFrame
        DataFrame containing travel distance data with a 'travel_distance' column.
    distance_threshold : float
        The maximum travel distance (in kilometers) to include in the filtered results.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing only rows where 'travel_distance' is less than or equal to the specified threshold.
    """
    within_threshold_df = distance_matrix_df[
        distance_matrix_df["travel_distance"] <= distance_threshold
    ]
    return within_threshold_df


def attach_travel_time(trav_mtx_gdf, ttm, mode_of_transport):
    """
    Attach travel times between origin-destination pairs for the given mode of transport.

    Parameters
    ----------
    trav_mtx_gdf : gpd.GeoDataFrame
        Geodataframe containing origin-destination pairs and travel times.
    ttm : _type_
        _description_
    mode_of_transport : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    ttm = ttm.rename(columns={"travel_time": f"{mode_of_transport}_travel_time"})
    merged_gdf = trav_mtx_gdf.merge(
        ttm[["from_id", "to_id", f"{mode_of_transport}_travel_time"]],
        left_on=["from_id", "to_id"],
        right_on=["from_id", "to_id"],
        how="left",
    )
    return merged_gdf


def return_population_within_threshold(
    grids_in_threshold: gpd.GeoDataFrame, pop_gdf: gpd.GeoDataFrame
) -> pd.DataFrame:
    """
    Return population statistics within threshold travel areas.

    Parameters
    ----------
    grids_in_threshold : gpd.GeoDataFrame
        _description_
    pop_gdf : gpd.GeoDataFrame
        _description_
    geog : str
        _description_

    Returns
    -------
    pd.DataFrame
        _description_
    """
    pop_stats_dict = {}

    total_pop = pop_gdf.population.sum()
    total_pop_included = grids_in_threshold.population.sum()
    total_pop_excluded = pop_gdf.population.sum() - total_pop_included
    pop_stats_dict["national"] = pd.DataFrame(
        {
            "total_population_included": [total_pop_included],
            "percentage_included": [total_pop_included / total_pop * 100],
            "total_population_excluded": [total_pop_excluded],
            "percentage_excluded": [total_pop_excluded / total_pop * 100],
            "total_population": [total_pop],
        }
    )
    for geog in ["ADM1", "ADM2"]:
        agg_total_pops = pop_gdf.groupby(geog).agg({"population": "sum"})
        included_pop = grids_in_threshold.groupby(geog).agg({"population": "sum"})
        excluded_pop = agg_total_pops.population - included_pop.population
        excluded_pop_pct = excluded_pop / agg_total_pops.population * 100
        percentage_included = included_pop.population / agg_total_pops.population * 100
        pop_stats_dict[geog] = pd.DataFrame(
            {
                "included_population": included_pop.population,
                "percentage_included": percentage_included,
                "excluded_population": excluded_pop,
                "percentage_excluded": excluded_pop_pct,
                "total_population": agg_total_pops.population,
            }
        )
    return pop_stats_dict


def plot_excluded_population_by_admin_areas(
    pop_stats_result_df, distance_threshold, admin_area_col="ADM2", label_fontsize=18
):
    """
    Create a horizontal bar plot showing the percentage of population excluded from service areas
    within a specified distance threshold, grouped by administrative areas.

    Parameters
    ----------
    pop_stats_result_df : dict
        Dictionary containing population statistics DataFrames for different administrative levels.
    distance_threshold : float
        The distance threshold used to determine service area inclusion.
    admin_area_col : str, optional
        The administrative area column to group by, by default "ADM2"
    label_fontsize : int, optional
        The font size for labels, by default 18
    """
    plt.figure(figsize=(10, 8), dpi=300)
    pop_stats_result_df[admin_area_col].percentage_excluded.sort_values().plot(
        kind="barh"
    )
    plt.xlabel("Percentage of population excluded (%)", fontsize=label_fontsize)
    plt.title(
        f"Percentage of population excluded from service area within {distance_threshold} km by {admin_area_col} admin areas"
    )
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.show()


def calc_cumulative_percentage(gdf, sub_total_pop, travel_metric="travel_time"):
    """
    Compute cumulative population and cumulative percentage for sorted travel times.

    Parameters
    ----------
    gdf : DataFrame
        Travel time data sorted by travel_time.
    sub_total_pop : DataFrame
        Population grid for the relevant area.
    travel_metric : str, optional
        The travel metric to use for the x-axis (default is "travel_time"). Can be

    Returns
    -------
    DataFrame
        DataFrame with cumulative population and percentage columns.
    """
    if "population" not in gdf.columns:
        gdf = dp_funcs.recombine_travel_matrix_with_pop_data(
            gdf, sub_total_pop, join_type="left"
        )

    gdf = dp_funcs.return_nearest_travel_outcome(
        gdf,
        grid_cell_id_column="to_id",
        travel_outcome_column=travel_metric,
    )

    gdf.sort_values(travel_metric, inplace=True)

    # computing cumulative population
    gdf["cumulative_population"] = gdf["population"].cumsum()

    total_population = sub_total_pop[
        "population"
    ].sum()  # uses source pop grid data to capture all populated grids

    # converting to cumulative %
    gdf["cumulative_percentage"] = gdf["cumulative_population"] / total_population * 100

    return gdf


def generate_cumulative_pop_plot(
    gdf,
    travel_metric="travel_time",
    location_description="nationwide",
    max_time=180,
    max_distance=25,
    labels_fontsize=20,
    title_fontsize=16,
    highlight_line=None,
):
    """
    Generate plot of cumulative percentage of population by travel time or distance.

    Parameters
    ----------
    gdf : DataFrame
        DataFrame containing travel time/distance and cumulative percentage data.
    travel_metric : str, optional
        The travel metric to plot on the x-axis (default is "travel_time").
    location_description : str, optional
        A description of the location for the plot title, such as a region name. Default is "nationwide".
    max_time : int, optional
        If metric is travel_time, the maximum travel time to display on the x-axis (default is 180).
    max_distance : int, optional
        If metric is travel_distance, the maximum travel distance to display on the x-axis (default is 25).
    labels_fontsize : int, optional
        The font size for the axis labels (default is 20).
    title_fontsize : int, optional
        The font size for the plot title (default is 16).
    highlight_line : float, optional
        The x-value at which to draw a vertical line (default is None).
    """
    plt.figure(figsize=(10, 8), dpi=300)
    plt.plot(gdf[travel_metric], gdf["cumulative_percentage"])  # , linestyle="-")

    if "travel_time" in travel_metric:
        plt.xlim(0, max_time)
        plt.xlabel("Travel Time (minutes)", fontsize=labels_fontsize)
        plt.title(
            f"Percentage of population within given travel time to the nearest facility {location_description}",
            fontsize=title_fontsize,
        )
    elif travel_metric == "travel_distance":
        plt.xlim(0, max_distance)
        plt.xlabel("Travel Distance (km)", fontsize=labels_fontsize)
        plt.title(
            f"Percentage of population within given travel distance \nto the nearest facility {location_description}",
            fontsize=title_fontsize,
        )
    plt.minorticks_on()
    plt.ylabel("Included Population (%)", fontsize=labels_fontsize)
    plt.ylim(0, 100)
    if highlight_line is not None:
        plt.vlines(x=highlight_line, ymin=0, ymax=100, colors="red", linestyles="--")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.show()


def plot_cumulative_population_by_travel_metric(
    travel_gdf,
    pop_gdf,
    travel_metric="travel_time",
    aggregate_admin=None,
    highlight_line=None,
    max_time=180,
    max_distance=25,
    labels_fontsize=20,
    title_fontsize=16,
):
    """
    Plot cumulative percentage of population by travel time or distance.

    Parameters
    ----------
    travel_gdf : DataFrame
        DataFrame containing travel time/distance and cumulative percentage data.
    travel_metric : str, optional
        The travel metric to plot on the x-axis (default is "travel_time").
    aggregate_admin : str, optional
        The administrative area column to aggregate by (e.g., "ADM1", "ADM2"). Optional.
    highlight_line : float, optional
        The x-value at which to draw a vertical line (default is None).
    max_time : int, optional
        If metric is travel_time, the maximum travel time to display on the x-axis (default is 180).
    max_distance : int, optional
        If metric is travel_distance, the maximum travel distance to display on the x-axis (default is 25).
    labels_fontsize : int, optional
        The font size for the axis labels (default is 20).
    title_fontsize : int, optional
        The font size for the plot title (default is 16).
    """
    if aggregate_admin:
        for adm_area in pop_gdf[aggregate_admin].unique():
            if adm_area is not None:
                print(f"Generating plot for {adm_area}")
                filtered_pop_gdf = pop_gdf[pop_gdf[aggregate_admin] == adm_area]
                gdf = calc_cumulative_percentage(
                    travel_gdf[travel_gdf[travel_metric].notna()],
                    filtered_pop_gdf,
                    travel_metric=travel_metric,
                )
                generate_cumulative_pop_plot(
                    gdf,
                    travel_metric=travel_metric,
                    location_description=f"in {adm_area}",
                    max_time=max_time,
                    max_distance=max_distance,
                    labels_fontsize=labels_fontsize,
                    title_fontsize=title_fontsize,
                    highlight_line=highlight_line,
                )
    else:
        gdf = calc_cumulative_percentage(
            travel_gdf[travel_gdf[travel_metric].notna()],
            pop_gdf,
            travel_metric=travel_metric,
        )
        generate_cumulative_pop_plot(
            gdf,
            travel_metric=travel_metric,
            max_time=max_time,
            labels_fontsize=labels_fontsize,
            title_fontsize=title_fontsize,
            highlight_line=highlight_line,
        )
