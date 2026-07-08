"""Seasonal aggregation helpers shared by the SWEI and SPI pipelines.

The SWEI (notebook 03) and SPI (notebook 04) pipelines performed the same
daily->monthly integration and rolling k-month integration, differing only in
the value column. Those steps live here as generic helpers, with thin
``*_swe`` / ``*_precipitation`` wrappers that preserve the original call sites.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import SEASON_START_MONTH


def select_seasonal_data(ts, start_month, end_month, min_year, max_year):
    """Map a timestamp to its seasonal (water) year, or NaN if out of range.

    Months from ``start_month`` onward belong to the year they fall in; months
    up to ``end_month`` belong to the previous year. Anything outside the
    ``[min_year, max_year]`` window (or the season) returns ``np.nan``.
    """
    month = ts.month
    year = ts.year
    if month >= start_month:
        seasonal_year = year
    elif month <= end_month:
        seasonal_year = year - 1
    else:
        return np.nan
    return seasonal_year if (min_year <= seasonal_year <= max_year) else np.nan


def extract_grid_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Extract per-Grid static metadata (lon, lat, elev_class) indexed by Grid_ID."""
    return (
        df[["Grid_ID", "lon", "lat", "elev_class"]]
        .drop_duplicates("Grid_ID")
        .set_index("Grid_ID")
    )


def daily_to_monthly(
    df: pd.DataFrame,
    value_col: str,
    out_col: str,
    season_start_month: int = SEASON_START_MONTH,
) -> pd.DataFrame:
    """Sum a daily value column to monthly totals and (re)compute Seasonal_Year.

    Months >= ``season_start_month`` belong to that calendar year, earlier
    months belong to the previous year (an Oct-Sep water year by default).
    """
    out = df.copy()
    out["time"] = pd.to_datetime(out["time"])

    monthly = (
        out
        .groupby(
            ["Grid_ID", pd.Grouper(key="time", freq="MS")],
            as_index=False,
        )
        .agg(**{out_col: (value_col, "sum")})
    )

    monthly["Seasonal_Year"] = np.where(
        monthly["time"].dt.month >= season_start_month,
        monthly["time"].dt.year,
        monthly["time"].dt.year - 1,
    )

    return monthly


def rolling_integrated_by_season(
    monthly_df: pd.DataFrame,
    value_col: str,
    out_col: str,
    window_months: int,
) -> pd.DataFrame:
    """Rolling k-month sum of ``value_col`` within each Seasonal_Year.

    * Rolling windows do NOT cross Seasonal_Year boundaries.
    * The first (k-1) months of each season are dropped.
    * Works for any window (3, 6, 8, ...).
    """
    out = monthly_df.copy()
    out = out.sort_values(["Grid_ID", "Seasonal_Year", "time"])

    out[out_col] = (
        out
        .groupby(["Grid_ID", "Seasonal_Year"])[value_col]
        .rolling(window=window_months, min_periods=window_months)
        .sum()
        .reset_index(level=[0, 1], drop=True)
    )

    return out.dropna(subset=[out_col])


# --- Named wrappers preserving the original notebook call signatures -----------
def daily_to_monthly_swe(df: pd.DataFrame) -> pd.DataFrame:
    """Daily perturbed SWE -> monthly integrated SWE (column ``SWE_monthly``)."""
    return daily_to_monthly(df, value_col="SWE_perturbed", out_col="SWE_monthly")


def daily_to_monthly_precipitation(df: pd.DataFrame) -> pd.DataFrame:
    """Daily precipitation -> monthly integrated precip (``Precipitation_monthly``)."""
    return daily_to_monthly(
        df, value_col="Precipitation", out_col="Precipitation_monthly"
    )


def rolling_integrated_swe_by_season(
    monthly_df: pd.DataFrame, window_months: int
) -> pd.DataFrame:
    """Rolling k-month integrated SWE (column ``SWE_{window_months}mo``)."""
    return rolling_integrated_by_season(
        monthly_df,
        value_col="SWE_monthly",
        out_col=f"SWE_{window_months}mo",
        window_months=window_months,
    )


def rolling_integrated_precipitation_by_season(
    monthly_df: pd.DataFrame, window_months: int
) -> pd.DataFrame:
    """Rolling k-month integrated precip (``Precipitation_{window_months}mo``)."""
    return rolling_integrated_by_season(
        monthly_df,
        value_col="Precipitation_monthly",
        out_col=f"Precipitation_{window_months}mo",
        window_months=window_months,
    )
