import matplotlib.pyplot as plt


def phyloplot():
    import io

    import Bio.Phylo

    tree = Bio.Phylo.read(io.StringIO(adata.uns["tree"]), "newick")
    cell_ids = []
    for a in tree.get_terminals():
        cell_ids.append(a.name)
    adata = adata[cell_ids]

    fig = plt.gcf()
    axes = fig.subplots(
        nrows=1,
        ncols=2,
        sharey=True,
        width_ratios=[0.3, 0.7],
        squeeze=False,
        gridspec_kw=dict(hspace=0, wspace=-0.1),
    )[0]
    axes[0].set_axis_off()
    axes[1].set_axis_off()
    with plt.rc_context({"lines.linewidth": 0.5}):
        Bio.Phylo.draw(tree, label_func=lambda a: "", axes=axes[0], do_show=False)
    axes[1].imshow(
        adata.to_df(layer="trisicell_input"), aspect="auto", interpolation="none"
    )
