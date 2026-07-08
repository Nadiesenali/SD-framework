"""Standardized drought indices: SWEI (snow) and SPI (precipitation).

``compute_swei`` and ``spi_pipeline`` are kept as separate entry points (their
standardization differs: SWEI uses a Gringorten plotting position, SPI a mixed
gamma fit), but both reuse the seasonal aggregation helpers in
:mod:`soyini.seasonal`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import gamma, norm

from .seasonal import (
    daily_to_monthly_precipitation,
    daily_to_monthly_swe,
    extract_grid_metadata,
    rolling_integrated_precipitation_by_season,
    rolling_integrated_swe_by_season,
)


# --- SWEI ----------------------------------------------------------------------
def perturb_daily_swe_zeros(
    df: pd.DataFrame,
    swe_col: str = "SWE",
    id_col: str = "Grid_ID",
    seed: int = 42,
    perturb_factor: float = 0.01,
) -> pd.DataFrame:
    """Perturb exact daily SWE zeros before integration.

    Keeps ``id_col`` as a normal column.
    """
    out = df.copy().reset_index(drop=True)

    if id_col not in out.columns:
        raise KeyError(f"{id_col} is not in columns. Columns are: {out.columns.tolist()}")

    out[swe_col] = out[swe_col].astype(float)

    rng = np.random.default_rng(seed)

    for sid, idx in out.groupby(id_col).groups.items():

        vals = out.loc[idx, swe_col]

        valid = vals.notna()
        zero_idx = vals[valid & (vals == 0)].index
        positive_vals = vals[valid & (vals > 0)]

        if len(zero_idx) == 0:
            continue

        if positive_vals.empty:
            continue

        min_positive = positive_vals.min()

        out.loc[zero_idx, swe_col] = (
            rng.uniform(low=1e-6, high=1e-5, size=len(zero_idx))
            * min_positive
            * perturb_factor
        )
    return out


def gringorten_probabilities(x: np.ndarray) -> np.ndarray:
    """Gringorten plotting position with NaN handling, average ties and clipping."""
    x = np.asarray(x, float)
    out = np.full_like(x, np.nan)

    mask = ~np.isnan(x)
    xv = x[mask]

    if xv.size == 0:
        return out

    # ranks with average ties
    order = np.argsort(xv, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(xv) + 1)

    uvals, inv, cnt = np.unique(xv, return_inverse=True, return_counts=True)
    for i, c in enumerate(cnt):
        if c > 1:
            idx = np.where(inv == i)[0]
            ranks[idx] = ranks[idx].mean()

    N = float(len(xv))
    p = (ranks - 0.44) / (N + 0.12)
    p = np.clip(p, 1e-12, 1 - 1e-12)

    out[mask] = p
    return out


def compute_swei_for_grid(df: pd.DataFrame, swe_col: str) -> pd.DataFrame:
    """Compute SWEI for ONE station/grid using calendar-month standardization."""
    out = df.copy()
    out["month"] = out["time"].dt.month

    pvals = np.full(len(out), np.nan)
    zvals = np.full(len(out), np.nan)

    for m in range(1, 13):
        idx = out["month"] == m
        vals = out.loc[idx, swe_col]

        if vals.notna().sum() == 0:
            continue

        p = gringorten_probabilities(vals.values)
        z = norm.ppf(p)

        pvals[idx] = p
        zvals[idx] = z

    out["Gringorten_p"] = pvals
    out["SWEI"] = zvals

    return out


def compute_swei(
    df: pd.DataFrame,
    window_months: int = 3,
    seed: int = 42,
) -> pd.DataFrame:
    """End-to-end SWEI calculation.

    Applies daily zero perturbation before monthly and rolling integration,
    then a per-grid Gringorten/normal standardization.
    """
    # 0. Extract static metadata
    grid_meta = extract_grid_metadata(df)

    # 1. Prepare daily data
    daily = df.copy()
    daily["time"] = pd.to_datetime(daily["time"])

    # 2. Create perturbed SWE column
    daily["SWE_perturbed"] = daily["SWE"]

    daily = perturb_daily_swe_zeros(
        daily,
        swe_col="SWE_perturbed",
        id_col="Grid_ID",
        seed=seed,
        perturb_factor=0.01,
    )

    # 3. Daily -> monthly integrated SWE
    monthly = daily_to_monthly_swe(daily)

    # 4. Rolling monthly integration
    integ = rolling_integrated_swe_by_season(monthly, window_months)

    # 5. Compute SWEI per station/grid
    swei = (
        integ
        .groupby("Grid_ID", group_keys=False)
        .apply(
            lambda g: compute_swei_for_grid(
                g,
                swe_col=f"SWE_{window_months}mo",
            )
        )
        .reset_index(drop=True)
    )
    if "Grid_ID" not in swei.columns:
        swei["Grid_ID"] = integ["Grid_ID"].values
    print(swei.columns.tolist())
    print(swei.head())

    # 6. Reattach static metadata
    swei = swei.reset_index()

    swei = swei.merge(
        grid_meta.reset_index(),
        on="Grid_ID",
        how="left",
    )

    return swei


# --- SPI -----------------------------------------------------------------------
def calculate_spi(series: pd.Series, min_samples: int = 20) -> pd.Series:
    """Calculate SPI using a mixed Gamma distribution (handles zero precip)."""
    x = series.values

    # Probability of zero precipitation
    q = np.mean(x == 0)

    pos = x[x > 0]
    if len(pos) < min_samples:
        return pd.Series(np.nan, index=series.index)

    shape, loc, scale = gamma.fit(pos, floc=0)

    G = gamma.cdf(x, shape, loc=loc, scale=scale)
    H = q + (1 - q) * G

    H = np.clip(H, 1e-6, 1 - 1e-6)

    spi = norm.ppf(H)

    return pd.Series(spi, index=series.index)


def compute_spi_for_grids(precip_df: pd.DataFrame, precip_col: str) -> pd.DataFrame:
    """Compute SPI per grid, standardizing within each calendar month."""
    out = []

    for Grid_ID, gdf in precip_df.groupby("Grid_ID"):
        gdf = gdf.sort_values("time")

        for month in range(1, 13):
            mask = gdf["time"].dt.month == month
            spi_series = calculate_spi(gdf.loc[mask, precip_col])

            gdf.loc[mask, "SPI"] = spi_series

        gdf["Grid_ID"] = Grid_ID
        out.append(gdf)

    return pd.concat(out).sort_values(["Grid_ID", "time"])


def spi_pipeline(daily_df: pd.DataFrame, window_months: int) -> pd.DataFrame:
    """End-to-end SPI calculation from a daily precipitation table."""
    # 1. Metadata
    grid_meta = extract_grid_metadata(daily_df)

    # 2. Daily -> Monthly
    monthly = daily_to_monthly_precipitation(daily_df)

    # 3. Rolling integrated precipitation
    rolled = rolling_integrated_precipitation_by_season(
        monthly,
        window_months=window_months,
    )

    precip_col = f"Precipitation_{window_months}mo"

    # 4. SPI calculation
    spi = compute_spi_for_grids(rolled, precip_col)

    # 5. Join metadata
    final = (
        spi
        .merge(grid_meta, left_on="Grid_ID", right_index=True, how="left")
        .sort_values(["Grid_ID", "time"])
    )
    final["month"] = final["time"].dt.month.astype("int32")

    return final
