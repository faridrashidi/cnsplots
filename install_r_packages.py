import os

import rpy2.robjects as ro

os.environ["R_PROFILE_USER"] = "./.Rprofile"
ro.r("renv::install('cmprsk')")
ro.r("renv::snapshot()")
