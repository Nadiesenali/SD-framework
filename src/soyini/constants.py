"""Shared constants for the SOYINI framework.

Centralizes values that were previously re-typed in several notebooks:
elevation ordering, the SWEI/SPI drought threshold, the climatology period,
the winter-season definition, and the drought-type colour maps.
"""

from __future__ import annotations

# Elevation classes, low -> high. Produced by notebook 01.
ELEV_ORDER_ASC = ["0_500m", "500_1000m", "1000_1500m", "1500_2000m", "2000_2500m"]

# High -> low. Notebooks 03/04 order the SWEI/SPI heatmap rows this way so that
# high elevations appear at the top.
ELEV_ORDER_DESC = list(reversed(ELEV_ORDER_ASC))

# A seasonal-average SWEI/SPI at or below this value flags a drought year.
DROUGHT_THRESHOLD = -0.5

# Climatological reference period (inclusive) for peak-SWE normalization.
CLIMATOLOGY_PERIOD = (1991, 2020)

# Winter season definition used for the seasonal (Oct-May) analysis.
SEASON_START_MONTH = 10  # October
SEASON_END_MONTH = 5     # May
WINTER_MONTHS = [10, 11, 12, 1, 2, 3, 4, 5]

# Colour map used for the classification scatter plot (notebook 05, cell 20).
DROUGHT_TYPE_COLORS_SCATTER = {
    "Warm": "#EB3A3A",
    "Warm & Dry": "#9C1C87",
    "Dry": "#0C889E",
    "Normal": "#B2B8BD",
}

# Colour map used for the classification heatmap (notebook 05, cell 22).
DROUGHT_TYPE_COLORS_HEATMAP = {
    "Dry": "#599CA8",
    "Warm & Dry": "#A16597",
    "Warm": "#C76363",
    "Normal": "#B2B8BD",
}

# Integer encoding of drought types for the classification heatmap.
DROUGHT_TYPE_TO_VALUE = {
    "Dry": 1,
    "Warm & Dry": 2,
    "Warm": 3,
    "Normal": 4,
}
