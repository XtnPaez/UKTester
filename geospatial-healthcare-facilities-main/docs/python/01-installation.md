# Installation

## Prerequisites

- [Conda](https://docs.conda.io/en/latest/) (recommended for geospatial dependencies)
- [Quarto](https://quarto.org/docs/get-started/) (required for dashboard rendering)

## Python environment

Conda is recommended due to the number of geospatial packages that require compiled system libraries.

Within a Terminal navigate to the repository root and run:

```bash
conda env create -f environment.yml
conda activate hc-mapping
```

Then whilst still in the root folder, and in your chosen python environment, run the following in a terminal:

```bash
pip install -e .
```

The final `pip install -e .` installs the local `healthcare_accessibility` package in editable mode so that all scripts can import from it directly.

**Alternatively:**

If the above does work, please try the following:

```bash
conda create -n hc-mapping python=3.11
conda activate hc-mapping
conda install -c conda-forge r5py osmnx pyrosm pyjanitor
pip install -r requirements.txt
```

Whilst in the root folder, and in your chosen python environment, run the following in a terminal:

```bash
pip install -e .
```

## Quarto

Download and install Quarto from [quarto.org](https://quarto.org/docs/get-started/), then verify it is on your PATH:

```bash
quarto --version
```

## Next step

→ [02 — Configuration](02-configuration.md)
