"""Smoke + sanity tests for the soyini package.

The full pipeline can't run end-to-end here (the CaSR data tree isn't in the
repo), so these tests exercise every moved function on small synthetic data and
check invariants, plus a couple of exact-value checks for the pure helpers.
"""

import numpy as np
import pandas as pd

from soyini import (
    classification,
    config,
    constants,
    indices,
    plotting,
    seasonal,
)


def _synthetic_daily(n_grids=4, seed=0):
    """Daily SWE + precipitation over two seasonal years for a few grids."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2000-10-01", "2002-05-31", freq="D")
    rows = []
    elev_classes = constants.ELEV_ORDER_ASC
    for gid in range(1, n_grids + 1):
        elev = elev_classes[gid % len(elev_classes)]
        swe = np.clip(rng.normal(50, 20, len(dates)), 0, None)
        swe[rng.random(len(dates)) < 0.3] = 0.0  # inject exact zeros
        precip = np.clip(rng.normal(2, 2, len(dates)), 0, None)
        rows.append(pd.DataFrame({
            "Grid_ID": gid,
            "time": dates,
            "lat": 50.0 + gid * 0.1,
            "lon": -114.0 - gid * 0.1,
            "elev_class": elev,
            "SWE": swe,
            "Precipitation": precip,
        }))
    return pd.concat(rows, ignore_index=True)


# --- pure helpers --------------------------------------------------------------
def test_gringorten_bounds_and_monotonic():
    x = np.array([5.0, 1.0, 3.0, np.nan, 3.0])
    p = indices.gringorten_probabilities(x)
    assert np.isnan(p[3])
    valid = p[~np.isnan(p)]
    assert np.all(valid > 0) and np.all(valid < 1)
    # ties (the two 3.0s) get equal probability
    assert p[2] == p[4]
    # larger value -> larger plotting position
    assert p[0] > p[1]


def test_zscore_by_group_zero_mean():
    df = pd.DataFrame({"g": ["a", "a", "a", "b", "b"], "v": [1.0, 2.0, 3.0, 10.0, 10.0]})
    out = classification.zscore_by_group(df.copy(), "g", "v", "z")
    a = out.loc[out.g == "a", "z"]
    assert abs(a.mean()) < 1e-9
    # constant group -> zeros (std == 0 branch)
    assert (out.loc[out.g == "b", "z"] == 0).all()


def test_normalize_years_variants():
    assert classification.normalize_years("[1982, 1995]") == [1982, 1995]
    assert classification.normalize_years("1982, 1995; 2001") == [1982, 1995, 2001]
    assert classification.normalize_years([1990.0, 1990, np.nan]) == [1990]
    assert classification.normalize_years(np.nan) == []
    assert classification.normalize_years("") == []


def test_cluster_naming_three():
    centers = pd.DataFrame({
        "cluster": [0, 1, 2],
        "Avg_SWE_P_ratio_z": [-1.0, 1.0, -0.5],
        "cum_P_anomaly_z": [-1.0, 0.5, 0.8],
    })
    names = classification.assign_cluster_names_from_centers(centers)
    mapping = dict(zip(names.cluster, names.cluster_name))
    assert set(mapping.values()) == {"Warm", "Dry", "Warm & Dry"}
    assert mapping[0] == "Warm & Dry"  # smallest combined score


# --- seasonal helpers ----------------------------------------------------------
def test_select_seasonal_data():
    f = seasonal.select_seasonal_data
    assert f(pd.Timestamp("2001-11-15"), 10, 5, 1980, 2020) == 2001
    assert f(pd.Timestamp("2002-02-15"), 10, 5, 1980, 2020) == 2001
    assert np.isnan(f(pd.Timestamp("2001-07-15"), 10, 5, 1980, 2020))  # out of season
    assert np.isnan(f(pd.Timestamp("1975-11-15"), 10, 5, 1980, 2020))  # out of range


def test_rolling_wrappers_match_generic():
    daily = _synthetic_daily()
    daily["SWE_perturbed"] = daily["SWE"]
    monthly = seasonal.daily_to_monthly_swe(daily)
    named = seasonal.rolling_integrated_swe_by_season(monthly, 3)
    generic = seasonal.rolling_integrated_by_season(
        monthly, "SWE_monthly", "SWE_3mo", 3
    )
    pd.testing.assert_frame_equal(named, generic)
    assert "SWE_3mo" in named.columns


# --- end-to-end index pipelines on synthetic data ------------------------------
def test_compute_swei_runs():
    daily = _synthetic_daily()
    swei = indices.compute_swei(daily, window_months=3, seed=42)
    assert "SWEI" in swei.columns
    assert {"Grid_ID", "elev_class", "month"}.issubset(swei.columns)
    assert swei["SWEI"].notna().any()


def test_spi_pipeline_runs():
    daily = _synthetic_daily()
    spi = indices.spi_pipeline(daily, window_months=3)
    assert "SPI" in spi.columns
    assert {"Grid_ID", "elev_class", "month"}.issubset(spi.columns)


# --- plotting builds figures ---------------------------------------------------
def test_plots_build(tmp_path):
    import matplotlib
    matplotlib.use("Agg")

    avg = pd.DataFrame({
        "elev_class": constants.ELEV_ORDER_ASC * 3,
        "Seasonal_Year": sorted([2000, 2001, 2002] * 5),
        "Avg_SWEI_8mo": np.linspace(-2, 2, 15),
    })
    fig = plotting.plot_index_heatmap(avg, "Avg_SWEI_8mo", "Test SWEI")
    assert fig is not None

    cls = pd.DataFrame({
        "elev_class": constants.ELEV_ORDER_ASC,
        "Seasonal_Year": [2000, 2001, 2002, 2003, 2004],
        "Avg_SWE_P_ratio": [0.1, 0.2, 0.3, 0.4, 0.5],
        "Avg_Cum_P_anomaly": [-5, 5, -3, 3, 0],
        "cluster_name": ["Dry", "Warm", "Warm & Dry", "Normal", "Dry"],
    })
    assert plotting.plot_classification_scatter(cls) is not None
    assert plotting.plot_classification_heatmap(cls) is not None


# --- config resolves -----------------------------------------------------------
def test_config_paths():
    assert config.data_root().name == "Data"
    p = config.elevation_shapefile()
    assert p.name == "Alberta_elevation_combined.shp"
