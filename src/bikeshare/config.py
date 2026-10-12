"""Paths, source URLs and defaults in one place."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = REPO_ROOT / "sql"

# Divvy publishes one zip per month in a public S3 bucket.
# Licence: https://divvybikes.com/data-license-agreement
TRIPS_URL = "https://divvy-tripdata.s3.amazonaws.com/{month}-divvy-tripdata.zip"

# NOAA GHCN-Daily, Chicago O'Hare International Airport station (public domain).
# The per-station files in this bucket stopped updating in Feb 2025, so the pipeline
# streams the per-year files (all stations worldwide, updated daily) and keeps one station.
WEATHER_STATION = "USW00094846"
WEATHER_URL = "https://noaa-ghcn-pds.s3.amazonaws.com/csv.gz/by_year/{year}.csv.gz"
WEATHER_COLUMNS = "id,date,element,data_value,m_flag,q_flag,s_flag,obs_time"

# Twelve full months. Override with --start / --end on the command line.
DEFAULT_START = "2025-10"
DEFAULT_END = "2026-09"


@dataclass(frozen=True)
class Paths:
    """Where the pipeline reads and writes. Everything lives under one data directory."""

    data_dir: Path

    @property
    def raw_trips(self) -> Path:
        return self.data_dir / "raw" / "trips"

    @property
    def raw_weather(self) -> Path:
        return self.data_dir / "raw" / "weather"

    @property
    def database(self) -> Path:
        return self.data_dir / "warehouse" / "bikeshare.duckdb"

    @property
    def exports(self) -> Path:
        return self.data_dir / "exports"


def default_paths() -> Paths:
    return Paths(Path(os.environ.get("BIKESHARE_DATA_DIR", REPO_ROOT / "data")))
