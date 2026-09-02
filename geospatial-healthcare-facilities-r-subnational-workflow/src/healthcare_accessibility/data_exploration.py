# %% [markdown]
# Visualisations after all 3 datasets cleaned and merged

# %%
# Import necessary libraries
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd
from pathlib import Path
import seaborn as sb
import yaml

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

# %%
# Load dataframe
gdf = gpd.read_file(
    config.get("data_dir") + datasets.get("health_facility").get("cleaned_hcf"),
)
gdf.head()

# %% [markdown]
# Regions

# %%
# Bar plot for Region column
plt.figure(figsize=(10, 6))
color = ["lightblue", "blue", "purple"]
gdf["Region"].value_counts().plot(kind="barh", color=color, edgecolor="black")
plt.title("Number of Health Facilities by Region in Malawi")
plt.xlabel("Number")
plt.ylabel("Region")
plt.grid()
plt.show()

# %% [markdown]
# Districts

# %%
# Bar plot for District
plt.figure(figsize=(10, 6))

# Count the occurrences of each facility type
district_counts = gdf["District"].value_counts()

# Generate a list of distinct colors using a colormap
colors = plt.cm.tab10.colors  # You can also try plt.cm.Set3, plt.cm.Paired, etc.
color_list = [colors[i % len(colors)] for i in range(len(district_counts))]


# Create the horizontal bar plot
gdf["District"].value_counts().plot(kind="barh", color=color_list, edgecolor="black")
plt.title("Number of Health Facilities by District in Malawi")
plt.xlabel("Number")
plt.ylabel("Districts")
plt.grid()
plt.show()

# %% [markdown]
# Facility Type

# %%
# Bar plot for Facility Type
plt.figure(figsize=(10, 6))

# Count the occurrences of each facility type
facility_type_counts = gdf["Facility Type"].value_counts()

# Generate a list of distinct colors using a colormap
colors = plt.cm.tab10.colors  # You can also try plt.cm.Set3, plt.cm.Paired, etc.
color_list = [colors[i % len(colors)] for i in range(len(facility_type_counts))]


# Create the horizontal bar plot
gdf["Facility Type"].value_counts().plot(
    kind="barh", color=color_list, edgecolor="black"
)
plt.title("Number of Health Facilities by Type in Malawi")
plt.xlabel("Number")
plt.ylabel("Facility Type")
plt.grid()
plt.show()

# %% [markdown]
# Group by Region and breakdown Facility Type

# %%
# Group by Facility Type and Region, then count occurrences
df_region_facility_type = (
    gdf.groupby("Facility Type")["Region"].value_counts().reset_index(name="Count")
)

# setting the dimensions of the plot
fig, ax = plt.subplots(figsize=(20, 10))
plt.title("Number of Health Facilities by Type and Region in Malawi")
plt.grid()
sb.barplot(
    y="Facility Type",
    x="Count",
    hue="Region",
    palette="viridis",  # can choose a different palette
    data=df_region_facility_type,
)

# %% [markdown]
# Rural or Urban (missing some values)

# %%
# Bar plot for Facility Location
plt.figure(figsize=(10, 6))

# Count the occurrences of each facility type
facility_location_counts = gdf["Facility Location"].value_counts()

# Generate a list of distinct colors using a colormap
colors = plt.cm.tab10.colors  # You can also try plt.cm.Set3, plt.cm.Paired, etc.
color_list = [colors[i % len(colors)] for i in range(len(facility_type_counts))]


# Create the horizontal bar plot
gdf["Facility Location"].value_counts().plot(
    kind="barh", color=color_list, edgecolor="black"
)
plt.title("Number of Health Facilities by Location in Malawi")
plt.xlabel("Number")
plt.ylabel("Facility Location")
plt.grid(which="major", axis="x", linestyle="--", linewidth=0.7)
plt.show()

# %%
# Group by Facility Location and Region, then count occurrences
df_region_location = (
    gdf.groupby("Facility Location")["Region"].value_counts().reset_index(name="Count")
)

# setting the dimensions of the plot
fig, ax = plt.subplots(figsize=(20, 10))
plt.title("Number of Health Facilities by Location and Region in Malawi")
plt.grid()
sb.barplot(
    y="Facility Location",
    x="Count",
    hue="Region",
    palette="hot",  # can choose a different palette
    data=df_region_location,
)

plt.grid(which="major", axis="x", linestyle="--", linewidth=0.7)

# %%
# Group by Facility Location and Type, then count occurrences
df_location_and_type = (
    gdf.groupby("Facility Type")["Facility Location"]
    .value_counts()
    .reset_index(name="Count")
)

# setting the dimensions of the plot
fig, ax = plt.subplots(figsize=(20, 10))
plt.title("Number of Health Facilities by Location and Type in Malawi")
sb.barplot(
    y="Facility Type",
    x="Count",
    hue="Facility Location",
    palette="pastel",  # can choose a different palette
    data=df_location_and_type,
)

plt.grid(which="major", axis="x", linestyle="--", linewidth=0.7)
plt.grid(which="major", axis="y", linestyle="--", linewidth=0.7)

# %% [markdown]
# Facility Ownership

# %%
# Group by Facility Type and Region, then count occurrences
df_region_facility_ownership = (
    gdf.groupby("Facility Ownership")["Region"].value_counts().reset_index(name="Count")
)

# setting the dimensions of the plot
fig, ax = plt.subplots(figsize=(20, 10))
plt.title("Number of Facility Ownerships by Region in Malawi")
plt.grid()
sb.barplot(
    y="Facility Ownership",
    x="Count",
    hue="Region",
    palette="viridis",  # can choose a different palette
    data=df_region_facility_ownership,
)

plt.grid(which="major", axis="x", linestyle="--", linewidth=0.7)

# %%
# Group by Facility Location and Type, then count occurrences
df_ownership_and_type = (
    gdf.groupby("Facility Ownership")["Facility Location"]
    .value_counts()
    .reset_index(name="Count")
)

# setting the dimensions of the plot
fig, ax = plt.subplots(figsize=(20, 10))
plt.title("Number of Health Facilities by Ownership and Location in Malawi")
plt.grid()
sb.barplot(
    y="Facility Ownership",
    x="Count",
    hue="Facility Location",
    palette="Accent",  # can choose a different palette
    data=df_ownership_and_type,
)

plt.grid(which="major", axis="x", linestyle="--", linewidth=0.7)
plt.grid(which="major", axis="y", linestyle="--", linewidth=0.7)
