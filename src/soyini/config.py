"""Central path configuration for the SOYINI framework.

This replaces the per-notebook ``project_root = Path.cwd().parent.parent`` /
``sys.path.append`` boilerplate and the hard-coded ``SOYINI/Data``
paths (which also fixes the ``DATA`` vs ``Data`` casing bug in notebook 02).

Typical use in a notebook::

    from soyini import config

    shapefile = config.output_data("elevation", "Alberta_elevation_combined.shp")
    swei_dir  = config.output_data("SWEI")          # created if missing
    plots_dir = config.output_plots("SWEI")         # created if missing

The base data directory is resolved once, in this order:

1. ``SD_DATA_ROOT`` environment variable, if set.
2. ``data_root`` in ``config/paths.yaml``, if not null.
3. The historical default ``<repo>/../SOYINI/Data``.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

# Repo root is two levels above this file: src/soyini/config.py -> repo/
REPO_ROOT = Path(__file__).resolve().parents[2]
PATHS_YAML = REPO_ROOT / "config" / "paths.yaml"

# Historical default used by the original notebooks:
#   project_root = Path.cwd().parent.parent  (parent of the repo)
#   data_root    = project_root / "SOYINI" / "Data"
_DEFAULT_DATA_ROOT = REPO_ROOT.parent / "SOYINI" / "Data"


@lru_cache(maxsize=1)
def _load_yaml() -> dict:
    if PATHS_YAML.exists():
        with open(PATHS_YAML, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    return {}


@lru_cache(maxsize=1)
def data_root() -> Path:
    """Return the resolved base data directory (not created automatically)."""
    env = os.environ.get("SD_DATA_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    cfg = _load_yaml()
    configured = cfg.get("data_root")
    if configured:
        return Path(configured).expanduser().resolve()

    return _DEFAULT_DATA_ROOT.resolve()


def _subdir_name(key: str, default: str) -> str:
    return _load_yaml().get("subdirs", {}).get(key, default)


def _resolve(base: Path, parts: tuple, ensure: bool) -> Path:
    path = base.joinpath(*[str(p) for p in parts]) if parts else base
    if ensure:
        # If the final component looks like a file (has a suffix), create its
        # parent directory; otherwise create the directory itself.
        target = path.parent if path.suffix else path
        target.mkdir(parents=True, exist_ok=True)
    return path


def input_data(*parts, ensure: bool = False) -> Path:
    """Path under ``<data_root>/input_data``. Inputs are never auto-created."""
    base = data_root() / _subdir_name("input_data", "input_data")
    return _resolve(base, parts, ensure)


def output_data(*parts, ensure: bool = True) -> Path:
    """Path under ``<data_root>/output_data`` (directory auto-created)."""
    base = data_root() / _subdir_name("output_data", "output_data")
    return _resolve(base, parts, ensure)


def output_plots(*parts, ensure: bool = True) -> Path:
    """Path under ``<data_root>/output_plots`` (directory auto-created)."""
    base = data_root() / _subdir_name("output_plots", "output_plots")
    return _resolve(base, parts, ensure)


# --- Commonly reused locations -------------------------------------------------
# The elevation shapefile produced by notebook 01 is consumed by 02-05.
def elevation_shapefile() -> Path:
    return output_data("elevation", "Alberta_elevation_combined.shp", ensure=False)


# The combined daily SWE/precip table produced by notebook 03 and consumed by 04/05.
def daily_all_csv() -> Path:
    return output_data("SWEI", "Alberta_casr_daily_all_new.csv", ensure=False)
