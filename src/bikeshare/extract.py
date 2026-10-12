"""Extract: download the monthly Divvy trip files and the NOAA weather file.

Downloads are idempotent: a file that is already on disk is skipped, so a re-run
only fetches what is missing. Use refresh=True to force a fresh copy.
"""

from __future__ import annotations

import gzip
import logging
import shutil
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

from bikeshare.config import (
    TRIPS_URL,
    WEATHER_COLUMNS,
    WEATHER_STATION,
    WEATHER_URL,
    Paths,
)

log = logging.getLogger(__name__)


def month_range(start: str, end: str) -> list[str]:
    """Return months between start and end inclusive as YYYYMM strings.

    >>> month_range("2025-11", "2026-02")
    ['202511', '202512', '202601', '202602']
    """
    first = date.fromisoformat(f"{start}-01")
    last = date.fromisoformat(f"{end}-01")
    if first > last:
        raise ValueError(f"start {start} is after end {end}")
    months = []
    current = first
    while current <= last:
        months.append(current.strftime("%Y%m"))
        current = date(current.year + current.month // 12, current.month % 12 + 1, 1)
    return months


def _download(url: str, dest: Path) -> None:
    """Stream url to dest, writing to a .part file first so a failed download never
    leaves a half-written file that a later run would mistake for a complete one."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    log.info("downloading %s", url)
    with urllib.request.urlopen(url, timeout=120) as response, open(tmp, "wb") as out:
        shutil.copyfileobj(response, out, length=1024 * 1024)
    tmp.replace(dest)


def extract_trip_csv(zip_path: Path, dest: Path) -> None:
    """Pull the single trip CSV out of a monthly zip.

    The zips contain macOS metadata (``__MACOSX/._*.csv``) that must be ignored, and
    the inner file name is not reliable (the January 2026 zip contains a file named
    ``202501-divvy-tripdata.csv``), so the output is named after the month requested.
    """
    with zipfile.ZipFile(zip_path) as zf:
        csvs = [
            name
            for name in zf.namelist()
            if name.lower().endswith(".csv") and not name.startswith("__MACOSX")
        ]
        if len(csvs) != 1:
            raise ValueError(f"expected exactly one CSV in {zip_path.name}, found {csvs}")
        tmp = dest.with_suffix(".csv.part")
        with zf.open(csvs[0]) as src, open(tmp, "wb") as out:
            shutil.copyfileobj(src, out, length=1024 * 1024)
        tmp.replace(dest)


def extract_trips(paths: Paths, months: list[str], refresh: bool = False) -> list[Path]:
    paths.raw_trips.mkdir(parents=True, exist_ok=True)
    written = []
    for month in months:
        csv_path = paths.raw_trips / f"{month}-divvy-tripdata.csv"
        if csv_path.exists() and not refresh:
            log.info("trips %s already downloaded, skipping", month)
            written.append(csv_path)
            continue
        zip_path = paths.raw_trips / f"{month}-divvy-tripdata.zip"
        _download(TRIPS_URL.format(month=month), zip_path)
        extract_trip_csv(zip_path, csv_path)
        zip_path.unlink()
        written.append(csv_path)
    return written


def extract_weather(paths: Paths, years: list[int], refresh: bool = False) -> list[Path]:
    """Stream each year's worldwide GHCN file (~170 MB gzipped) and keep only the
    O'Hare rows, so a few hundred KB lands on disk instead of the whole file.

    Files for past years are kept between runs. The current year's file is updated
    daily by NOAA, so it is always re-fetched.
    """
    paths.raw_weather.mkdir(parents=True, exist_ok=True)
    this_year = date.today().year
    prefix = f"{WEATHER_STATION},".encode()
    written = []
    for year in years:
        dest = paths.raw_weather / f"ghcn_{WEATHER_STATION}_{year}.csv"
        if dest.exists() and not refresh and year < this_year:
            log.info("weather %s already downloaded, skipping", year)
            written.append(dest)
            continue
        url = WEATHER_URL.format(year=year)
        log.info("streaming %s (keeping station %s)", url, WEATHER_STATION)
        tmp = dest.with_suffix(".csv.part")
        with (
            urllib.request.urlopen(url, timeout=120) as response,
            gzip.GzipFile(fileobj=response) as lines,
            open(tmp, "wb") as out,
        ):
            out.write(f"{WEATHER_COLUMNS}\n".encode())
            for line in lines:
                if line.startswith(prefix):
                    out.write(line)
        tmp.replace(dest)
        written.append(dest)
    return written
