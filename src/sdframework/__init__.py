"""Snow Drought Framework.

Reusable building blocks for the Alberta snow-drought detection and
classification workflows. The scientific narrative and step-by-step
orchestration live in the ``workflows/*.ipynb`` notebooks; this package holds
the shared, deduplicated machinery they import.

Submodules
----------
config          Path resolution (replaces per-notebook cwd/sys.path hacks).
io              Data loaders (shapefile / CSV / NetCDF).
constants       Elevation ordering, thresholds, colour maps.
seasonal        Seasonal-year + daily->monthly + rolling integration helpers.
indices         SWEI and SPI computation.
classification  Drought-year parsing, z-scoring, k-means cluster naming.
plotting        Seasonal index heatmaps and classification plots.
"""

from __future__ import annotations

from . import (  # noqa: F401
    classification,
    config,
    constants,
    indices,
    io,
    plotting,
    seasonal,
)
from .io import load_basin_data, load_csv_data, load_nc_data
from .indices import compute_swei, spi_pipeline
from .seasonal import select_seasonal_data, extract_grid_metadata

__version__ = "0.1.0"

__all__ = [
    "config",
    "constants",
    "io",
    "seasonal",
    "indices",
    "classification",
    "plotting",
    "load_basin_data",
    "load_csv_data",
    "load_nc_data",
    "compute_swei",
    "spi_pipeline",
    "select_seasonal_data",
    "extract_grid_metadata",
]
