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

# %%
# plot hazardplot using :func:`cnsplots.hazardplot`
cns.figure(150, 150)
cns.hazardplot(data=rossi, duration="week", event="arrest")
