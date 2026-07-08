"""Reusable plots for the SOYINI framework.

Extracts the repeated matplotlib setup from notebooks 03/04 (SWEI/SPI seasonal
heatmaps) and 05 (classification scatter + heatmap). Each function optionally
saves to ``out_file`` and returns the Matplotlib ``Figure``.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap

from .constants import (
    DROUGHT_TYPE_COLORS_HEATMAP,
    DROUGHT_TYPE_COLORS_SCATTER,
    DROUGHT_TYPE_TO_VALUE,
    ELEV_ORDER_ASC,
    ELEV_ORDER_DESC,
)


def plot_index_heatmap(
    avg_df,
    value_col,
    title,
    out_file=None,
    elev_order=ELEV_ORDER_DESC,
    cbar_label="Standardized anomaly (z-score)",
):
    """Seasonal SWEI/SPI heatmap (elevation x seasonal year).

    ``avg_df`` must have columns ``elev_class``, ``Seasonal_Year`` and
    ``value_col`` (e.g. ``Avg_SWEI_8mo`` or ``Avg_SPI_8mo``).
    """
    mat = avg_df.pivot_table(
        index="elev_class",
        columns="Seasonal_Year",
        values=value_col,
    ).reindex(elev_order)

    fig, axes = plt.subplots(figsize=(20, 10))

    im1 = axes.imshow(mat, cmap="RdBu_r", aspect="auto")

    axes.set_title(title, fontsize=20, fontweight="bold")
    axes.set_ylabel("Elevation (m)", fontsize=18, fontweight="bold")

    axes.set_yticks(np.arange(len(mat.index)))
    axes.set_yticklabels(mat.index, fontsize=18, fontweight="bold")

    years = mat.columns.to_numpy()
    step = max(1, len(years) // 12)
    axes.set_xticks(np.arange(len(years))[::step])
    axes.set_xticklabels(years[::step], fontsize=18, fontweight="bold")

    fig.subplots_adjust(right=0.86)
    cbar_ax = fig.add_axes([0.88, 0.18, 0.02, 0.64])
    cbar = fig.colorbar(im1, cax=cbar_ax)
    cbar.set_label(cbar_label, fontsize=20, fontweight="bold")

    if out_file is not None:
        fig.savefig(out_file, dpi=300, bbox_inches="tight")
    return fig


def plot_classification_scatter(
    classification_all_years,
    out_file=None,
    elev_order=ELEV_ORDER_ASC,
    cluster_colors=None,
):
    """Per-elevation scatter of drought years in (Cum P anomaly, SWE/P) space."""
    if cluster_colors is None:
        cluster_colors = DROUGHT_TYPE_COLORS_SCATTER

    elevations_ordered = [
        e for e in elev_order if e in classification_all_years["elev_class"].unique()
    ]

    ncols = 3
    nrows = int(np.ceil(len(elevations_ordered) / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(16, 5 * nrows), sharex=True, sharey=True
    )
    axes = np.atleast_1d(axes).flatten()

    for i, elev in enumerate(elevations_ordered):
        ax = axes[i]
        elev_all = classification_all_years[
            classification_all_years["elev_class"] == elev
        ]

        # Plot non-drought years lightly as background.
        normal_points = elev_all[elev_all["cluster_name"] == "Normal"]
        ax.scatter(
            normal_points["Avg_Cum_P_anomaly"],
            normal_points["Avg_SWE_P_ratio"],
            color=cluster_colors["Normal"],
            alpha=0.35,
            label="Normal" if i == 0 else "",
        )

        # Plot classified drought years on top.
        for cname in ["Dry", "Warm & Dry", "Warm"]:
            pts = elev_all[elev_all["cluster_name"] == cname]
            ax.scatter(
                pts["Avg_Cum_P_anomaly"],
                pts["Avg_SWE_P_ratio"],
                color=cluster_colors[cname],
                alpha=0.9,
                edgecolor="black",
                linewidth=0.3,
                label=cname if i == 0 else "",
            )

        ax.axvline(0, color="black", linewidth=1.2)
        ax.set_title(elev, fontsize=16, fontweight="bold")
        ax.set_xlabel("Cumulative precipitation anomaly (mm)", fontsize=13)
        ax.set_ylabel("SWE/P ratio", fontsize=13)
        ax.grid(True, alpha=0.3)

    for j in range(len(elevations_ordered), len(axes)):
        axes[j].axis("off")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Snow drought type", loc="upper right", fontsize=12)
    plt.tight_layout(rect=[0, 0, 0.9, 1])

    if out_file is not None:
        fig.savefig(out_file, dpi=1000, bbox_inches="tight")
    return fig


def plot_classification_heatmap(
    classification_all_years,
    out_file=None,
    elev_order=ELEV_ORDER_ASC,
    colors=None,
    type_to_value=None,
):
    """Final snow-drought classification heatmap (elevation x seasonal year)."""
    if colors is None:
        colors = DROUGHT_TYPE_COLORS_HEATMAP
    if type_to_value is None:
        type_to_value = DROUGHT_TYPE_TO_VALUE

    plot_df = classification_all_years.copy()
    plot_df["type_value"] = plot_df["cluster_name"].map(type_to_value)

    all_years = sorted(plot_df["Seasonal_Year"].dropna().astype(int).unique())
    elevations_ordered = [e for e in elev_order if e in plot_df["elev_class"].unique()]

    heatmap_data = np.full((len(elevations_ordered), len(all_years)), np.nan)
    for i, elev in enumerate(elevations_ordered):
        elev_df = plot_df[plot_df["elev_class"] == elev]
        year_to_value = dict(zip(elev_df["Seasonal_Year"].astype(int), elev_df["type_value"]))
        for j, year in enumerate(all_years):
            heatmap_data[i, j] = year_to_value.get(year, np.nan)

    cmap = ListedColormap([
        colors["Dry"],
        colors["Warm & Dry"],
        colors["Warm"],
        colors["Normal"],
    ])
    boundary_norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5, 4.5], cmap.N)

    fig, ax = plt.subplots(figsize=(16, 6))
    im = ax.imshow(heatmap_data, aspect="auto", cmap=cmap, norm=boundary_norm)

    # X-axis ticks every 5 years
    all_years_arr = np.array(all_years)
    tick_years = np.arange(all_years_arr.min(), all_years_arr.max() + 1, 5)
    tick_pos = [np.where(all_years_arr == y)[0][0] for y in tick_years if y in all_years_arr]
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(
        [str(y) for y in tick_years if y in all_years_arr], fontsize=12, fontweight="bold"
    )

    ax.set_yticks(np.arange(len(elevations_ordered)))
    ax.set_yticklabels(elevations_ordered, fontsize=12, fontweight="bold")
    ax.invert_yaxis()

    ax.set_xlabel("Seasonal year", fontsize=16, fontweight="bold")
    ax.set_ylabel("Elevation class", fontsize=16, fontweight="bold")

    # Grid lines between cells
    ax.set_xticks(np.arange(-0.5, len(all_years), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(elevations_ordered), 1), minor=True)
    ax.grid(which="minor", color="black", linestyle="-", linewidth=0.25)
    ax.tick_params(which="minor", bottom=False, left=False)

    cbar = fig.colorbar(im, ax=ax, ticks=[1, 2, 3, 4], pad=0.02)
    cbar.set_ticklabels(["Dry", "Warm & Dry", "Warm", "Normal"], fontsize=12, fontweight="bold")
    cbar.set_label("Snow drought type", fontsize=14, fontweight="bold")

    plt.tight_layout()

    if out_file is not None:
        fig.savefig(out_file, dpi=1000, bbox_inches="tight")
    return fig
