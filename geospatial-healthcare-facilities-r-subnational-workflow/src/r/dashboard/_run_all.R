# Run all scripts to launch the dashboard
# Before running this script, ensure that you have installed all required R packages
# and that you have configured the config.yaml file with your country and data paths.
# You can find detailed instructions in the `docs/R/` directory.
library(quarto)

source(here::here("src", "r", "dashboard", "run", "01_preprocess.R"))
source(here::here("src", "r", "dashboard", "run", "02_ttm.R"))

# Launch dashboard
quarto::quarto_preview(here::here('src', 'r', 'dashboard', 'hcf-dashboard.qmd'))