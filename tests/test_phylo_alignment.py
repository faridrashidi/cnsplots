from __future__ import annotations

import io

import anndata as ad
import Bio.Phylo
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import LineCollection, QuadMesh

import cnsplots as cns


@pytest.mark.parametrize(
    "newick",
    [
        "((cell3:1.3,cell1:2.4)95:0.7,(cell4:3.6,cell2:4.8):0.9);",
        "(((cell2:1.1,cell4:2.3):0.4,cell1:3.7):0.5,cell3:5.3);",
        "(cell4:1.2,cell2:2.4,cell3:3.6,cell1:4.8);",
    ],
    ids=["balanced", "ladder", "star"],
)
@pytest.mark.parametrize("explicit_axes", [False, True], ids=["current", "host"])
def test_phylo_leaves_align_with_their_heatmap_rows(
    newick: str, explicit_axes: bool
) -> None:
    adata = ad.AnnData(2 * np.eye(4))
    adata.obs_names = ["cell1", "cell2", "cell3", "cell4"]
    adata.obs["group"] = ["B", "A", "C", "A"]
    adata.layers["trisicell_output"] = np.eye(4)
    adata.uns["tree"] = newick
    adata = adata[["cell4", "cell1", "cell2", "cell3"]].copy()
    original = adata.copy()
    tree = Bio.Phylo.read(io.StringIO(newick), "newick")
    terminals = tree.get_terminals()
    terminal_names = [terminal.name for terminal in terminals]
    depths = tree.depths()

    fig = cns.figure(8, 4, unit="in")
    if explicit_axes:
        host_ax, other_ax = fig.subplots(1, 2)
        plt.sca(other_ax)
        heatmap_ax = cns.phyloplot(adata, ax=host_ax)
        assert heatmap_ax is host_ax
        assert not other_ax.collections
    else:
        host_ax = fig.subplots()
        heatmap_ax = cns.phyloplot(adata)
        assert heatmap_ax is host_ax

    tree_ax = next(
        ax
        for ax in fig.axes
        if any(isinstance(artist, LineCollection) for artist in ax.collections)
    )
    mutation_mesh = next(
        artist for artist in heatmap_ax.collections if isinstance(artist, QuadMesh)
    )
    group_meshes = [
        artist
        for ax in fig.axes
        if ax is not heatmap_ax
        for artist in ax.collections
        if isinstance(artist, QuadMesh)
        and np.asarray(artist.get_array()).shape == (4, 1)
    ]
    assert len(group_meshes) == 2
    ordered = original[terminal_names]
    np.testing.assert_array_equal(
        mutation_mesh.get_array(), ordered.layers["trisicell_output"]
    )
    expected_groups = ordered.obs["group"].map({"A": 0, "B": 1, "C": 2})
    for mesh in group_meshes:
        np.testing.assert_array_equal(
            np.asarray(mesh.get_array())[:, 0], expected_groups
        )

    horizontal_branches = [
        (artist, segment)
        for artist in tree_ax.collections
        if isinstance(artist, LineCollection)
        for segment in artist.get_segments()
        if segment[0, 1] == segment[1, 1]
    ]
    np.testing.assert_allclose(
        sorted(segment[1, 0] - segment[0, 0] for _, segment in horizontal_branches),
        sorted(clade.branch_length or 0 for clade in tree.find_clades()),
    )
    for size in [(8, 4), (10, 6)]:
        fig.set_size_inches(*size)
        fig.canvas.draw()
        for row, terminal in enumerate(terminals):
            # Unique terminal depths identify named leaves from rendered branches.
            leaf_branches = [
                (artist, segment)
                for artist, segment in horizontal_branches
                if np.isclose(segment[1, 0], depths[terminal])
            ]
            assert len(leaf_branches) == 1
            artist, segment = leaf_branches[0]
            leaf_y = artist.get_transform().transform(segment[1])[1]
            for mesh in [mutation_mesh, *group_meshes]:
                coordinates = np.asarray(mesh.get_coordinates())
                center = coordinates[row : row + 2, :2].mean(axis=(0, 1))
                row_y = mesh.get_transform().transform(center)[1]
                assert leaf_y == pytest.approx(row_y, abs=1e-7), terminal.name
        for clade in tree.find_clades():
            if clade.confidence is None:
                continue
            label = next(text for text in tree_ax.texts if text.get_text() == "95")
            artist, segment = next(
                (artist, segment)
                for artist, segment in horizontal_branches
                if np.isclose(segment[1, 0], depths[clade])
            )
            label_y = label.get_transform().transform(label.get_position())[1]
            branch_y = artist.get_transform().transform(segment.mean(axis=0))[1]
            assert label_y == pytest.approx(branch_y, abs=1e-7)

    np.testing.assert_array_equal(adata.X, original.X)
    np.testing.assert_array_equal(
        adata.layers["trisicell_output"], original.layers["trisicell_output"]
    )
    pd.testing.assert_frame_equal(adata.obs, original.obs)
    pd.testing.assert_frame_equal(adata.var, original.var)
    assert adata.uns == original.uns
