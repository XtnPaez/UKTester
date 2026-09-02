"""Script for retrieval of admin boundaries from OSM"""

# %%
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import yaml
from pathlib import Path
import requests

import healthcare_accessibility.geospatial_utils as geo_util
import healthcare_accessibility.osm_utils as osm_util


# %%
# Enable certificate verification explicitly
session = requests.Session()
session.verify = True

# Pass the session to osmnx
ox.settings.requests_kwargs = {"verify": True}

# %%
# Set path to data folder
config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

visualisation_crs = config.get("visualisation_crs")

data_dir = Path(config.get("data_dir"))

output_dir = Path(config.get("outputs_dir"))

# %% [markdown]
# Admin boundaries - districts

# %%
# List of values to filter by
district_list = [
    "Kasungu",
    "Lilongwe",
    "Blantyre",
    "Zomba",
    "Chiradzulu",
    "Nkhotakota",
    "Machinga",
    "Mchinji",
    "Chikwawa",
    "Thyolo",
    "Balaka",
    "Likoma",
    "Salima",
    "Ntchisi",
    "Karonga",
    "Mzimba",
    "Mulanje",
    "Nkhata Bay",
    "Chitipa",
    "Dedza",
    "Ntcheu",
    "Mangochi",
    "Dowa",
    "Rumphi",
    "Nsanje",
    "Neno",
    "Phalombe",
    "Mwanza",
]

# %%
district_boundaries = osm_util.get_osm_admin_boundaries(
    country="Malawi", admin_level="2", boundary_area_list=district_list
)

# %%
# Create the plot
fig, ax = plt.subplots(figsize=(35, 10))

# Plot the districts
district_boundaries.plot(
    ax=ax,
    column="name",
    cmap="Set3",
    edgecolor="black",
    linewidth=0.5,
    legend=True,
    legend_kwds={
        "loc": "lower center",
        "bbox_to_anchor": (0.5, -0.30),
        "ncol": 4,  # Number of columns in the legend
        "title": "Districts",
    },
)

# Add title and labels
ax.set_title("Malawi District Boundaries", fontsize=16)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

# Remove axis ticks
ax.set_xticks([])
ax.set_yticks([])

plt.tight_layout
plt.show()

# %%
# Save to data directory
district_boundaries.to_file(data_dir / "OpenStreetMap_ADM2.gpkg", driver="GPKG")

# %%
# List of authorities in Malawi
authority_list = [
    "Chinde",
    "Chikulamayembe",
    "Mlolo",
    "Musisya",
    "Katuli",
    "Nankumba",
    "Ngozi",
    "Dzoole",
    "Nchema",
    "Timbiri",
    "Malenga Chanzi",
    "Tengani",
    "Ngabu",
    "Mkhumba",
    "Symon",
    "Mtwalo Ii",
    "Kawinga",
    "Chimombo",
    "Kalembo",
    "Zomba",
    "Likoma",
    "Jalasi",
    "Kabudula",
    "Njolomole",
    "Mkanda",
    "Kaomba",
    "Chiwere",
    "Muchinjili",
    "Nyachikadza",
    "Makata",
    "Changata",
    "Msakambewa",
    "Massea",
    "Pemba",
    "Fukamapiri",
    "Khombedza",
    "Mambeya",
    "Tambala",
    "Karonga",
    "Kunthembwe",
    "Nsabwe",
    "Katunga",
    "Mpando",
    "Chitukula",
    "Kanduku",
    "Chigaru",
    "Mwabulambya",
    "Mwadzama",
    "Lake Chilwa",
    "Kyungu",
    "Mlauli",
    "Chimaliro",
    "Mankambira",
    "Lake Malombe",
    "Kaluluma",
    "Kuntumanji",
    "Ndamera",
    "Bibi Kaluunda",
    "Kasumbu",
    "Nkanda",
    "Kapeni",
    "Kalumo",
    "Kuntaja",
    "Malemia",
    "Malenga Mzoma",
    "Chiseka",
    "Likoswe",
    "Bvumbwe",
    "Mwambo",
    "Kilupula",
    "Mpherembe",
    "Katumbi",
    "Nazombe",
    "Mzikubola",
    "Mwamlowe",
    "Mabulabo",
    "Makanjira",
    "Malili",
    "Mazengera",
    "Kabunduli",
    "Mponda",
    "Nthalire",
    "Zulu",
    "Chimutu",
    "Nkalo",
    "Chitera",
    "Liwonde",
    "Blantyre City",
    "Lake Chiuta",
    "Chulu",
    "Mwenemisuku",
    "Maganga",
    "M'Mbelwa",
    "Lundu",
    "Mwenewenya",
    "Chikowi",
    "Kwataine",
    "Chadza",
    "Phambala",
    "Kaphuka",
    "Ngamwane",
    "Kanyenda",
    "Kachindamoto",
    "Mlumbe",
    "Somba",
    "Mzukuzuku",
    "Makhwira",
    "Santhe",
    "Mlonyeni",
    "Kandewere",
    "Kameme",
    "Njewa",
    "Nchilamwela",
    "Kasisi",
    "Chapananga",
    "Dambe",
    "Wasambo",
    "Masasa",
    "Boghoyo",
    "Ntache",
    "Thomas",
    "Mpama",
    "Kapelula",
    "Msamala",
]

# %%
authority_boundaries = osm_util.get_osm_admin_boundaries(
    country="Malawi", admin_level="8", boundary_area_list=authority_list
)

# %%
# Check if authority is in gdf
for auth in authority_list:
    if auth not in authority_boundaries["name"].values:
        print(auth)

# %% [markdown]
# Roads with admin boundaries

# %%

# NOTE: Has dependency on a data file generated elsewhere in the project

# Load dataframe
gdf = gpd.read_file(
    config.get("data_dir") + datasets.get("health_facility").get("cleaned_hcf"),
)

# %%
district_gdf, district_roads, facility_network, *_ = (
    osm_util.osm_district_and_road_network(
        country="Malawi",
        district_name="Kasungu",
        healthcare_facility="Chulu Health Centre",
        distance=1500,
        gdf=gdf,
        network_type="walk",
    )
)
