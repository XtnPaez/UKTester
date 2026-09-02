# %%
# Packages
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
from function_script import clean_gdf_boundaries

# %%
# Set relative path to data folder for notebook
data_dir = Path().cwd().parent.joinpath('data')

# %% [markdown]
# # Load partially cleaned gdf

# %%
data_dir

# %%
# Load dataframe
partial_clean_gdf = gpd.read_file(data_dir.joinpath('partial_clean_malawi_health_facilities.geojson'))

# %%
# Check crs 
partial_clean_gdf.crs

# %%
# Change column name for Region
partial_clean_gdf.rename(columns={"Region": "Region Incomplete"}, inplace=True)

# %% [markdown]
# # Regions

# %%
# Use imported function
malawi_regions = clean_gdf_boundaries(file_name='regional_boundaries.geojson',
                                      column_name_to_change='Region')

# %%
# Remove the word "Region" from the 'location' column
malawi_regions['Region'] = malawi_regions['Region'].str.replace('Region', '', regex=False).str.strip()

# %%
malawi_regions

# %%
# Join Regions with gdf
partial_clean_gdf = gpd.sjoin(partial_clean_gdf, malawi_regions, how="left", predicate="within")

# %%
partial_clean_gdf

# %%
# Drop index right column for next join
partial_clean_gdf.drop(columns=['index_right'], inplace=True)

# %% [markdown]
# # Districts

# %%
# Use imported function
district_boundaries = clean_gdf_boundaries(file_name='district_boundaries.geojson',
                                           column_name_to_change='District')

# %%
# Check crs
district_boundaries.crs

# %%
# Join Regions with gdf
partial_clean_gdf = gpd.sjoin(partial_clean_gdf, district_boundaries, how="left", predicate="within")

# %%
# Drop Region incomplete, index right and District left column for next join
partial_clean_gdf.drop(columns=['index_right', 'District_left', 'Region Incomplete'], inplace=True)

# %%
# Change column name of district
partial_clean_gdf.rename(columns={"District_right": "District"}, inplace=True)

# %%
partial_clean_gdf

# %% [markdown]
# # Localities

# %%
# Use imported function
locality_boundaries = clean_gdf_boundaries(file_name='locality_boundaries.geojson',
                                           column_name_to_change='Localities')

# %%
locality_boundaries

# %%
# Check crs
locality_boundaries.crs

# %%
# Join Regions with gdf
partial_clean_gdf = gpd.sjoin(partial_clean_gdf, locality_boundaries, how="left", predicate="within")

# %%
# Drop unneeded columns
partial_clean_gdf.drop(columns=['index_right', 'District Code', 'Facility Code', 'Reg No.'], inplace=True)

# %%
partial_clean_gdf.to_file(data_dir / "cleaned_malawi_health_facilities.geojson", driver="GeoJSON")


