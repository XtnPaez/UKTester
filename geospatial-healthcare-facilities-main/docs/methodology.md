# Introduction

Effective delivery of healthcare services depends on populations having adequate access to healthcare facilities. Accurate mapping of a country's health system infrastructure supports better planning and management of healthcare provision and helps ensure equitable distribution of resources, particularly during epidemics and disease outbreaks. However, many low- and middle‑income countries (LMICs), including those in sub‑Saharan Africa, can lack comprehensive and up‑to‑date information on healthcare access.

Building on the Office for National Statistics' (ONS) prior work on access to amenities, we developed a tool that combines:

- georeferenced locations of healthcare facilities,
- small‑area population estimates, and
- road network data,

to map healthcare facilities alongside the populations they serve and quantify levels of accessibility to these facilities.

A prototype version of this tool was initially developed and tested using Malawi as a case study. Following this initial development, further work is being undertaken to generalise the tool for wider application across multiple contexts as part of the Analysis for Action platform. This generalisable tool is what is being described in this document.

# Methodology

## Overview

A travel‑time–based approach is used to estimate healthcare accessibility. This involves generating origin–destination travel‑time matrices between population grid cells and healthcare facilities using routing software and road network maps. Travel times are then converted to distances across the road network, enabling visualisation of the population with reasonable access to healthcare services within specified distance thresholds.

## What data we use 

To estimate the population resident within some travel threshold of a healthcare facility we require: geospatial information on health facilities, spatially resolved population estimates and road network data.

**Table of data sources**

|Name |Source |
|:--- |:--- |
|Healthcare facilities |Health facility registers e.g. [Malawi Ministry of Health](https://zipatala.health.gov.mw/facilities) [1] or [Healthsites.io](https://healthsites.io/) data [2] |
|Population estimates |[WorldPop](https://hub.worldpop.org/geodata/summary?id=97503) [3] |
|Road network |[OpenStreetMap](https://www.openstreetmap.org/about) [4] data from [Geofabrik](https://download.geofabrik.de/) [5] in [`.osm.pbf`](https://wiki.openstreetmap.org/wiki/PBF_Format) format [6] |
|Administrative area boundaries |[OpenStreetMap](https://overpass-turbo.eu/s/2mPz) [7] or [geoBoundaries](https://www.geoboundaries.org/countryDownloads.html) [8] |

### Healthcare facilities

The tool relies on up to date georeferenced data on healthcare facilities in order to calculate estimates. Data with low completeness or accuracy will affect the number of people estimated to be within or outside a given distance of a healthcare facility due to missing or incorrect facility locations. It is therefore recommended that the most complete and accurate data available is used.

Accurate and regularly updated open geospatial data on health facilities at a country level are difficult to find. Often the most reliable data are collected by state agencies.

As a minimum, this workflow relies on the following features being available in the data:

- A unique healthcare facility identification (such as an ID number or facility name)
- Georeferenced coordinates for the facilities location (preferably a longitude and latitude)

#### Malawi case study
For the Malawi case study, we used the [Malawi Master Health Facility Register](https://zipatala.health.gov.mw/facilities) (MHFR) from the Malawi Ministry of Health [1]. This provides georeferenced health facilities by district and type.

**Example data from the Malawi Master Health Facility Register**    

|CODE |NAME |COMMON NAME |OWNERSHIP |TYPE |STATUS |ZONE |DISTRICT |DATE OPENED |LATITUDE |LONGITUDE
|:--- |:--- |:--- |:--- |:--- |:--- |:--- |:--- |:--- |:--- |:--- |
|LL040007 |African Bible College Community Hospital	|ABC Clinic	|Christian Health Association of Malawi (CHAM)	|Hospital	|Functional	|Centrals West Zone	|Lilongwe	|Jan 1st 75	|-13.96816	|33.74129 |

#### Flexible source - healthsites.io via HDX
The data landscape for health facility datasets varies from country to country. In many cases, a publicly available register maintained by the relevant authorities, such as a Ministry of Health, is likely to provide the most reliable source.

In an effort to create a generalised tool, we identified data from [Healthsites.io](https://healthsites.io/) [2] as a reasonable source to experiment with initially. It was selected because it is open and easy to use, with data available for many countries and publicly downloadable from the [Humanitarian Data Exchange (HDX)](https://data.humdata.org/) platform [9].

Healthsites is suggested as a flexible starting point for contexts where a reliable official register is not openly available, with validation against country-owned sources where possible. Published evidence suggests Healthsites has reasonable coverage in several settings, although this assessment is based on facility counts and may not fully capture data completeness or quality.[10]

### Population estimates
#### WorldPop population and demographic estimates
Open source population estimates for different countries are available from [WorldPop](https://www.worldpop.org/) [3]. This workflow uses WorldPop's constrained age-sex structures at 1 km resolution, which allocate population to likely settlement locations rather than distributing estimates across all land cells. This approach is particularly suitable for accessibility analysis because it reduces the likelihood of assigning population to uninhabited areas where facility access is irrelevant. The age-sex demographic subsets enable disaggregation of accessibility estimates by population group (for example, children, working-age adults, women of reproductive age), which supports more nuanced health service planning.

#### Constrained population grids
Constrained population grids are built using building footprints and settlement layers to refine distribution models.[11] While this improves spatial realism compared to unconstrained products, the method remains subject to uncertainties in the underlying settlement data, settlement classification, and census source data (see [Limitations and Caveats](#limitations-and-caveats) below). The datasets are provided as raster files in `.tif` format for different years and are available for download from [WorldPop](https://data.worldpop.org/) [3]. The total number of people per grid cell is an estimate and caution is advised when interpreting results at fine spatial scales.

#### Assigning population cells to administrative areas
To support subnational summaries, each 1 km population grid cell is assigned to a single administrative area. Where a grid cell straddles the border between two or more administrative areas, it is assigned to the area with the largest overlap of the grid-cell area.

This approach avoids double counting, but introduces a boundary caveat: cells near administrative borders may be attributed to a neighbouring area even where population is distributed across both sides of the boundary. This is most relevant for small administrative units and irregular boundaries.

In the R workflow, an alternative raster-based assignment method is also available. This approach assigns each point to an administrative area using the district value at the point's grid-cell centroid location, rather than resolving overlap by area. It is a faster approach and is included for testing and comparison purposes, but is not the preferred method for production outputs.

### Road network
[OpenStreetMap](https://www.openstreetmap.org/about) (OSM) [4] provide network data for calculating travel time distances between healthcare facilities.

The completeness of the OpenStreetMap network was measured by comparing its district level coverage against Microsoft's [RoadDetections](https://github.com/microsoft/RoadDetections) data [12]. This is open data of the world's roads detected using machine learning of Bing Maps satellite imagery. The ratio between the overall length of the Microsoft RoadDetections network already mapped by OSM and the total length of the MS network gives an indication of OSM completeness. A high ratio indicates that there are few missing OSM roads detected by the MS machine learning model. Since the processing was computationally intensive only a few districts were assessed. For example, in Phalombe district, 94.9% of the MS network has already been mapped by OSM.</br>

</br>OSM road network data are available from [download.geofabrik.de](https://download.geofabrik.de/) [5] in [`.osm.pbf`](https://wiki.openstreetmap.org/wiki/PBF_Format) format [6].

### Administrative boundaries
Digital vector boundaries for subnational administrative areas enable accessibility measures to be quantified across different areas. Malawi for example is divided into three regions and subdivided into 28 districts. In the R based workflow these are derived from OpenStreetMap [7], whereas the python workflow uses those sourced from [geoBoundaries](https://www.geoboundaries.org/countryDownloads.html) [8]. Both sources vary in quality in different local contexts, users are recommended to conduct their own investigation of quality and alternatively identify and use official sources where possible. 

## What we do to it 

The pipeline for calculating the accessibility of healthcare facilities is broadly similar for both R and Python.

### Processing 

#### Healthcare facilities
The generalised workflow requires a `CSV` or `GeoJSON` file containing the healthcare facility data with an `id` column containing the name of the healthcare facility and accompanying `lon`/`lat` coordinates in the WGS84 coordinate system. The data is assumed to be cleaned and pre-processed before running the workflow.

In the Malawi use case missing values were removed and facilities with coordinates outside of Malawi were discarded. Only facilities that were recorded as 'FUNCTIONAL' were retained. The results were stored as a `CSV` file with an `id` column containing the name of the healthcare facility and accompanying `lon`/`lat` coordinates in the WGS84 coordinate system. Cleaning of this nature should be completed before running the workflow to ensure that the workflow accepts the data and the data are of sufficient quality to produce meaningful estimates.

#### Population estimates
Gridded population estimates are cropped to the Malawi boundary and rasters combined for specific population subsets:

- Females
- Males
- Children (0-14 years) 
- Working-age adults (15-64 years)
- Older people (65+ years)
- Women of reproductive age (15-49 years)

The resulting raster layers are vectorised to points with a unique `id` column, `lon`/`lat` coordinate pairs, and a `population` count.

#### Road network 
The OSM road network needs to be converted into a multimodal transport network before travel times can be calculated. Using the R [`r5r`](https://ipeagit.github.io/r5r/) [13] and Python [`r5py`](https://r5py.readthedocs.io/stable/) [14] packages to interface with [R⁵](https://github.com/conveyal/r5) [15] (Rapid Realistic Routing on Real-world and Reimagined networks) we can build a routable network object.

### Calculating travel times 
#### Travel time matrices
To calculate travel time estimates between origin (healthcare facilities) and destinations (population grids) pairs the [`r5r::travel_time_matrix()`](https://ipeagit.github.io/r5r/reference/travel_time_matrix.html) R function [16] and [`r5py.TravelTimeMatrix`](https://r5py.readthedocs.io/stable/reference/reference.html#r5py.TravelTimeMatrix) Python class are used [14]. The origin/destination pairs need to contain `id`, `lon`, and `lat` columns.

Travel times are based on network distance rather than 'as the crow flies' because they better represent accessibility in a physical environment constrained by roads and buildings.

#### Travel mode and max time
There are a number of possible inputs including travel *mode* (e.g. WALK, BICYCLE, CAR) and the *max time* and *max trip duration*. We have used *BICYCLE* as the travel mode because it applies less permissive routing than *WALK*, helping to better represent distances along commonly used road links, although the tool can be adapted to use other modes depending on the context.

#### Level of Traffic Stress (LTS) for bicycle routing
For *BICYCLE* mode, the parameter `max_lts` in `r5r::travel_time_matrix()` and `r5py.TravelTimeMatrix` controls the maximum Level of Traffic Stress accepted in bicycle routing [16]. It is set in code to `4` by default (r5r's own default is `2`).
LTS values are inferred from OSM tags such as speed limits, lane counts, and cycleway tags. Roads without these tags fall to LTS 4 by default. In settings where OSM data is sparsely tagged, common in many low- and middle-income country contexts, using `max_lts = 2` can exclude navigable roads due to missing data rather than genuine stress. Using `4` avoids this, at the cost of not distinguishing road stress levels. It is a pragmatic default for data-sparse settings and should be considered depending on the level of local data quality. See [Conway (2015)](https://medium.com/conveyal-blog/better-measures-of-bike-accessibility-d875ae5ed831) [17] for more information on LTS.
For more details on `max_lts`, see the [r5r documentation](https://ipeagit.github.io/r5r/reference/travel_time_matrix.html#level-of-traffic-stress-lts-) [16].
If you need a different `max_lts` value, update the call in `src/r/dashboard/R/compute_closest_accessibility.R` and re-run `02_ttm.R`.

### Deriving distance
The `r5r` and `r5py` packages calculate travel times rather than distance by default. The `r5r::travel_time_matrix()` function has a [`max_walk_time`](https://ipeagit.github.io/r5r/reference/travel_time_matrix.html#arg-max-walk-time) argument [16] which is the maximum walking *time* for direct trips in all routing functions but no [`max_walk_dist`](https://ipeagit.github.io/r5r/news/index.html#r5r-100) parameter [18]. To derive distance from the *max time* we used:

</br>$t = \frac{d}{v}$

where $t$ is time, $d$ is distance, and $v$ is velocity or speed.

Bicycle speed defaults to 12km/h in R⁵ so we can calculate the time it takes to cover 8km as:

$t$ = 8000/3600

which converted into minutes is **40**.

### Joining with population data 
The resulting travel time matrix contains a `from_id` column which refers to the destination and `to_id` the destination. The `travel_time_p50` (`travel_time` in the python workflow) column provides the travel time estimate between each origin/destination pair.

**Example travel time matrix**   

|from_id |to_id |travel_time_p50 |
|:--- |:--- |:--- |
|244357263 |40677 |133 |
|244357263 |40678 |125 |
|244357263 |40680 |133 |
|244357263 |40899 |128 |
|244357263 |40900 |127 |

The matrices are summarised so that the shortest time between origin and destination pairs are retained. To match the travel time estimates to the gridded population data we then use the `to_id` and `id` columns as joining variables. 

### Aggregating to get quantitative outputs
To summarise population estimates by say a 8km distance band, we can simply use a 40 minute threshold. Gridded populations that are not accessible within 40 minutes are marked as being beyond reach of a healthcare facility.


# Limitations and Caveats

- **Healthcare facility dataset quality:** The timeliness and completeness of healthcare facility datasets used in this analysis are difficult to verify. For example, in Malawi we have been informed that the Malawi Health Facility Registry (MHFR) is outdated, and that a more recent version is under development but not yet publicly available (as of April 2026). Missing facilities, as well as the inclusion of facilities that have permanently closed, can substantially affect the derived accessibility metrics for local area. In addition, the data does not indicate the capacity of a healthcare facility, nor the services that may or may not be provided.

- **OpenStreetMap's (OSM) variable quality:** OpenStreetMap relies on volunteer contributors to create and maintain geographic data. Consequently, data quality varies by location and depends on the level of local contributor activity. This variability affects the detail, completeness, and timeliness of the data. This may include details about road conditions and accessibility, which r5 uses for its travel time estimations. OSM is generally less reliable in low-density rural areas and in low‑resource settings - contexts that are also more likely to experience gaps in healthcare access.

- **Travel distances are approximate derivations:** Travel distances are not measured directly along the road network; instead, they are derived from estimated travel times. Sensitivity testing showed that distances derived from cycling-based travel times (which assume a fixed average speed) are systematically higher than those derived from walking-based travel times, with a median difference of 2.1 km (interquartile range: 0.34–4.56 km). This difference likely reflects route permissibility: walking routes are less restrictive and may include footpaths or stairs that are not accessible to bicycles or vehicles. As cycling routes more closely approximate permissible vehicular routes, cycling-based distances are used in this analysis.
  
- **Maximum travel time limitations:** When conducting travel time analysis, a maximum travel time threshold must be specified. Any origin-destination pairs with travel times exceeding this threshold are excluded from subsequent analysis. This directly affects the maximum travel distance that can be assessed. For example, if a user defines accessibility as being within 20 km, a maximum travel time that only corresponds to approximately 10 km would exclude relevant journeys and lead to misleading results. The detailed workflow documentation provides guidance on selecting an appropriate maximum travel time to avoid this issue.

- **Population estimates:** The WorldPop gridded population estimates used in this analysis are subject to several sources of uncertainty:
  - Population surfaces are created by disaggregating known population counts from administrative areas using modeled weighting surfaces. However, for individual countries it is often unclear which population source was used and at what administrative level. These sources are typically national census data (from the 2010 or 2020 census rounds), but may also include U.S. Census Bureau subnational projections or United Nations Common Operational Datasets (CODs). Uncertainty is lower when disaggregation is performed from smaller administrative units.
  - The disaggregation models rely on globally available geospatial covariates selected for their broad applicability. While this enables consistent global application, it prevents the use of country-specific datasets that could potentially improve local accuracy.
  - Independent research conducted by the Office for National Statistics (ONS) applying this methodology in the UK found a tendency to overestimate population density in low‑density areas and underestimate population density in high‑density areas.
  - Age and sex distributions are adjusted during the demographic modelling stage to align with the UN’s 2024 Revision of World Population Prospects. Consequently, the accuracy of these demographic estimates depends on the reliability of the UN projections.
  - Further details on the underlying methodology and associated caveats are available in the accompanying [technical documentation](https://data.worldpop.org/repo/prj/Global_2015_2030/R2025A/doc/Global2_Release_Statement_R2025A_v1.pdf) [19].
 
- **Water bodies:** The travel time analysis only considers crossings of water bodies via bridges on the road network. Alternative crossing methods, such as ferries, are not included. This can lead to accessibility being underestimated for locations near rivers, estuaries, or islands, where such crossings are available in reality but are not represented in the model.

# References

1. Malawi Ministry of Health. Malawi Master Health Facility Register [Internet]. [cited 2026 Aug 6]. Available from: https://zipatala.health.gov.mw/facilities

2. Healthsites.io. Healthsites [Internet]. [cited 2026 Aug 6]. Available from: https://healthsites.io/

3. WorldPop. WorldPop data portal [Internet]. [cited 2026 Aug 6]. Available from: https://data.worldpop.org/

4. OpenStreetMap Foundation. OpenStreetMap [Internet]. [cited 2026 Aug 6]. Available from: https://www.openstreetmap.org/about

5. Geofabrik GmbH. Geofabrik download server [Internet]. [cited 2026 Aug 6]. Available from: https://download.geofabrik.de/

6. OpenStreetMap Wiki contributors. PBF Format [Internet]. [cited 2026 Aug 6]. Available from: https://wiki.openstreetmap.org/wiki/PBF_Format

7. Overpass Turbo. Overpass Turbo query interface [Internet]. [cited 2026 Aug 6]. Available from: https://overpass-turbo.eu/s/2mPz

8. Williams C, Trabucco A, Maisels M, et al. geoBoundaries: A global database of political administrative boundaries [Internet]. [cited 2026 Aug 6]. Available from: https://www.geoboundaries.org/countryDownloads.html

9. UN OCHA. Humanitarian Data Exchange (HDX) [Internet]. [cited 2026 Aug 6]. Available from: https://data.humdata.org/

10. Wellcome Open Research. Article 5-157 version 2 [Internet]. London: Wellcome Open Research; [cited 2026 Aug 6]. Available from: https://wellcomeopenresearch.org/articles/5-157/v2

11. WorldPop. Peandy T, Tatem AJ. WorldPop building maps dataset [Internet]. Southampton: University of Southampton; 2024. Available from: https://www.worldpop.org/

12. Microsoft. RoadDetections [Internet]. GitHub repository; [cited 2026 Aug 6]. Available from: https://github.com/microsoft/RoadDetections

13. Pereira RHM, Saraiva M, Herszenhut D, Braga CKV, Conway MW. r5r: Rapid Realistic Routing on Multimodal Transport Networks with R⁵ in R [Internet]. [cited 2026 Aug 6]. Available from: https://ipeagit.github.io/r5r/

14. r5py developers. r5py documentation [Internet]. [cited 2026 Aug 6]. Available from: https://r5py.readthedocs.io/stable/

15. Conway MW, Byrd A, van der Linden S. R⁵ (Rapid Realistic Routing on Real-world and Reimagined networks) [Internet]. GitHub repository; [cited 2026 Aug 6]. Available from: https://github.com/conveyal/r5

16. r5r developers. travel_time_matrix reference [Internet]. [cited 2026 Aug 6]. Available from: https://ipeagit.github.io/r5r/reference/travel_time_matrix.html

17. Conway MW. Better measures of bike accessibility [Internet]. Medium; [cited 2026 Aug 6]. Available from: https://medium.com/conveyal-blog/better-measures-of-bike-accessibility-d875ae5ed831

18. r5r developers. r5r changelog and news [Internet]. [cited 2026 Aug 6]. Available from: https://ipeagit.github.io/r5r/news/index.html#r5r-100

19. WorldPop. Global 2015-2030 unconstrained/constrained release statement R2025A v1 [Internet]. [cited 2026 Aug 6]. Available from: https://data.worldpop.org/repo/prj/Global_2015_2030/R2025A/doc/Global2_Release_Statement_R2025A_v1.pdf
