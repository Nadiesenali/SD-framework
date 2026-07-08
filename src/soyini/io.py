"""Thin data-loading helpers shared across all workflow notebooks.

These wrap the underlying readers so the notebooks call one named function
instead of re-declaring ``load_basin_data`` etc. in every notebook.
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
import xarray as xr


def load_basin_data(file_path) -> gpd.GeoDataFrame:
    """Load basin/elevation shapefile data.

    Parameters
    ----------
    file_path : str or path-like
        Path to the shapefile containing basin data.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing basin data.
    """
    return gpd.read_file(file_path)


def load_csv_data(file_path) -> pd.DataFrame:
    """Load CSV data.

    Parameters
    ----------
    file_path : str or path-like
        Path to the CSV file containing data.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the loaded CSV data.
    """
    return pd.read_csv(file_path)


def load_nc_data(file_path) -> xr.Dataset:
    """Load data from a NetCDF file.

    Parameters
    ----------
    file_path : str or path-like
        Path to the NetCDF file containing data.

    Returns
    -------
    xarray.Dataset
        Dataset containing the loaded data.
    """
    return xr.open_dataset(file_path)
