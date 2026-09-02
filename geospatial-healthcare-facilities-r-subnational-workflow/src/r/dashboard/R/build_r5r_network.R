#' Build or load an r5r transport network
#'
#' @param data_path Path to the folder containing OSM and GTFS data
#' @return An r5r network object
#' @importFrom r5r build_network
#' @export
build_r5r_network_cached <- function(data_path) {
  r5r_network <- r5r::build_network(data_path = data_path)
  return(r5r_network)
}
