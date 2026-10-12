"""Export the mart tables to Parquet (or CSV) so Power BI can read them without a
database driver. See docs/powerbi.md."""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from bikeshare.config import Paths

log = logging.getLogger(__name__)

MART_TABLES = ("fct_trips", "dim_station", "dim_date", "daily_summary", "data_quality_summary")


def export_marts(
    con: duckdb.DuckDBPyConnection, paths: Paths, file_format: str = "parquet"
) -> list[Path]:
    if file_format not in ("parquet", "csv"):
        raise ValueError(f"unsupported format {file_format!r}")
    paths.exports.mkdir(parents=True, exist_ok=True)
    if file_format == "parquet":
        options = "format parquet, compression zstd"
    else:
        options = "format csv, header"
    written = []
    for table in MART_TABLES:
        dest = paths.exports / f"{table}.{file_format}"
        con.execute(f"copy marts.{table} to '{dest.as_posix()}' ({options})")
        log.info("exported marts.%s -> %s", table, dest)
        written.append(dest)
    return written
