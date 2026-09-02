## Malawi healthcare accessibility

### User interface

This [R Shiny](https://shiny.posit.co/) application enables the user to identify estimated populations that reside beyond 5, 8, and 10km distance of a health facility. The dropdown menus allow users to select individual subnational areas or the whole of the country. Healthcare facilities can be selected by type, for example: hospital, clinic, dispensary, private and unclassified. It also possible to choose estimated populations by subgroup:

- Females
- Males
- Children (0-14)
- Working-age adults (15-64)
- Older people (65+)
- Women of reproductive age (15-49)

Finally users can toggle between estimated populations that live *within* and *outside* the chosen distance of a healthcare facility.

The map will automatically zoom to the area of interest and update summary statistics in the right panel.

### Datasets

The following datasets were used in the application:

|Name |Source |URL |Type |Licence |
|:-----|:-----|:-----|:-----|:-----|
|Administrative boundaries |[OpenStreetMap (OSM)](ttps://wiki.openstreetmap.org/wiki/Overpass_API) |[Link](https://overpass-api.de/) |`.GeoJSON`  |[ODbL](https://opendatacommons.org/licenses/odbl/) |
|Healthcare facilities |[healthsites.io](https://healthsites.io/) | [Link](https://data.humdata.org/dataset) |`.csv` |[Open Database License](https://opendatacommons.org/licenses/odbl/) |
|Population estimates |[WorldPop](https://www.worldpop.org/) | [Link](https://www.worldpop.org/datacatalog/) |`.tif` |[Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0) |
|Road network |[OpenStreetMap (OSM)](ttps://wiki.openstreetmap.org/wiki/Overpass_API) | [Link](https://overpass-api.de/) |`.pbf` |[ODbL](https://opendatacommons.org/licenses/odbl/) |

### Method

A distance matrix was derived from a travel time matrix calculated using the [`r5r`](https://ipeagit.github.io/r5r/) R package which interfaces with [R<sup>5</sup>](https://github.com/conveyal/r5) routing engine. The shortest distances between origin (healthcare facilities) and destination (gridded population estimates) pairs were identified and visualised in the application. Full details of the methodology can be found in the accompanying GitHub repo.