"""
hazardplot
----------

create hazardplot
"""

# %%
# load data
from lifelines.datasets import load_rossi

import cnsplots as cns

rossi = load_rossi()
rossi["wexp"] = rossi["wexp"].map({0: "Male", 1: "Female"})

# %%
# plot hazardplot using :func:`cnsplots.hazardplot`
cns.figure(130, 170)
cns.hazardplot(data=rossi, duration="week", event="arrest", hue="wexp")
