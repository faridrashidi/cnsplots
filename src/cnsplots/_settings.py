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
>>> cns.settings.title_fontsize = 10
>>> cns.settings.title_fontweight = "normal"

>>> # Suppress print statements
>>> cns.settings.verbosity = 0

>>> # Reset to defaults
>>> cns.settings.reset()

>>> # Temporarily override settings using a context manager
>>> with cns.settings.context(title_fontsize=12, palette_qual="Set2"):
...     cns.boxplot(...)  # Uses temporary settings
>>> cns.settings.title_fontsize  # Restored to previous value
8
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


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
    title_fontsize : int
        Font size for titles and axis labels.
        Default: 8
    title_fontweight : str | int
        Font weight for titles.
        Default: "bold"
    fontsize_legend : int
        Font size for tick labels and legend text.
        Default: 7
    axes_linewidth : float
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
    >>> cns.settings.title_fontsize = 10
    >>> cns.settings.title_fontweight = "normal"
    >>> cns.settings.verbosity = 0  # Suppress prints

    >>> # Reset all settings to defaults
    >>> cns.settings.reset()
    """

    # Default values (class-level constants for reference)
    _defaults = {
        "palette_qual": "Ecotyper1",
        "palette_seq": "gnuplot",
        "title_fontsize": 8,
        "title_fontweight": "bold",
        "fontsize_legend": 7,
        "axes_linewidth": 0.5,
        "verbosity": 1,
    }

    _palette_qual: str
    _palette_seq: str
    _title_fontsize: int | float
    _title_fontweight: str | int
    _fontsize_legend: int | float
    _axes_linewidth: int | float
    _verbosity: int

    def _invalid_setting_message(self, name: str) -> str:
        """Return a consistent error message for unknown setting names."""
        valid_settings = ", ".join(sorted(type(self)._defaults))
        return f"'{name}' is not a valid setting. Valid settings: {valid_settings}"

    def __setattr__(self, name: str, value: Any) -> None:
        """Reject unknown public attributes so removed settings fail loudly."""
        if not name.startswith("_") and name not in type(self)._defaults:
            raise AttributeError(self._invalid_setting_message(name))
        super().__setattr__(name, value)

    def __getattr__(self, name: str) -> Any:
        """Raise a helpful error for missing public setting names."""
        if not name.startswith("_"):
            raise AttributeError(self._invalid_setting_message(name))
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}"
        )

    def __init__(self) -> None:
        """Initialize settings with default values."""
        self.reset()

    def reset(self) -> None:
        """Reset all settings to their default values.

        Examples
        --------
        >>> import cnsplots as cns
        >>> cns.settings.title_fontsize = 12
        >>> cns.settings.reset()
        >>> cns.settings.title_fontsize
        8
        """
        self._palette_qual = str(self._defaults["palette_qual"])
        self._palette_seq = str(self._defaults["palette_seq"])
        self._title_fontsize = int(self._defaults["title_fontsize"])
        self._title_fontweight = str(self._defaults["title_fontweight"])
        self._fontsize_legend = int(self._defaults["fontsize_legend"])
        self._axes_linewidth = float(self._defaults["axes_linewidth"])
        self._verbosity = int(self._defaults["verbosity"])

    # --- palette_qual ---
    @property
    def palette_qual(self) -> str:
        """str: Default qualitative color palette for categorical data."""
        return self._palette_qual

    @palette_qual.setter
    def palette_qual(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("palette_qual must be a string")
        self._palette_qual = value

    # --- palette_seq ---
    @property
    def palette_seq(self) -> str:
        """str: Default sequential colormap for continuous data."""
        return self._palette_seq

    @palette_seq.setter
    def palette_seq(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("palette_seq must be a string")
        self._palette_seq = value

    # --- title_fontsize ---
    @property
    def title_fontsize(self) -> int | float:
        """int: Font size for titles and axis labels."""
        return self._title_fontsize

    @title_fontsize.setter
    def title_fontsize(self, value: int | float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("title_fontsize must be a number")
        if value <= 0:
            raise ValueError("title_fontsize must be positive")
        self._title_fontsize = value

    # --- title_fontweight ---
    @property
    def title_fontweight(self) -> str | int:
        """str | int: Font weight for titles."""
        return self._title_fontweight

    @title_fontweight.setter
    def title_fontweight(self, value: str | int) -> None:
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise TypeError("title_fontweight must be a string or integer")
        self._title_fontweight = value

    # --- fontsize_legend ---
    @property
    def fontsize_legend(self) -> int | float:
        """int: Font size for tick labels and legend text."""
        return self._fontsize_legend

    @fontsize_legend.setter
    def fontsize_legend(self, value: int | float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("fontsize_legend must be a number")
        if value <= 0:
            raise ValueError("fontsize_legend must be positive")
        self._fontsize_legend = value

    # --- axes_linewidth ---
    @property
    def axes_linewidth(self) -> int | float:
        """float: Line width for axis spines."""
        return self._axes_linewidth

    @axes_linewidth.setter
    def axes_linewidth(self, value: int | float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("axes_linewidth must be a number")
        if value <= 0:
            raise ValueError("axes_linewidth must be positive")
        self._axes_linewidth = value

    # --- verbosity ---
    @property
    def verbosity(self) -> int:
        """int: Verbosity level. 0 = silent, 1 = normal (default)."""
        return self._verbosity

    @verbosity.setter
    def verbosity(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("verbosity must be an integer")
        if value < 0:
            raise ValueError("verbosity must be non-negative")
        self._verbosity = value

    @contextmanager
    def context(self, **kwargs: Any) -> Generator[CNSSettings, None, None]:
        """Temporarily override settings within a context manager.

        Settings are restored to their previous values when the context
        exits, even if an exception occurs.

        Parameters
        ----------
        **kwargs
            Setting names and their temporary values. Valid keys are:
            palette_qual, palette_seq, title_fontsize, title_fontweight,
            fontsize_legend, axes_linewidth, verbosity.

        Raises
        ------
        AttributeError
            If an invalid setting name is provided.

        Examples
        --------
        >>> import cnsplots as cns
        >>> with cns.settings.context(title_fontsize=12, palette_qual="Set2"):
        ...     print(cns.settings.title_fontsize)
        12
        >>> cns.settings.title_fontsize
        8
        """
        # Validate keys before changing anything
        for key in kwargs:
            if key not in self._defaults:
                raise AttributeError(self._invalid_setting_message(key))

        # Save current values
        old_values = {key: getattr(self, key) for key in kwargs}

        # Apply temporary values (uses property setters for validation)
        try:
            for key, value in kwargs.items():
                setattr(self, key, value)
            yield self
        finally:
            # Restore previous values
            for key, value in old_values.items():
                setattr(self, key, value)

    def __repr__(self) -> str:
        """Return a string representation of current settings."""
        return (
            f"CNSSettings(\n"
            f"    palette_qual={self.palette_qual!r},\n"
            f"    palette_seq={self.palette_seq!r},\n"
            f"    title_fontsize={self.title_fontsize},\n"
            f"    title_fontweight={self.title_fontweight!r},\n"
            f"    fontsize_legend={self.fontsize_legend},\n"
            f"    axes_linewidth={self.axes_linewidth},\n"
            f"    verbosity={self.verbosity}\n"
            f")"
        )


# Global settings instance
settings = CNSSettings()
