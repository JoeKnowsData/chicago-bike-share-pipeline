"""Load: copy the raw CSV files into the DuckDB ``raw`` schema exactly as they arrive.

Every column is loaded as text. Typing and cleaning happen in the staging SQL, so the
raw layer is a faithful copy that can always be re-processed if a cleaning rule changes.
"""

from __future__ import annotations

import logging

import duckdb

from bikeshare.config import Paths

log = logging.getLogger(__name__)


def load_raw(con: duckdb.DuckDBPyConnection, paths: Paths) -> dict[str, int]:
    trip_glob = (paths.raw_trips / "*-divvy-tripdata.csv").as_posix()
    weather_glob = (paths.raw_weather / "ghcn_*.csv").as_posix()

    con.execute("create schema if not exists raw")
    con.execute(
        f"""
        create or replace table raw.trips as
        select
            *,
            regexp_extract(filename, '(\\d{{6}})-divvy-tripdata\\.csv$', 1) as source_month,
            current_timestamp as loaded_at
        from read_csv(
            '{trip_glob}',
            header = true,
            all_varchar = true,
            union_by_name = true,
            filename = true
        )
        """
    )
    con.execute(
        f"""
        create or replace table raw.weather as
        select *, current_timestamp as loaded_at
        from read_csv('{weather_glob}', header = true, all_varchar = true)
        """
    )
    counts = {
        table: con.execute(f"select count(*) from raw.{table}").fetchone()[0]
        for table in ("trips", "weather")
    }
    log.info("loaded raw.trips=%s raw.weather=%s rows", counts["trips"], counts["weather"])
    return counts
