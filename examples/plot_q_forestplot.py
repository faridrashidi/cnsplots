"""
forestplot
----------

create forestplot
"""

# %%
# load data
from lifelines.datasets import load_rossi

import cnsplots as cns

rossi = load_rossi()

# %%
# plot forestplot using :func:`cnsplots.forestplot`
cns.figure(100, 180, ["black"])
cns.forestplot(rossi, duration="week", event="arrest")
