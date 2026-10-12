"""Shared fixtures: a tiny, hand-written copy of the raw files, with one row for each
data problem the pipeline is meant to handle."""

from __future__ import annotations

import csv
from pathlib import Path

import duckdb
import pytest

from bikeshare.config import Paths

TRIP_HEADER = [
    "ride_id", "rideable_type", "started_at", "ended_at",
    "start_station_name", "start_station_id", "end_station_name", "end_station_id",
    "start_lat", "start_lng", "end_lat", "end_lng", "member_casual",
]  # fmt: skip

A = ("Morgan St & Lake St", "CHI00878", "41.8855", "-87.6524")
A_STAR = ("Morgan St & Lake St*", "CHI00878", "41.8855", "-87.6524")
B = ("  Clark St & Elm St ", "CHI00300", "41.9030", "-87.6313")
B_ARCHIVED = ("[Archived] Clark St & Elm St", "CHI00300", "41.9030", "-87.6313")
TEST_STATION = ("Hastings Test Station", "CHI09999", "41.8500", "-87.6500")
NO_STATION = ("", "", "41.89", "-87.64")


def trip(ride_id, start, end, frm, to, member="member", bike="classic_bike", end_coords=True):
    end_lat, end_lng = (to[2], to[3]) if end_coords else ("", "")
    return [ride_id, bike, start, end, frm[0], frm[1], to[0], to[1],
            frm[2], frm[3], end_lat, end_lng, member]  # fmt: skip


# 202601 file
JANUARY = [
    trip("OK01", "2026-01-05 08:00:00", "2026-01-05 08:12:00", A, B),
    trip("OK02", "2026-01-05 09:00:00", "2026-01-05 09:30:00", B, A, member="casual"),
    trip("OK03", "2026-01-06 17:00:00", "2026-01-06 17:20:00", A_STAR, A),  # round trip
    trip("OK04", "2026-01-06 18:00:00", "2026-01-06 18:10:00", NO_STATION, B, bike="electric_bike"),
    trip("SHORT", "2026-01-07 10:00:00", "2026-01-07 10:00:30", A, A),
    trip("NEG", "2026-01-07 11:00:00", "2026-01-07 10:59:00", A, B),
    trip("LONG", "2026-01-07 12:00:00", "2026-01-08 13:00:00", A, B),
    trip("TEST", "2026-01-08 12:00:00", "2026-01-08 12:30:00", TEST_STATION, A),
    trip("NOEND", "2026-01-08 13:00:00", "2026-01-08 13:30:00", A, NO_STATION, end_coords=False),
    trip("EARLY", "2025-12-31 23:50:00", "2026-01-01 00:05:00", A, B),  # month not loaded
    trip("BADTS", "not a timestamp", "2026-01-09 10:00:00", A, B),
    trip("DUP", "2026-01-31 23:55:00", "2026-02-01 00:10:00", A, B),  # also in February
]

# 202602 file. Station B now appears under its archived name, A under its '*' name.
FEBRUARY = [
    trip("DUP", "2026-01-31 23:55:00", "2026-02-01 00:10:00", A, B),
    trip("OK05", "2026-02-02 07:45:00", "2026-02-02 08:00:00", B_ARCHIVED, A_STAR),
]

EXPECTED_VALID = {"OK01", "OK02", "OK03", "OK04", "OK05", "DUP"}
EXPECTED_REJECTS = {
    "SHORT": "under_1_minute",
    "NEG": "negative_duration",
    "LONG": "over_24_hours",
    "TEST": "internal_station",
    "NOEND": "missing_end_location",
    "EARLY": "outside_period",
    "BADTS": "unparseable_timestamp",
}

WEATHER_HEADER = "id,date,element,data_value,m_flag,q_flag,s_flag,obs_time"


def weather_rows() -> list[str]:
    rows = []
    for day in range(1, 32):
        rows += [
            f"USW00094846,202601{day:02d},TMAX,{-20 + day},,,W,2400",
            f"USW00094846,202601{day:02d},TMIN,{-80 + day},,,W,2400",
            f"USW00094846,202601{day:02d},PRCP,{25 if day == 5 else 0},,,W,2400",
            f"USW00094846,202601{day:02d},AWND,45,,,W,",
        ]
    for day in range(1, 29):
        rows += [
            f"USW00094846,202602{day:02d},TMAX,15,,,W,2400",
            f"USW00094846,202602{day:02d},TMIN,-30,,,W,2400",
            f"USW00094846,202602{day:02d},PRCP,0,,,W,2400",
        ]
    # A value that failed NOAA's quality checks (Q_FLAG set) must be ignored.
    rows.append("USW00094846,20260102,TMAX,999,,X,W,2400")
    return rows


def write_trips(path: Path, rows: list[list[str]]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(TRIP_HEADER)
        writer.writerows(rows)


@pytest.fixture
def paths(tmp_path: Path) -> Paths:
    p = Paths(tmp_path / "data")
    p.raw_trips.mkdir(parents=True)
    p.raw_weather.mkdir(parents=True)
    write_trips(p.raw_trips / "202601-divvy-tripdata.csv", JANUARY)
    write_trips(p.raw_trips / "202602-divvy-tripdata.csv", FEBRUARY)
    (p.raw_weather / "ghcn_USW00094846_2026.csv").write_text(
        "\n".join([WEATHER_HEADER, *weather_rows()]) + "\n"
    )
    return p


@pytest.fixture
def con(paths: Paths):
    connection = duckdb.connect(":memory:")
    yield connection
    connection.close()
