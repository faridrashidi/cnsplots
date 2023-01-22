import matplotlib.pyplot as plt

import cnsplots as cns


def setup_matplotlib():
    styles_path = cns.__path__[0]
    stylesheets = plt.style.core.read_style_directory(styles_path)
    plt.style.core.update_nested_dict(plt.style.library, stylesheets)
    plt.style.core.available[:] = sorted(plt.style.library.keys())
    plt.style.use("CNS")
