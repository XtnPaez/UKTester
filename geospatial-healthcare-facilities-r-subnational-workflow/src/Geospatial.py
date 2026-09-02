"""This script covers exploration of HCF datasets and cleaning them for further analysis"""

# %%
import yaml
import pandas as pd
import geopandas as gpd
from pathlib import Path
from decimal import Decimal

import healthcare_accessibility.geospatial_utils as geo_util

# %%
config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

analysis_crs = config.get("analysis_crs")

visualisation_crs = config.get("visualisation_crs")

# %%
# using the joined data between figshare and hml
fig_dir = config.get("data_dir") + datasets.get("health_facility").get("figshare_hml")
df = gpd.read_file(fig_dir)
df.head()

# %%
df.isnull().sum()

# %%
df.info()

# %%
# converting long and lat
df["Lat"] = df["Lat"].apply(Decimal)
df["Long"] = df["Long"].apply(Decimal)

# %%
geo_df = geo_util.convert_to_georeferenced(df, "Lat", "Long", analysis_crs)

# %%
geo_df.plot()

# %%
region_path = config.get("data_dir") + datasets.get("admin_boundary").get(
    "geoboundaries_ADM1"
)
district_path = config.get("data_dir") + datasets.get("admin_boundary").get(
    "geoboundaries_ADM2"
)

# %%
adm1 = gpd.read_file(region_path)
adm2 = gpd.read_file(district_path)

# %%
# renaming for better understanding
adm1.rename(columns={"shapeName": "Region"}, inplace=True)
adm2.rename(columns={"shapeName": "District"}, inplace=True)

# %%
mp = geo_util.plot_map(
    geo_df, adm1, adm2, "Lat", "Long", "Facility name", visualisation_crs
)
mp

# %%
region_map, district_map = geo_util.get_maps(
    adm1, adm2, "Region", "District", "geometry"
)

# %% [markdown]
# ##### Testing if all regions are correct


# %%
# testing
def get_region2(x, y):
    """
    This checks if a facility is in any of the regions and that it matches the region that came with the dataset.

    Parameters:
        x (Geomerty Points) : Geometry coordinates of the facilities in Point form
        y (str) : The region that originally came with the dataset

    Returns:
        bool
    """
    for reg, reg_poly in region_map.items():
        if reg_poly.contains(x) and reg == y:
            return True
    return False


# %%
geo_df["reg_check"] = geo_df.apply(
    lambda x: get_region2(x.geometry, x.Region_x), axis=1
)
geo_df["reg_check"].value_counts()

# %%
geo_df[geo_df["reg_check"] == False]

# %%
# comparing with geo location in baobab
baobab_dir = config.get("data_dir") + datasets.get("health_facility").get("baobab")

baobab_df = geo_util.clean_datasets(baobab_dir, "baobab")

# %%
# checking if the two that failed are right in baobab

sub = baobab_df[
    baobab_df["Facility name"].isin(["Kasasa Clinic", "Mkomaula Health Centre"])
]
subgeo = geo_util.convert_to_georeferenced(sub, "latitude", "longitude", analysis_crs)

print(
    region_map["Central"].contains(subgeo.loc[347]["geometry"]),
    region_map["Southern"].contains(subgeo.loc[1252]["geometry"]),
)

# %% [markdown]
# ##### Testing if all districts are correct


# %%
# testing for districts
def get_district2(x, y):
    """
    This checks if a facility is in any of the districts and that it matches the district that came with the dataset.

    Parameters:
        x (Geomerty Points) : Geometry coordinates of the facilities in Point form
        y (str) : The district that originally came with the dataset

    Returns:
        bool
    """
    for dis, dis_poly in district_map.items():
        if dis_poly.contains(x) and dis == y:
            return True
    return False


# %%
geo_df["dis_check"] = geo_df.apply(
    lambda x: get_district2(x.geometry, x.District), axis=1
)
geo_df["dis_check"].value_counts()

# %%
# facilities that did not match
fac = geo_df[geo_df["dis_check"] == False]["Facility name"].tolist()

# %%
dis_check = baobab_df[baobab_df["Facility name"].isin(fac)]
check_df = geo_util.convert_to_georeferenced(
    dis_check, "latitude", "longitude", analysis_crs
)

# %%
check_df["dis_check"] = check_df.apply(
    lambda x: get_district2(x.geometry, x.District), axis=1
)
check_df["dis_check"].value_counts()

# %% [markdown]
# Out of the 25 that did not match for district in the figshare data, 22 of those are in baobab and 20 out of them matched. With this it seems the location from baobab is more accurate than the ones from figshare.

# %%
check_df[check_df["dis_check"] == False]

# %% [markdown]
# ### Using the current way to determine districts and region for baobab

# %%
geo_bao = geo_util.convert_to_georeferenced(
    baobab_df, "latitude", "longitude", analysis_crs
)
geo_bao.head(3)

# %%
geo_bao.isnull().sum()

# %%
## getting the list of facilities with no location to check if elsewhere and removing them from main data

bao_noloc = geo_bao[geo_bao["latitude"].isna()]
bao_noloc.head(2)

geo_bao = geo_bao.loc[geo_bao["longitude"].notnull()]

# %%
geo_bao["derived_region"] = geo_bao.apply(
    lambda x: geo_util.get_region(x.geometry, region_map), axis=1
)
geo_bao["derived_district"] = geo_bao.apply(
    lambda x: geo_util.get_district(x.geometry, district_map), axis=1
)

# %%
geo_bao.isnull().sum()

# %% [markdown]
# This shows that some of the geolocations do not fall in any of the bounded regions we have. 1 for region and 6 for districts

# %%
geo_bao[geo_bao["derived_region"].isna()]

# %%
geo_bao[geo_bao["derived_district"].isna()]

# %%
# visualising where these are on the map
geo_util.plot_map(
    geo_bao[geo_bao["derived_district"].isna()],
    adm1,
    adm2,
    "latitude",
    "longitude",
    "Facility name",
    visualisation_crs,
)

# %% [markdown]
# From the visualisation, the original districts are correct and even the locations fall within those districts but they are majorly on the edge and slighty outside the boundary we have for the districts. It is the same for the region that returned null. Zooming in further it shows that the administrative boundary layers a little shifted on the map. They are not a perfect fit. Also, removing the administrative layers shows that their might be issues with resolution of the boundary coordinates we have, which has caused the issues above.

# %%
# comparing both columns
geo_bao["District"].equals(geo_bao["derived_district"])

# %%
geo_bao = geo_bao.loc[geo_bao["derived_district"].notnull()]
no_match = geo_bao.query("District != derived_district")
no_match

# %%
geo_util.plot_map(
    no_match, adm1, adm2, "latitude", "longitude", "Facility name", visualisation_crs
)

# %%
no_match[["Facility name", "District", "derived_district"]]

# %%
no_match.shape

# %%
geodf_copy = geo_df.copy()

# %%
for g in geodf_copy["Facility name"].tolist():
    if g.startswith("Suco"):
        print(g)

# %%
# checking if they are in fig_hml
geodf_copy[geodf_copy["Facility name"].isin(no_match["Facility name"].tolist())]

# %% [markdown]
# From the internet:
# 'Lupachi': Nkhotakota : in Mzimba on plot
#  "Towoo's Private Clinic" : can't find : in lilongwe on plot
#  'Kaputalambwe' : Dowa : in lilongwe on plot
#  'Kapire Dream Centre': Magnochi
#  'Kapire Health Centre' : Phalombe
#  'Liwonde Medical Clinic': Machinga
#  'Mota-Engil 301 Clinic': can't find
#  'Magunda Health Centre': Rumphi
#  'Mbalanguzi': Thyolo
#  'Gotha Estate Clinic': Phalombe
#  'Mulungu Alinafe Clinic': Rumphi
#  'Sucoma/Mwanza/Illovo Clinic': Mwanza
#  'Mota-Engil Clinic - Mkwinda Ca': Not sure (Mwinda/Neno)

# %%
district_map["Nkhotakota"].contains(no_match.loc[348]["geometry"])

# %% [markdown]
#

# %% [markdown]
# ### Combining Figshare, Elizabeth and baobab

# %%
figshare_dir = config.get("data_dir") + datasets.get("health_facility").get("figshare")
figshare_df = geo_util.clean_datasets(figshare_dir, "figshare")
figshare_df.head(2)

# %%
baobab_df.head(2)

# %%
eliz_dir = config.get("data_dir") + datasets.get("health_facility").get("eliz_data")
eliz_df = geo_util.clean_datasets(eliz_dir, "eliz")
eliz_df.head(2)

# %%
join_df = pd.concat([baobab_df, eliz_df, figshare_df], ignore_index=True)
join_df.drop(["#"], axis=1, inplace=True)
join_df

# %%
join_df.isnull().sum()

# %%
# dropping the facilities with no geolocations
join_df.dropna(axis=0, subset=["longitude", "latitude"], inplace=True)

# %%
join_df["Facility name"].groupby(join_df["Facility name"]).filter(
    lambda x: len(x) > 1
).value_counts().sort_values()

# %%
join_geo = geo_util.convert_to_georeferenced(
    join_df, "latitude", "longitude", analysis_crs
)

# %%
# using the geolocations to determine where the facilities fall
join_geo["derived_region"] = join_geo.apply(
    lambda x: geo_util.get_region(x.geometry, region_map), axis=1
)
join_geo["derived_district"] = join_geo.apply(
    lambda x: geo_util.get_district(x.geometry, district_map), axis=1
)

# %%
# filling nulls in type, ownership and location with filled values from duplicate
cols_to_fill = ["Facility type", "Facility ownership", "Facility Location"]

for cols in cols_to_fill:
    mask = join_geo[cols].isna()
    filled_col = join_geo.groupby("Facility name")[cols].transform(
        lambda x: x.ffill().bfill()
    )
    join_geo.loc[mask & join_geo[cols].isna(), cols] = filled_col[
        mask & join_geo[cols].isna()
    ]

# %%
join_geo.shape

# %%
# dropping the duplicates with the same name and location
join_geo.drop_duplicates(
    subset=["Facility name", "longitude", "latitude"], keep="first", inplace=True
)

# %%
# checking for duplicates
duplicates_df = join_geo[
    join_geo.duplicated(subset=["Facility name"], keep=False)
].sort_values("Facility name")
duplicates_df.shape

# %%
# saving duplicates for further evaluation
duplicates_df.to_csv(config.get("data_dir") + "duplicates.csv")

# %%
# Working to get the ids of all duplicates that need to be dropped based on different requirements

# %%
# # null counts per row (gives priority to baobab and eliz)
# duplicates_df['null_count'] = duplicates_df.isnull().sum(axis=1)

# # filtering for rows where the derived and original districts do not and neither is null
# drop_condition = (duplicates_df['District'].notnull() \
#                   & duplicates_df['derived_district'].notnull() \
#                   & (duplicates_df['District'] != duplicates_df['derived_district']) \
#                   & (duplicates_df['null_count'] > 1))

# to_drop = (duplicates_df[drop_condition].sort_values(['Facility name', 'null_count'], ascending=[True, True])\
#            .groupby('Facility name').head(1))
# to_drop

# duplicates_clean = duplicates_df.drop(index=to_drop.index)

# %%
left = duplicates_clean.sort_values("null_count").drop_duplicates(
    subset="Facility name", keep="first"
)
left

# %%
# get indexes of dropped duplicates
diff_index = duplicates_df.index.difference(left.index)
diff_index

# %%
# dropping all duplicates from main data
joinclean_geo = join_geo.drop(index=diff_index)

# %%
join_geo.shape, joinclean_geo.shape

# %%
# confirming if all identical name duplicates have been removed

joinclean_geo["Facility name"].value_counts()

# %%
join_geo["matched_name"] = join_geo["Facility name"].apply(
    lambda x: geo_util.fuzz_match(x, join_geo["Facility name"])
)

# %%
join_geo[join_geo["Facility name"] != join_geo["matched_name"]][
    ["Facility name", "matched_name"]
][:50]

# %%
join_geo[join_geo["Facility name"] != join_geo["matched_name"]][
    ["Facility name", "matched_name"]
][51:]

# %%
# null counts per row
join_geo["null_count"] = join_geo.isnull().sum(axis=1)

# %%
join_geo

# %%
# to further filter the match

# setting index for easy lookup
drop_idxs = set()
dup_within = set()


for index, row in join_geo.iterrows():

    if row["Facility name"] != row["matched_name"]:

        similar = join_geo[join_geo["Facility name"] == row["matched_name"]]
        similar_idx = similar.index

        if len(similar) > 1:
            similar_idx = (
                similar.sort_values("null_count")
                .drop_duplicates(subset="Facility name", keep="first")
                .index
            )
            for i in similar.index.difference(similar_idx).tolist():
                drop_idxs.add(i)

            # drop_idxs.add(similar.index)
        # confirm they're in the same district
        matched_series = join_geo.loc[similar_idx]
        matched_district = matched_series["District"].item()

        if (
            pd.isnull(row["District"])
            or pd.isnull(matched_district)
            or row["District"] == matched_district
        ):
            # selecting indexes with max null values
            if row["null_count"] < matched_series["null_count"].item():
                drop_idxs.add(index)
            elif row["null_count"] > matched_series["null_count"].item():
                drop_idxs.add(similar_idx.item())
            else:
                drop_idxs.add(similar_idx.item())

            print(row["Facility name"], row["matched_name"])

# %%
# dropping one of the matched ones
joinclean_geo = join_geo.drop(drop_idxs)

# %%
# re checking the match
joinclean_geo["matched_name"] = joinclean_geo["Facility name"].apply(
    lambda x: geo_util.fuzz_match(x, joinclean_geo["Facility name"])
)

# %%
joinclean_geo[joinclean_geo["Facility name"] != joinclean_geo["matched_name"]][
    ["Facility name", "matched_name"]
]

# %%
# The above gives the similar hospitals left
joinclean_geo[
    joinclean_geo["Facility name"].isin(
        [
            "Sucoma Clinic Illovo",
            "Sucoma Illovo Factory Clinic",
            "Mvera Mission Health Centre",
            "Mvera Health Centre",
            "Mua Hospital",
            "Mua Mission Hospital",
            "Nkhamenya Community Hospital",
            "Nkhamenya Hospital",
        ]
    )
]

# %%
drop_idxs = [2374, 2047, 2140, 2376]
# dropping one of the matched ones
joinclean_geo = joinclean_geo.drop(drop_idxs)

# %%
# drop unwanted columns
joinclean_geo.drop(columns=["null_count", "matched_name"], axis=1, inplace=True)

# %%
# saving currently combined data
joinclean_geo.to_csv(config.get("data_dir") + "Combined_data.csv", index=False)
