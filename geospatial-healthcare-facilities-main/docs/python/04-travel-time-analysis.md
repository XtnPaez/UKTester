# Travel Time Analysis

Travel time estimation is carried out by `pop_travel_times.py`. It computes travel times between every populated grid cell and every healthcare facility along the road network, for each configured transport mode.

## Before running

Ensure you have completed the data preparation step and all processed output files exist. See [03 — Data preparation](03-data-preparation.md).

## Adjustable parameters

The following variables near the top of `src/healthcare_accessibility/pop_travel_times.py` can be changed before running:

### `max_travel_time_mins`

Sets the upper limit at which travel times are returned. Any routes beyond this threshold are excluded. Default is `120` (two hours).

- Increasing this value captures more origin-destination pairs but increases runtime and output file size.
- Decreasing it risks excluding journeys that fall within accessibility thresholds of interest.

At 120 minutes, approximate maximum travel distances are:

- Bicycle: ~24 km (the default travel metric)
- Walking: ~7.2 km

> NOTE: This maximum travel distance has important implications for further analysis. Within the dashboard the user defines a threshold for accessability, this threshold should not exceed the maximum travel-time derived distance for BICYCLE travel. See **Max travel time limitations** in the [Methodology documentation](../methodology.md#limitations-and-caveats) for more details.

### `transport_modes_dict`

Controls which transport modes are included. Default is bicycle only, which is also the minimum requirement for the downstream dashboard.

```python
transport_modes_dict = {
    "bicycle": r5py.TransportMode.BICYCLE,
    # "car": r5py.TransportMode.CAR,
    # "walk": r5py.TransportMode.WALK,
}
```

Car and walking modes are available but currently unsupported in the dashboard display. Uncomment to generate their parquet outputs.

## Run the script

From the repository root:

```bash
python src/healthcare_accessibility/pop_travel_times.py
```

## Outputs

Results are written to `outputs/<country>/`. For each active transport mode:

- `<mode>_travel_times_to_All healthcare facilities.parquet` — full origin-destination travel-time matrix (GZIP compressed)
- A national HTML travel-time map (note: national maps are large and may not load in most browsers)
- Per-ADM1 region HTML travel-time maps

## Expected runtimes

These are indicative — actual times depend on available hardware and memory.

| Country | Facilities | Grid cells | Mode | Approx. runtime | Notes |
| --- | --- | --- | --- | --- | --- |
| Rwanda | ~1.3K | ~26K | Bicycle | ~2 mins | — |
| Switzerland | ~6K | ~53K | Bicycle | ~30 mins | — |
| Nepal | ~6.8K | ~116K | Bicycle | ~1 hour | Requires >5.6 GB RAM |
| Bangladesh | ~7.6K | ~156K | Bicycle | — | Memory errors observed at national scale |

## Scalability limitation and proposed solution

For large, densely populated countries the number of origin-destination pairs can exceed available memory at national scale.

The recommended approach is to segment the country into sub-national areas (for example by ADM1 region), run the analysis for each segment independently, and then recombine results.

**Important:** to avoid boundary effects where valid journeys near a segment border are missed, add a spatial buffer around each segment when clipping inputs. The buffer should comfortably exceed your largest accessibility threshold of interest — a buffer of 20 km is reasonable where 10 km thresholds are important. This will produce duplicate pairs across segment boundaries, so deduplication is required when recombining.

## Optional extra: accessibility population charts

Outside of the core workflow, there is an additional script that can be run after travel-time analysis to generate extra accessibility outputs focused on population inclusion and exclusion.

Script:

`src/healthcare_accessibility/accessability_metrics.py`

Run from repository root:

```bash
python src/healthcare_accessibility/accessability_metrics.py
```

What it provides:

- Charts of excluded population percentages by admin area (ADM1 and ADM2)
- Cumulative population accessibility charts by travel distance (and travel time where available)

When to run it:

- After `pop_travel_times.py` has completed successfully
- Optionally in parallel to dashboard work (for example in a separate terminal session)

Running in VS Code as notebook-style cells:

- The script includes `# %%` cell markers, so it can be executed step-by-step in VS Code's Interactive Window/Jupyter-style workflow.
- Open `src/healthcare_accessibility/accessability_metrics.py` in VS Code and run cells sequentially from top to bottom.
- This is useful if you want to test threshold/metric changes iteratively without restarting the full script each time.

Current script assumptions:

- Reads travel-time parquet files from `outputs/<country>/`
- Uses processed population and healthcare facility files from `data/<country>/processed_data/`
- Expects bicycle travel matrix and, in its current implementation, also references walking and car matrices when attaching mode-specific travel times

Key adjustable options in `accessability_metrics.py`:

- `distance_threshold` (default `10`): controls the service-area threshold (km) used for excluded/included population summaries.

Related plotting controls:

- `highlight_line`: draws a vertical reference marker on cumulative plots.
- `max_time` and `max_distance`: set x-axis limits for time/distance chart variants.

Practical usage examples:

```python
# Service area threshold used in excluded-population charts
distance_threshold = 10
```

Note:

- This script is optional and not required for the core workflow or dashboard creation.
- The charts are displayed interactively (matplotlib) and are not automatically persisted as files unless you add save commands.

## Next step

→ [05 — Dashboard](05-dashboard.md)
