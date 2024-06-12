"""
forestplot
----------

create forestplot
"""

# %%
# load data
import lifelines as ll
from lifelines.datasets import load_rossi

import cnsplots as cns

rossi = load_rossi()
cph = ll.CoxPHFitter()
cph.fit(rossi, duration_col="week", event_col="arrest")
df = cph.summary.reset_index()

# %%
# plot forestplot using :func:`cnsplots.forestplot`
cns.figure(100, 180, ["black"])
cns.forestplot(df)
