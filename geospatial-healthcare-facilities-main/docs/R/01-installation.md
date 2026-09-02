# Installation

## Prerequisites

- [R](https://cran.r-project.org/) 4.3 or later
- [RStudio](https://posit.co/download/rstudio-desktop/) or VS Code with an R extension
- Java 21 for [r5r](https://ipeagit.github.io/r5r/)
- [Quarto](https://quarto.org/docs/get-started/) to render and view the dashboard output

## Install R packages

The R workflow includes a `DESCRIPTION` file at `src/r/dashboard/DESCRIPTION`, which can be used to install dependencies.

From an R session in the repository root:

```r
install.packages("devtools")
devtools::install_deps("src/r/dashboard", dependencies = TRUE)
```

This installs the packages needed for the two main pipeline scripts:

- `src/r/dashboard/run/01_preprocess.R`
- `src/r/dashboard/run/02_ttm.R`

It also installs optional dashboard and test dependencies declared in `Suggests`.

If you need a manual fallback, install the core runtime packages with:

```r
install.packages(c(
	"arrow",
	"countrycode",
	"curl",
	"dplyr",
	"here",
	"httr",
	"jsonlite",
	"osmdata",
	"purrr",
	"r5r",
	"rJavaEnv",
	"readr",
	"readxl",
	"rlang",
	"sf",
	"stringr",
	"terra",
	"yaml"
))
```

If `devtools::install_deps()` fails on R 4.5 with messages that specific package versions do not exist. A practical workaround is to install the required versions explicitly with `pak`:

```r
install.packages("pak")
pak::pak("osmdata@0.3.0")
pak::pak("r5r@2.3.0")
```

## Java setup for r5r

The travel-time stage in `02_ttm.R` builds an `r5r` network and requires a working Java installation. The script uses `rJavaEnv::java_quick_install(version = 21)`, but it is still better to verify that Java is available before running the pipeline.

In R install java with the following command and type "yes" when prompted for consent to install the JDK:
```r
rJavaEnv::java_quick_install(version = 21)
```

Check that Java is installed and configured correctly with:
```r
rJavaEnv::java_check_version_rjava()
```

If Java is already installed and configured correctly, these checks should pass without further changes.

## Quarto

Quarto is required to render and inspect the dashboard output produced from the travel-time results.

Download and install Quarto from [quarto.org](https://quarto.org/docs/get-started/), then verify it is on your PATH:

```bash
quarto --version
```

## Verify the setup

After installing packages, a simple check is to load the dashboard package from its local folder and confirm dependencies load cleanly.

```r
devtools::load_all(here::here("src", "r", "dashboard"), quiet = TRUE)
```

You can then move on to configuring:

- the country
- boundary source
- facility source
- WorldPop inputs
- district assignment method

See [02 — Configuration](02-configuration.md).

## Running the full pipeline

Once installed and configured, the entire pipeline can be run end-to-end from a single entry point at the repository root:

```r
source(here::here("src", "r", "dashboard", "_run_all.R"))
```

This runs `01_preprocess.R`, `02_ttm.R`, and then launches the dashboard. The numbered scripts can still be run independently if you only need to re-run a specific stage — for example, after updating config or facility data without repeating the travel-time computation.

## Next step

→ [02 — Configuration](02-configuration.md)
