# %%
import os
import re
import yaml
import pyproj 
import pandas as pd
import seaborn as sns
import geopandas as gpd
from pathlib import Path
import matplotlib.pyplot as plt

import healthcare_accessibility.geospatial_utils as geo_util

#%%
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
osm_points_shp = config.get("data_dir") + datasets.get("health_facility").get("hotosm_mwi_points")
osm_polys_shp = config.get("data_dir") + datasets.get("health_facility").get("hotosm_mwi_polygons")
#baobab = config.get("data_dir") + datasets.get("health_facility").get("baobab")
health_master_list = config.get("data_dir") + datasets.get("health_facility").get("zipatala") # or hml
figshare_data = config.get("data_dir") + datasets.get("health_facility").get("figshare")

# %%
osm_points_df = gpd.read_file(osm_points_shp)
osm_points_df

# %%
osm_polys_df = gpd.read_file(osm_polys_shp)
osm_polys_df

# %%
# Load dataframe
baobab_df = geo_util.load_georeferenced_csv_or_xlsx(
    file_path=config.get("data_dir") + datasets.get("health_facility").get("baobab"),
    lat_col="latitude",
    lon_col="longitude",
    sheet_name="csv",
    desired_crs=visualisation_crs,
)

baobab_df.drop(
    columns=[
        "Catchment Population (2018)",
        "longitude",
        "latitude",
    ],
    inplace=True,
)

baobab_df = baobab_df.loc[
    :, ~baobab_df.columns.str.lower().str.contains("nnamed:")
]
# %%
hml_df = pd.read_excel(health_master_list, engine='openpyxl')
hml_df.head()

# %%
# correctly naming the features in hml
hml_df.drop(columns=['Facility Name', 'Facility type'], axis=1, inplace=True)
hml_df.drop([0], axis=0, inplace=True)
hml_df.rename(columns={'Unnamed: 1':'Zone', 'Unnamed: 2':'District', 'Unnamed: 3':'Facility name', \
    'Unnamed: 6':'Facility type', 'Managing authority   Urban/Rural': 'Managing authority', \
    'Unnamed: 8':'Urban/Rural', 'Region            Zone                District':'Region',}, inplace=True)
hml_df.head()

# %%
# grouping districts by zones
hml_df.groupby('Zone')['District'].unique().to_frame()

# %%
figshare_dir = config.get("data_dir") + datasets.get("health_facility").get("figshare")
figshare_df = geo_util.clean_figshare(figshare_dir)
figshare_df.head()


# %%
# available datasets
data = {'osm_points':osm_points_df, 'osm_polys':osm_polys_df, 'baobab':baobab_df, 'master_list':hml_df, 'figshare':figshare_df}

# %%
# exploring the uniqueness of each data
for name, d in data.items():
    print(f'The features in {name} are {d.columns}')
    print(' ')

# %%
def show_adminbrkdown():
    """
    Displays the administrative units in each datasets
    """

    # checking the administrative breakdowns in datasets
    print('For masters list')
    print(hml_df['Region'].unique())
    print(hml_df['District'].unique())
    print(f'Masters list has {hml_df['District'].nunique()} districts')

    print('For baobab')
    print(baobab_df['District'].unique())
    print(f'Baobab list has {baobab_df['District'].nunique()} districts')

    print('For figshare')
    print(figshare_df['Region'].unique())

# %%
show_adminbrkdown()

# %%
# From online resources Malawi has 28 districts but there are 29 districts
# within our datasets.
# Masters list divided Mzimba into north and south and nkhatabay and blantyre
# are misspelt

curr_districts = ['Dedza', 'Dowa', 'Kasungu', 'Lilongwe', 'Mchinji', 'Nkhotakota', 'Ntcheu', 'Ntchisi', 'Salima', 'Chitipa', 'Karonga', 'Likoma', 'Mzimba', 'Nkhata Bay', 'Rumphi', 'Balaka', 'Blantyre', 'Chikwawa', 'Chiradzulu', 'Machinga', 'Mangochi','Mulanje', 'Mwanza', 'Nsanje', 'Thyolo', 'Phalombe', 'Zomba', 'Neno']
for d in curr_districts:
    if d not in hml_df['District'].unique():
        print('hml_df', d)
    elif d not in baobab_df['District'].unique():
        print('baobab', d)

# %%
# making the corrections to districts

# some values in district have white space
baobab_df['District'] = baobab_df['District'].str.strip()

# correcting the names
hml_df['District'] = hml_df['District'].replace('Blanytyre', 'Blantyre')
hml_df['District'] = hml_df['District'].replace('Nkhatabay', 'Nkhata Bay')
hml_df['District'] = hml_df['District'].replace('Mzimba North', 'Mzimba')
hml_df['District'] = hml_df['District'].replace('Mzimba South', 'Mzimba')

# %%
show_adminbrkdown()

# %% [markdown]
# From above we see that numbers have adjusted to how it's meant to be

# %%
# checking th null values
for name, d in data.items():
    print(f'For {name}')
    print(f'The size of {name} is {d.shape}')
    print(d.isnull().sum())
    print('  ')

# %% [markdown]
# ### Combining Figshare and hml

# %%
# exploring figshare in master list
figshare_df['in_hml'] = figshare_df['Facility name'].isin(hml_df['Facility name'])
figshare_df

# %% [markdown]
# Note: Malawi is administratively divided into three regions, which are further broken down into 28 districts

# %%
figshare_df['in_hml'].value_counts()

# %%
# exploring the ones not found 
fig_not_hml = list(figshare_df[figshare_df['in_hml'] == False]['Facility name'])
hml_hos = list(hml_df['Facility name'])
in_hml = {}

for hos in fig_not_hml:
    for k in hml_hos:
        if re.search(hos, k, re.IGNORECASE):
            #dropping lugola and gola as they are different hospitals
            if hos == 'Gola Health Centre':
                continue
            print(hos, '...', k)
            in_hml[hos] = k


# changing the ones not caught earlier to true
m = figshare_df['Facility name'].isin(list(in_hml))

# update those specifically
figshare_df.loc[m, ['in_hml']] = True

figshare_df['in_hml'].value_counts()

# %%
figshare_df['in_hml'].value_counts()

# %%
# making the names the same 
for hos, hos_hml in in_hml.items():
    figshare_df.at[figshare_df['Facility name'].tolist().index(hos),'Facility name'] = hos_hml

# %%
# joining figshre with masters list
figshare_hml = pd.merge(figshare_df, hml_df, on='Facility name', how='inner')
figshare_hml

# %%
figshare_hml.isnull().sum()

# %%
# checking the hospitals with missing lat and long
null_rows = figshare_hml[figshare_hml.isna().any(axis=1)].copy()
null_rows

# %%
# checking if it is in baobaab
null_rows['in_hml'] = null_rows['Facility name'].isin(baobab_df['Facility Name'])
null_rows

# %%
# getting their coordinates from baobab
figshare_hml.loc[figshare_hml['Lat'].isna(), 'Lat'] = baobab_df['latitude']
figshare_hml.loc[figshare_hml['Long'].isna(), 'Long'] = baobab_df['longitude']
figshare_hml

# %%
# saving currently combined data
figshare_hml.to_csv(config.get("data_dir") + 'figshare_hml.csv', index=False)

# %%
# Analysis of combined data (figshare, baobab and eliz aids)
combined_data = geo_util.load_georeferenced_csv_or_xlsx(
    config.get("data_dir") + datasets.get("health_facility").get("whole_data"),
    "latitude",
    "longitude",
    desired_crs=analysis_crs,
)

# further cleaning
combined_data['Facility Location'].replace('U', 'Urban', inplace=True)

# %%
# number of facilities in each district
sns.countplot(data=combined_data, x='District', hue='Facility Location')
plt.xticks(rotation=90)
plt.title('Urban and Rural distribution within districts')
plt.show()

#%%
sns.countplot(data=combined_data, x='Facility type', hue='Facility Location')
plt.title('Facility type distribution within urban and rural locations')
plt.xticks(rotation=90)
plt.show()


# %%
plt.figure(figsize=(10,8))
sns.histplot(data=combined_data, x='District', hue='Facility type', multiple='fill', shrink=0.8, palette='husl')
plt.title('Facility type distribution within districts')
plt.xticks(rotation=90)
plt.show()

# %%
plt.figure(figsize=(10,8))
sns.histplot(data=combined_data, x='Facility type', hue='Facility ownership', multiple='fill', shrink=0.8, palette='husl')
plt.title('Ownership of the different facilities, distributed by type')
plt.xticks(rotation=90)
plt.show()

# %%
combined_data.head(5)

# %%
