"""Multipanel figure creation for CNSPlots."""

import matplotlib.pyplot as plt

import cnsplots as cns


class multipanel:
    """
    Create multi-panel figures with flexible panel sizes and margins.

    Each panel can have independent dimensions and margins. Panels flow
    left-to-right and wrap to new rows when they exceed max_width.

    Each panel consists of:
    - Label space (label_left, label_top): reserved area for the panel label
    - Padding (pad_left, pad_top): space for ylabel/xlabel and tick labels
    - Axes area (width, height): the plotting area
    - Margins (left, top, right, bottom): space around the entire panel

    Parameters
    ----------
    max_width : int, optional
        Maximum figure width in pixels (default: 540). Panels wrap to new
        rows when this width would be exceeded.

    Attributes
    ----------
    fig : matplotlib.figure.Figure
        The matplotlib figure object.
    axes : list
        List of matplotlib axes objects in order of creation.

    Examples
    --------
    >>> import cnsplots as cns
    >>> mp = cns.multipanel(max_width=540)
    >>> # Panel with label space and padding for ylabel
    >>> mp.panel(
    ...     "A",
    ...     width=100,
    ...     height=200,
    ...     label_left=10,
    ...     label_top=12,
    ...     pad_left=30,
    ...     margin=(0, 0, 10, 10),
    ... )
    >>> cns.boxplot(...)
    >>> cns.savefig("figure.pdf")

    Notes
    -----
    Panel layout structure::

        +--------------------------------------------------------+
        |                      margin_top                        |
        |  +--------------------------------------------------+  |
        |  |    label_top                                     |  |
        |  |  +--------------------------------------------+  |  |
        |m |  |  pad_top (for title if any)                |  |m |
        |a |l |  +--------------------------------------+  |  |a |
        |r |a |  |                                      |  |  |r |
        |g |b |p |                                      |  |  |g |
        |i |e |a |         axes content area            |  |  |i |
        |n |l |d |         (width x height)             |  |  |n |
        |_ |_ |_ |                                      |  |  |_ |
        |l |l |l |    (ylabel drawn here by mpl)        |  |  |r |
        |e |e |e |                                      |  |  |i |
        |f |f |f |                                      |  |  |g |
        |t |t |t |                                      |  |  |h |
        |  |  |  +--------------------------------------+  |  |t |
        |  |  +--------------------------------------------+  |  |
        |  +--------------------------------------------------+  |
        |                      margin_bottom                     |
        +--------------------------------------------------------+

    The panel label ("A", "B", etc.) is positioned in the label_left space,
    ensuring it appears to the left of the ylabel and axes content.
    """

    def __init__(self, max_width=540):
        self._max_width = max_width
        self._panels = []  # List of panel info dicts
        self.fig = None
        self.axes = []
        self._created_axes = {}
        self._label_texts = {}
        self._labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self._panel_index = 0

        # Track rows for flow layout
        # Each row is a list of panel indices
        self._rows = []
        self._row_heights = []  # Max total height in each row

    def _get_panel_total_size(self, panel):
        """Get the total width and height of a panel including margins."""
        total_width = (
            panel["margin_left"]
            + panel["label_left"]
            + panel.get("pad_left", 0)
            + panel["width"]
            + panel["margin_right"]
        )
        total_height = (
            panel["margin_top"]
            + panel["label_top"]
            + panel.get("pad_top", 0)
            + panel["height"]
            + panel["margin_bottom"]
        )
        return total_width, total_height

    def _get_stacked_height(self, panel_idx):
        """Get total height of a panel plus any panels stacked below it."""
        panel = self._panels[panel_idx]
        _, total_height = self._get_panel_total_size(panel)
        # Add heights of children stacked below
        for p in self._panels:
            if p.get("_below") == panel["label"]:
                _, child_height = self._get_panel_total_size(p)
                total_height += child_height
        return total_height

    def _calculate_layout(self):
        """Calculate row assignments and positions for all panels."""
        self._rows = []
        self._row_heights = []

        current_row = []
        current_row_x = 0
        current_row_max_height = 0

        for idx, panel in enumerate(self._panels):
            # Skip panels that are stacked below another panel
            if panel.get("_below"):
                continue

            total_width, _ = self._get_panel_total_size(panel)
            # Use stacked height (parent + children) for row height
            stacked_height = self._get_stacked_height(idx)

            # Check if panel fits in current row
            if current_row and current_row_x + total_width > self._max_width:
                # Start new row
                self._rows.append(current_row)
                self._row_heights.append(current_row_max_height)
                current_row = [idx]
                current_row_x = total_width
                current_row_max_height = stacked_height
            else:
                # Add to current row
                current_row.append(idx)
                current_row_x += total_width
                current_row_max_height = max(current_row_max_height, stacked_height)

        # Don't forget the last row
        if current_row:
            self._rows.append(current_row)
            self._row_heights.append(current_row_max_height)

    def _get_panel_position(self, panel_idx):
        """Get the x, y position (top-left of axes content area) for a panel."""
        panel = self._panels[panel_idx]

        # Handle panels stacked below another panel
        if panel.get("_below"):
            # Find the parent panel index
            parent_idx = None
            for i, p in enumerate(self._panels):
                if p["label"] == panel["_below"]:
                    parent_idx = i
                    break
            if parent_idx is None:
                return 0, 0

            parent = self._panels[parent_idx]
            parent_x, parent_y = self._get_panel_position(parent_idx)

            # x: align to parent's column (adjust for difference in label_left/pad_left)
            x = (
                parent_x
                - parent.get("pad_left", 0)
                - parent["label_left"]
                + panel["margin_left"]
                + panel["label_left"]
                + panel.get("pad_left", 0)
            )

            # y: below parent's total height
            y = (
                parent_y
                + parent["height"]
                + parent["margin_bottom"]
                + panel["margin_top"]
                + panel["label_top"]
                + panel.get("pad_top", 0)
            )

            return x, y

        # Find which row this panel is in
        row_idx = None
        col_in_row = None
        for r_idx, row in enumerate(self._rows):
            if panel_idx in row:
                row_idx = r_idx
                col_in_row = row.index(panel_idx)
                break

        if row_idx is None:
            return 0, 0

        # Calculate y position (from top of figure)
        y = sum(self._row_heights[:row_idx])

        # Calculate x position
        x = 0
        for i in range(col_in_row):
            prev_idx = self._rows[row_idx][i]
            prev_panel = self._panels[prev_idx]
            x += (
                prev_panel["margin_left"]
                + prev_panel["label_left"]
                + prev_panel.get("pad_left", 0)
                + prev_panel["width"]
                + prev_panel["margin_right"]
            )

        # Add this panel's left margin, label space, and padding
        x += panel["margin_left"] + panel["label_left"] + panel.get("pad_left", 0)
        y += panel["margin_top"] + panel["label_top"] + panel.get("pad_top", 0)

        return x, y

    def _create_or_update_figure(self):
        """Create or update the figure and all axes based on current layout."""
        self._calculate_layout()

        # Calculate total figure size
        fig_height_px = sum(self._row_heights)
        fig_width_px = self._max_width

        # Convert pixels to inches (72 dpi base)
        fig_width = fig_width_px / 72
        fig_height = fig_height_px / 72

        if self.fig is None:
            self.fig = plt.figure(figsize=(fig_width, fig_height), dpi=72 * 2)
        else:
            self.fig.set_size_inches(fig_width, fig_height)

        # Create or update axes for all panels
        for idx, panel in enumerate(self._panels):
            # Skip spacer panels
            if panel.get("_is_spacer"):
                continue

            x, y = self._get_panel_position(idx)
            label = panel["label"]
            pad_left = panel.get("pad_left", 0)
            pad_top = panel.get("pad_top", 0)

            # Convert to figure coordinates (0-1 range)
            # Note: matplotlib uses bottom-left as origin, we use top-left
            left = x / fig_width_px
            bottom = (fig_height_px - y - panel["height"]) / fig_height_px
            ax_width = panel["width"] / fig_width_px
            ax_height = panel["height"] / fig_height_px

            ax = self._created_axes.get(label)
            if ax is None:
                # Create new axes
                ax = self.fig.add_axes([left, bottom, ax_width, ax_height])
                self.axes.append(ax)
                self._created_axes[label] = ax

                # Add panel label in the label space area (before pad_left)
                # Position: label is in label_left space, which is to the left of pad_left
                # x is the left edge of axes, so label_x = x - pad_left - label_left
                label_x_px = x - pad_left - panel["label_left"]
                # Vertically: label is in label_top space, above pad_top
                label_y_px = y - pad_top - panel["label_top"] / 2

                # Convert to figure coordinates
                label_x_fig = label_x_px / fig_width_px
                label_y_fig = (fig_height_px - label_y_px) / fig_height_px

                label_text = self.fig.text(
                    label_x_fig,
                    label_y_fig,
                    label,
                    fontsize=cns.settings.fontsize_title,
                    fontweight="bold",
                    fontname="Arial",
                    va="center",
                    ha="left",
                )
                self._label_texts[label] = label_text
            else:
                # Update existing axes position
                ax.set_position([left, bottom, ax_width, ax_height])

                # Update label position
                label_text = self._label_texts.get(label)
                if label_text is not None:
                    label_x_px = x - pad_left - panel["label_left"]
                    label_y_px = y - pad_top - panel["label_top"] / 2
                    label_x_fig = label_x_px / fig_width_px
                    label_y_fig = (fig_height_px - label_y_px) / fig_height_px
                    label_text.set_position((label_x_fig, label_y_fig))

    def panel(
        self,
        label=None,
        height=150,
        width=150,
        label_left=10,
        label_top=12,
        pad_left=20,
        pad_top=0,
        margin=(10, 0, 0, 20),
        color_cycle=None,
        color_map=None,
        below=None,
    ):
        """
        Add a panel with specified dimensions, label space, padding, and margins.

        Parameters
        ----------
        label : str or None, optional
            Panel label (e.g., "A", "B", "C"). If None, uses automatic
            sequential labeling (A, B, C, ...).
        height : int, optional
            Axes height in pixels (default: 150).
        width : int, optional
            Axes width in pixels (default: 150).
        label_left : int, optional
            Space reserved for the panel label to the left in pixels (default: 10).
            The label is positioned here, outside of pad_left.
        label_top : int, optional
            Space reserved for the panel label above in pixels (default: 12).
            The label is positioned here, outside of pad_top.
        pad_left : int, optional
            Padding between label and axes for ylabel/yticks in pixels (default: 20).
            This space accommodates matplotlib's ylabel which is drawn outside
            the axes bounding box.
        pad_top : int, optional
            Padding between label and axes for title in pixels (default: 0).
            Set this if you have axes titles that need space.
        margin : tuple of 4 ints, optional
            Margins as (left, top, right, bottom) in pixels (default: (10,0,0,20)).
            These are additional space around the complete panel.
        color_cycle : str, optional
            Color palette name for this panel. If None, uses cns.settings.palette_qual.
        color_map : str, optional
            Colormap name for this panel. If None, uses cns.settings.palette_seq.
        below : str, optional
            Label of another panel to stack this panel below (e.g., "D").
            The panel is positioned directly below the specified panel
            instead of flowing in the normal left-to-right layout.

        Returns
        -------
        ax : matplotlib.axes.Axes
            The matplotlib axes object for plotting.

        Examples
        --------
        >>> mp = cns.multipanel(max_width=400)
        >>> # Panel with ylabel - use pad_left for ylabel space
        >>> ax = mp.panel(
        ...     "A",
        ...     width=100,
        ...     height=150,
        ...     label_left=10,
        ...     label_top=12,
        ...     pad_left=35,
        ...     margin=(0, 0, 10, 20),
        ... )
        >>> cns.boxplot(data=df, x="group", y="value")
        >>> plt.ylabel("Values")  # ylabel appears in pad_left space
        >>>
        >>> # Panel without ylabel - less padding needed
        >>> ax = mp.panel(
        ...     "B",
        ...     width=100,
        ...     height=150,
        ...     label_left=10,
        ...     label_top=12,
        ...     pad_left=5,
        ...     margin=(0, 0, 10, 20),
        ... )
        >>> cns.barplot(data=df, x="category", y="count")

        Notes
        -----
        Total panel dimensions are calculated as:
        - Total width = margin_left + label_left + pad_left + width + margin_right
        - Total height = margin_top + label_top + pad_top + height + margin_bottom

        The panel label ("A", "B", etc.) is positioned in the label_left/label_top
        space, which is outside the pad_left/pad_top space where ylabel/title appear.
        This ensures the panel label is always the leftmost/topmost element.
        """
        if color_cycle is None:
            color_cycle = cns.settings.palette_qual
        if color_map is None:
            color_map = cns.settings.palette_seq
        cns.setup_matplotlib(color_cycle, color_map)

        if label is None:
            label = self._labels[self._panel_index]

        # Parse margin tuple
        margin_left, margin_top, margin_right, margin_bottom = margin

        # Store panel info
        panel_info = {
            "label": label,
            "width": width,
            "height": height,
            "label_left": label_left,
            "label_top": label_top,
            "pad_left": pad_left,
            "pad_top": pad_top,
            "margin_left": margin_left,
            "margin_top": margin_top,
            "margin_right": margin_right,
            "margin_bottom": margin_bottom,
            "_below": below,
        }
        self._panels.append(panel_info)

        # Create or update figure
        self._create_or_update_figure()

        self._panel_index += 1

        # Set this axes as current and return it
        ax = self._created_axes.get(label)
        if ax is not None:
            plt.sca(ax)
        return ax

    def get_axes(self, label):
        """
        Get a previously created axes by its label.

        Parameters
        ----------
        label : str
            The label of the panel to retrieve (e.g., "A", "B").

        Returns
        -------
        ax : matplotlib.axes.Axes or None
            The matplotlib axes object, or None if not found.
        """
        return self._created_axes.get(label)

    def newline(self):
        """
        Force the next panel to start on a new row.

        This is useful when you want to manually control row breaks
        instead of relying on the automatic wrapping behavior.

        Examples
        --------
        >>> mp = cns.multipanel(max_width=400)
        >>> mp.panel("A", width=100, height=100)
        >>> mp.newline()  # Force B to start on new row
        >>> mp.panel("B", width=100, height=100)
        """
        # Add a zero-width panel to force wrapping
        # We do this by adding a spacer panel that takes up remaining width
        if self._panels:
            self._calculate_layout()
            if self._rows:
                # Calculate remaining width in current row
                current_row = self._rows[-1]
                used_width = 0
                for idx in current_row:
                    p = self._panels[idx]
                    used_width += (
                        p["margin_left"]
                        + p.get("label_left", 0)
                        + p.get("pad_left", 0)
                        + p["width"]
                        + p["margin_right"]
                    )
                remaining = self._max_width - used_width
                if remaining > 0:
                    # Add invisible spacer
                    self._panels.append(
                        {
                            "label": f"_spacer_{len(self._panels)}",
                            "width": 0,
                            "height": 0,
                            "label_left": 0,
                            "label_top": 0,
                            "pad_left": 0,
                            "pad_top": 0,
                            "margin_left": 0,
                            "margin_top": 0,
                            "margin_right": remaining,
                            "margin_bottom": 0,
                            "_is_spacer": True,
                        }
                    )
