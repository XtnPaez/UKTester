# %%
import os
import yaml
import pyproj
import geopandas as gpd
from pathlib import Path
import geopandas as gpd
from shapely.ops import unary_union
from scipy.spatial import distance_matrix
import healthcare_accessibility.geospatial_utils as geo_util

# %%
# parse explicit path to projection database to avoid errors
pyproj.datadir.set_data_dir(os.environ["PROJ_DATA"])

config_filepath = Path().cwd().joinpath("configs", "config.yaml")

with open(config_filepath) as file:
    config = yaml.safe_load(file)

with open(config.get("datasets_config")) as file:
    datasets = yaml.safe_load(file)

analysis_crs = config.get("analysis_crs")

visualisation_crs = config.get("visualisation_crs")

# %%
region_path = config.get("data_dir") + datasets.get("admin_boundary").get("geoboundaries_ADM1")
district_path = config.get("data_dir") + datasets.get("admin_boundary").get("geoboundaries_ADM2")

adm1 = gpd.read_file(region_path)
adm2 = gpd.read_file(district_path)

# renaming for better understanding
adm1.rename(columns={'shapeName':'Region'}, inplace=True)
adm2.rename(columns={'shapeName':'District'}, inplace=True)

# %%
dup_dir = config.get("data_dir") + datasets.get("health_facility").get("duplicates")

df = gpd.read_file(dup_dir)

df.rename(columns={'field_1': 'orig_index'}, inplace=True)

# converting long and lat 
df['latitude'] = df['latitude'].apply(float)
df['longitude'] = df['longitude'].apply(float)
df['orig_index'] = df['orig_index'].apply(int)
#df.rename(columns={'Facility name': 'Facility Name', 'Facility ownership': 'Facility Ownership', 'Facility type': 'Facility Type'}, inplace=True)

df.head()

# %%
df['Facility name'].value_counts()

# %%
# null counts per row 
df['null_count'] = df.isnull().sum(axis=1)

# %%
df.head()

# %%
# visualising where these are on the map
geo_util.plot_map(df, adm1, adm2, 'latitude', 'longitude', 'Facility name', visualisation_crs)

# %%
checked_fac = []
far_and_same = []
far_and_diff = []
same = []
idxs_same = {}
idxs_far_same = set()
idxs_far_diff = set()
idxs_extra = set()

for idxup, rowup in df.iterrows():
    for idx, row in df.iterrows():
       if rowup['Facility name'] == row['Facility name'] and rowup.orig_index != row.orig_index and {rowup.orig_index, row.orig_index} not in checked_fac:
            checked_fac.append({rowup.orig_index, row.orig_index})
            dist = geo_util.straight_path_distance(rowup.latitude, rowup.longitude, row.latitude, row.longitude)
            if dist > 1 and rowup['District'] == row['District']:
                far_and_same.append([rowup.orig_index, row.orig_index, dist])
                idxs_far_same.add(rowup.orig_index)
                idxs_far_same.add(row.orig_index)
            elif dist > 1 and rowup['District'] != row['District']:
                # checks for same but far, such that nulls district is making them different
                if not rowup['District'] or not row['District']:
                    if rowup['derived_district'] == row['derived_district']:
                        idxs_extra.add(row.orig_index)
                        idxs_extra.add(rowup.orig_index)
                else: 
                    far_and_diff.append([rowup.orig_index, row.orig_index, dist])
                    idxs_far_diff.add(rowup.orig_index)
                    idxs_far_diff.add(row.orig_index)

            elif dist < 1 and rowup['District'] == row['District']:
                same.append([rowup.orig_index, row.orig_index, dist])
                idxs_same[rowup.orig_index] = row.orig_index

# %% [markdown]
# ### Same facilties within 1km

# %%
# for facilities that are the same and within 1km

one_of_same = df[df['orig_index'].isin(list(idxs_same.keys()))]
one_of_same['Facility name'].value_counts()

# %% [markdown]
# ### Same facilities but outisde 1km

# %%

# for facilities that are the same but outisde 1km
far_same = df[df['orig_index'].isin(list(idxs_far_same))]
far_same['Facility name'].value_counts()

# %%
far_same[far_same['Facility name'] == 'Zomba Central Prison Clinic']

# %%
# visualising where these are on the map
geo_util.plot_map(far_same[far_same['Facility name'] == 'Zomba Central Prison Clinic'], adm1, adm2, 'latitude', 'longitude', 'Facility name', visualisation_crs)

# %% [markdown]
# ### Different facilities 

# %%
far_diff = df[df['orig_index'].isin(list(idxs_far_diff))]
far_diff['Facility name'].value_counts()

# %%
far_diff

# %%
# dropping the facilities that are same based on the name and district
# dropping the duplicates with the same name and location
far_diff.drop_duplicates(subset=['Facility name', 'District'], keep='first', inplace=True)

# %%
far_diff

# %%
# visualising where these are on the map
geo_util.plot_map(far_diff[far_diff['Facility name'] == 'Madalitso Private Clinic'], adm1, adm2, 'latitude', 'longitude', 'Facility name', visualisation_crs)

# %% [markdown]
# The ones below are for facilities with possiblities of being the same but do no have district to use as a deciding factor. The derived districts were used to confirm that their different. A major issue with handling the duplicates is knowing which facility to drop because some that are the same have different geo locations, so it's difficult telling which is right.

# %%
# possibly same facilities but with some districts missing
far_nan = df[df['orig_index'].isin(list(idxs_extra))]
far_nan['Facility name'].value_counts()

# %%
far_nan[far_nan['Facility name'] == 'Chipho Health Centre']

# %%



