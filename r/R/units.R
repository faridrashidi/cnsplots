.cns_pt_to_mm <- function(value) {
  value * 25.4 / 72
}

.cns_to_inches <- function(value, units) {
  switch(
    units,
    px72 = value / 72,
    pt = value / 72,
    "in" = value,
    cm = value / 2.54,
    mm = value / 25.4,
    stop("Unsupported figure unit.", call. = FALSE)
  )
}

.cns_resolve_family <- function(value) {
  if (identical(value, "sans-serif")) return("sans")
  value
}

.cns_resolve_face <- function(value) {
  if (is.numeric(value)) return(if (value >= 600) "bold" else "plain")
  value <- tolower(value)
  if (value %in% c("normal", "regular")) return("plain")
  value
}
