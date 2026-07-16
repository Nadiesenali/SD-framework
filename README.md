# SOYINI

A Python framework for assessing and analysing snow drought.

> Named after the Blackfoot word *soyini*, describing winter weather
> changing to milder, warmer conditions - a transition that underlies many
> warm snow droughts.

The project name was choosen to acknowledge the land where the traditional territories
of the Blackfoot Confederacy, Stoney Nakoda Nations, Tsuu T'ina Nation, and the
Métis Nation of Alberta.

---

SOYINI identifies and classifies snow droughts in the Bow River Basin, Alberta, Canada from the
data obatin from Canadian Surface Reaanalysis v3.2[CaSR](https://hpfx.collab.science.gc.ca/~scar700/rcas-casr/download_CaSR_regions_var_period.html) dataset (snow-water-equivalent (SWE) + 24hr precipitation), combined with CanSWEv7 (https://doi.org/10.5281/zenodo.4734371)  historic SWE dataset.

The scientific narrative and step-by-step orchestration live in the
`workflows/*.ipynb` notebooks. The reusable, deduplicated machinery those
notebooks import lives in the installable `soyini` package under `src/`.

## Layout

```
SOYINI/
├── pyproject.toml            # installable package metadata
├── requirements.txt          # runtime deps (or use `pip install -e .`)
├── config/
│   └── paths.yaml            # where your data tree lives (data_root)
├── src/soyini/          # the reusable package
│   ├── config.py             # path resolution (no more cwd/sys.path hacks)
│   ├── io.py                 # load_basin_data / load_csv_data / load_nc_data
│   ├── constants.py          # elevation order, thresholds, colour maps
│   ├── seasonal.py           # seasonal-year, daily→monthly, rolling integration
│   ├── indices.py            # SWEI and SPI computation
│   ├── classification.py     # drought-year parsing, z-scoring, cluster naming
│   └── plotting.py           # seasonal index heatmaps + classification plots
├── tests/                    # synthetic-data smoke/sanity tests
└── workflows/                # the five notebooks (run in order)
``o`

## Setup

```bash
# from the repository root
python -m pip install -e .
```

This installs the `soyini` package in editable mode, so the notebooks can
simply `import soyini` and you can keep editing the package in place.

## Data

The large input data (CaSR NetCDFs, DEM tiles, Alberta shapefiles) is **not**
stored in this repository. Point the framework at your own copy in one of three
ways (first match wins):

1. The `SD_DATA_ROOT` environment variable.
2. The `data_root:` value in [`config/paths.yaml`](config/paths.yaml).
3. The historical default: a `SOYINI/Data` folder sitting next
   to this repository.

`data_root` is expected to contain:

```
<data_root>/
├── input_data/
│   ├── shapefiles/Alberta/HydrologicUnitCode6WatershedsOfAlberta.shp
│   ├── shapefiles/tif/*.tif                     # DEM tiles
│   ├── CaSR_SWE/combined_SWE_new.nc
│   └── CaSR_precipitation/combined_precipitation.nc
├── output_data/                                 # created by the notebooks
└── output_plots/                                # created by the notebooks
```

Output sub-directories are created automatically on demand
(`soyini.config.output_data(...)` / `output_plots(...)`).

## The pipeline (run notebooks in order)

| # | Notebook | What it does | Key package imports |
|---|----------|--------------|---------------------|
| 01 | `01_join_tif_elevation` | Merge DEM tiles, zonal stats per HUC6 watershed, split into elevation classes | `io.load_basin_data` |
| 02 | `02_Combine_CaSR_data` | Clip CaSR SWE + precip to Alberta, tag grids with elevation class, write per-year CSVs | `io.load_basin_data`, `io.load_nc_data` |
| 03 | `03_SWEI` | 8-month SWEI (Standardized SWE Index); flag SWEI drought years | `indices.compute_swei`, `seasonal.select_seasonal_data`, `plotting.plot_index_heatmap` |
| 04 | `04_SPI` | 8-month SPI (Standardized Precipitation Index) | `indices.spi_pipeline`, `plotting.plot_index_heatmap` |
| 05 | `05_SD_classification_clean_workflow` | Two-stage classification: SWEI detects drought years, k-means types them (Warm / Dry / Warm & Dry) | `classification.*`, `plotting.plot_classification_*` |

### Method (notebook 05)

1. **Detection** — SWEI (nb 03) identifies drought years per elevation class.
2. **Typing** — only those years are clustered (k-means, k=3) on standardized
   **SWE/P ratio** and **cumulative precipitation anomaly**; centroids are mapped
   to physical types (Warm, Dry, Warm & Dry). Non-drought years are labelled
   Normal after clustering.

## Tests

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

The tests run the moved functions on small synthetic data (the full pipeline
can't run without the external data tree) and check the key invariants.

## Name & acknowledgment

**SOYINI** takes its name from the Blackfoot word *soyini* (https://blackfoot.algonquianlanguages.ca/), which is used to discribe the winter weather change to a milder, warmer temperature, warmer conditions—the very transition that drives
many *warm* snow droughts. The aurthors aknowledges and pays tribute to the land where this work was carried out, the
traditional territories of the Blackfoot Confederacy, the Stoney Nakoda Nations,
the Tsuu T'ina Nation, and the Métis Nation of Alberta. 
