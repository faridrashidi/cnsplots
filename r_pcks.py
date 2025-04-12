import os

import rpy2.robjects as ro

ro.r("renv::init(settings = list(project.directory = '.renv'))")

# os.environ["R_PROFILE_USER"] = "./.Rprofile"
# ro.r("renv::install('devtools')")
# ro.r("renv::install('tidyverse/tidyr')")
ro.r("renv::snapshot()")
