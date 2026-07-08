"""Snow-drought type classification helpers (notebook 05).

These are the reusable building blocks for the two-stage classification:
parsing drought-year lists, within-group standardization, and mapping k-means
centroids to physical drought-type names. The k-means orchestration itself
stays in the notebook.
"""

from __future__ import annotations

import ast

import numpy as np
import pandas as pd


def normalize_years(years):
    """Convert list-like, string, scalar, or missing drought-year values to a sorted list of ints."""
    if years is None or (isinstance(years, float) and np.isnan(years)):
        return []

    if isinstance(years, str):
        years = years.strip()
        if years in ["", "[]", "nan", "NaN", "None"]:
            return []
        try:
            parsed = ast.literal_eval(years)
            years = parsed
        except (ValueError, SyntaxError):
            # fallback for strings like "1982, 1995, 2001"
            years = years.replace(";", ",").split(",")

    if isinstance(years, (list, tuple, set, np.ndarray, pd.Series)):
        out = []
        for y in years:
            if pd.notna(y):
                try:
                    out.append(int(float(y)))
                except ValueError:
                    pass
        return sorted(set(out))

    try:
        return [int(float(years))]
    except (TypeError, ValueError):
        return []


def zscore_by_group(df, group_col, value_col, output_col):
    """Add ``output_col`` = within-``group_col`` z-score of ``value_col``.

    Groups with zero or undefined standard deviation are set to zeros.
    """
    def zscore(x):
        std = x.std(ddof=1)
        if pd.isna(std) or std == 0:
            return pd.Series(np.zeros(len(x)), index=x.index)
        return (x - x.mean()) / std

    df[output_col] = df.groupby(group_col)[value_col].transform(zscore)
    return df


def assign_cluster_names_from_centers(centers_df):
    """Map k-means centroids to physical snow-drought type names.

    Expects a DataFrame with columns ``cluster``, ``Avg_SWE_P_ratio_z`` and
    ``cum_P_anomaly_z``. Returns ``[cluster, cluster_name]``. Logic:

    - Warm & Dry: smallest combined (SWE/P + precip-anomaly) score.
    - Of the remaining two: lower SWE/P = Warm, lower precip anomaly = Dry.

    Avoids hard-coding cluster numbers, which change between datasets.
    """
    centers_df = centers_df.copy()
    centers_df["cluster_name"] = None

    if len(centers_df) == 3:
        # Warm & Dry should be the cluster with the smallest combined score:
        # low SWE/P and low precipitation anomaly.
        centers_df["warm_dry_score"] = (
            centers_df["Avg_SWE_P_ratio_z"] + centers_df["cum_P_anomaly_z"]
        )
        warm_dry_cluster = centers_df.loc[centers_df["warm_dry_score"].idxmin(), "cluster"]
        centers_df.loc[centers_df["cluster"] == warm_dry_cluster, "cluster_name"] = "Warm & Dry"

        remaining = centers_df[centers_df["cluster_name"].isna()].copy()

        # Of the remaining two clusters:
        # lower SWE/P = Warm, lower precipitation anomaly = Dry.
        warm_cluster = remaining.loc[remaining["Avg_SWE_P_ratio_z"].idxmin(), "cluster"]
        dry_cluster = remaining.loc[remaining["cum_P_anomaly_z"].idxmin(), "cluster"]

        # If both rules choose the same cluster, use the opposite cluster for Dry.
        if warm_cluster == dry_cluster:
            other_clusters = remaining.loc[remaining["cluster"] != warm_cluster, "cluster"].tolist()
            dry_cluster = other_clusters[0]

        centers_df.loc[centers_df["cluster"] == warm_cluster, "cluster_name"] = "Warm"
        centers_df.loc[centers_df["cluster"] == dry_cluster, "cluster_name"] = "Dry"

    else:
        # Fallback for tiny datasets with fewer than 3 clusters.
        # Label each cluster using simple physical rules around the centroid signs.
        for idx, row in centers_df.iterrows():
            low_swep = row["Avg_SWE_P_ratio_z"] <= 0
            low_p = row["cum_P_anomaly_z"] <= 0
            if low_swep and low_p:
                label = "Warm & Dry"
            elif low_swep and not low_p:
                label = "Warm"
            elif not low_swep and low_p:
                label = "Dry"
            else:
                # Drought years should rarely fall here; choose least misleading label.
                label = "Warm"
            centers_df.loc[idx, "cluster_name"] = label

    return centers_df[["cluster", "cluster_name"]]
