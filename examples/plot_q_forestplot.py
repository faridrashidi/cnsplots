"""
forestplot
----------

create forestplot
"""

# %%
# load data
import lifelines as ll

import cnsplots as cns

rossi = ll.datasets.load_rossi()

# %%
# plot forestplot using :func:`cnsplots.forestplot`
cns.figure(100, 180, ["black"])
cns.forestplot(rossi, duration="week", event="arrest")
