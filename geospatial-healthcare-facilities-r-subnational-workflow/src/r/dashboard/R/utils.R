#' Clean area name for file paths
#'
#' @param area_name Area name to clean
#' @return Cleaned area name
clean_area_name <- function(area_name) {
    # Convert to lowercase
    area_name <- tolower(area_name)
    
    # Replace spaces and special characters with underscores
    area_name <- gsub("[^a-z0-9]+", "_", area_name)
    
    # Remove leading and trailing underscores
    area_name <- gsub("^_+|_+$", "", area_name)
    
    return(area_name)
}


#' Define area name based on analysis mode
#'
#' @param config Configuration list containing analysis_mode, country, and subnational_area
#' @return The area name based on the analysis mode
define_area_name <- function(config) {
  if (config$analysis_mode == "country") {
    return(clean_area_name(config$country))
  } else if (config$analysis_mode == "subnational") {
    return(clean_area_name(config$subnational_area))
  } else {
    stop("Invalid analysis_mode in config.yaml. Must be 'country' or 'subnational'.")
  }
}
