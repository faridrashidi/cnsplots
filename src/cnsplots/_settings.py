"""Global settings for cnsplots.

This module provides a centralized configuration system for cnsplots,
allowing users to set global defaults for plotting parameters.

Examples
--------
>>> import cnsplots as cns

>>> # View current settings
>>> cns.settings.palette_qual
'Ecotyper1'

>>> # Change settings
>>> cns.settings.palette_qual = "Set2"
>>> cns.settings.fontsize_title = 10

>>> # Suppress print statements
>>> cns.settings.verbosity = 0

>>> # Reset to defaults
>>> cns.settings.reset()
"""


class CNSSettings:
    """Global settings for cnsplots.

    This class manages global configuration options that affect plotting
    behavior across all cnsplots functions.

    Attributes
    ----------
    palette_qual : str
        Default qualitative (categorical) color palette.
        Default: "Ecotyper1"
    palette_seq : str
        Default sequential colormap for continuous data.
        Default: "gnuplot"
    fontsize_title : int
        Font size for titles and axis labels.
        Default: 8
    fontsize_legend : int
        Font size for tick labels and legend text.
        Default: 7
    linewidth_axes : float
        Line width for axis spines.
        Default: 0.5
    verbosity : int
        Controls print output verbosity.
        0 = silent (no prints), 1 = normal (default).

    Examples
    --------
    >>> import cnsplots as cns

    >>> # Access settings
    >>> cns.settings.palette_qual
    'Ecotyper1'

    >>> # Modify settings
    >>> cns.settings.palette_qual = "Dark2"
    >>> cns.settings.fontsize_title = 10
    >>> cns.settings.verbosity = 0  # Suppress prints

    >>> # Reset all settings to defaults
    >>> cns.settings.reset()
    """

    # Default values (class-level constants for reference)
    _defaults = {
        "palette_qual": "Ecotyper1",
        "palette_seq": "gnuplot",
        "fontsize_title": 8,
        "fontsize_legend": 7,
        "linewidth_axes": 0.5,
        "verbosity": 1,
    }

    def __init__(self):
        """Initialize settings with default values."""
        self.reset()

    def reset(self):
        """Reset all settings to their default values.

        Examples
        --------
        >>> import cnsplots as cns
        >>> cns.settings.fontsize_title = 12
        >>> cns.settings.reset()
        >>> cns.settings.fontsize_title
        8
        """
        self._palette_qual = self._defaults["palette_qual"]
        self._palette_seq = self._defaults["palette_seq"]
        self._fontsize_title = self._defaults["fontsize_title"]
        self._fontsize_legend = self._defaults["fontsize_legend"]
        self._linewidth_axes = self._defaults["linewidth_axes"]
        self._verbosity = self._defaults["verbosity"]

    # --- palette_qual ---
    @property
    def palette_qual(self):
        """str: Default qualitative color palette for categorical data."""
        return self._palette_qual

    @palette_qual.setter
    def palette_qual(self, value):
        if not isinstance(value, str):
            raise TypeError("palette_qual must be a string")
        self._palette_qual = value

    # --- palette_seq ---
    @property
    def palette_seq(self):
        """str: Default sequential colormap for continuous data."""
        return self._palette_seq

    @palette_seq.setter
    def palette_seq(self, value):
        if not isinstance(value, str):
            raise TypeError("palette_seq must be a string")
        self._palette_seq = value

    # --- fontsize_title ---
    @property
    def fontsize_title(self):
        """int: Font size for titles and axis labels."""
        return self._fontsize_title

    @fontsize_title.setter
    def fontsize_title(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("fontsize_title must be a number")
        if value <= 0:
            raise ValueError("fontsize_title must be positive")
        self._fontsize_title = value

    # --- fontsize_legend ---
    @property
    def fontsize_legend(self):
        """int: Font size for tick labels and legend text."""
        return self._fontsize_legend

    @fontsize_legend.setter
    def fontsize_legend(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("fontsize_legend must be a number")
        if value <= 0:
            raise ValueError("fontsize_legend must be positive")
        self._fontsize_legend = value

    # --- linewidth_axes ---
    @property
    def linewidth_axes(self):
        """float: Line width for axis spines."""
        return self._linewidth_axes

    @linewidth_axes.setter
    def linewidth_axes(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("linewidth_axes must be a number")
        if value <= 0:
            raise ValueError("linewidth_axes must be positive")
        self._linewidth_axes = value

    # --- verbosity ---
    @property
    def verbosity(self):
        """int: Verbosity level. 0 = silent, 1 = normal (default)."""
        return self._verbosity

    @verbosity.setter
    def verbosity(self, value):
        if not isinstance(value, int):
            raise TypeError("verbosity must be an integer")
        if value < 0:
            raise ValueError("verbosity must be non-negative")
        self._verbosity = value

    def __repr__(self):
        """Return a string representation of current settings."""
        return (
            f"CNSSettings(\n"
            f"    palette_qual={self.palette_qual!r},\n"
            f"    palette_seq={self.palette_seq!r},\n"
            f"    fontsize_title={self.fontsize_title},\n"
            f"    fontsize_legend={self.fontsize_legend},\n"
            f"    linewidth_axes={self.linewidth_axes},\n"
            f"    verbosity={self.verbosity}\n"
            f")"
        )


# Global settings instance
settings = CNSSettings()
