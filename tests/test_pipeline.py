"""End-to-end test: load the fixture files, run every SQL model and every data quality
check, then assert on the cleaned output."""

import pytest

from bikeshare import export, load, quality, report, transform
from tests.conftest import EXPECTED_REJECTS, EXPECTED_VALID


@pytest.fixture
def built(con, paths):
    load.load_raw(con, paths)
    transform.run_models(con)
    return con


def rows(con, sql):
    return con.execute(sql).fetchall()


def test_only_valid_trips_reach_the_fact_table(built):
    loaded = {r[0] for r in rows(built, "select ride_id from marts.fct_trips")}
    assert loaded == EXPECTED_VALID


def test_each_bad_row_is_rejected_for_the_right_reason(built):
    rejected = dict(
        rows(
            built,
            "select ride_id, reject_reason from staging.trips where reject_reason is not null",
        )
    )
    assert rejected == EXPECTED_REJECTS


def test_duplicate_across_files_is_kept_once(built):
    assert rows(built, "select count(*) from staging.trips where ride_id = 'DUP'") == [(1,)]
    [(duplicates,)] = rows(
        built,
        "select rows from marts.data_quality_summary "
        "where outcome = 'duplicate_across_monthly_files'",
    )
    assert duplicates == 1


def test_station_names_are_cleaned(built):
    stations = dict(rows(built, "select station_id, station_name from marts.dim_station"))
    assert stations["CHI00878"] == "Morgan St & Lake St"  # trailing '*' removed
    assert stations["CHI00300"] == "Clark St & Elm St"  # '[Archived]' and spaces removed
    assert stations["DOCKLESS"] == "No station (dockless e-bike)"
    assert "CHI09999" not in stations  # test station never reaches the marts


def test_trip_measures(built):
    [(minutes, round_trip, start, km)] = rows(
        built,
        "select duration_minutes, is_round_trip, start_station_id, distance_km "
        "from marts.fct_trips where ride_id = 'OK03'",
    )
    assert (minutes, round_trip, start, km) == (20.0, True, "CHI00878", 0.0)
    [(dockless_start,)] = rows(
        built, "select start_station_id from marts.fct_trips where ride_id = 'OK04'"
    )
    assert dockless_start == "DOCKLESS"
    [(km_ok01,)] = rows(built, "select distance_km from marts.fct_trips where ride_id = 'OK01'")
    assert 2.5 < km_ok01 < 2.7  # Morgan & Lake to Clark & Elm is about 2.6 km


def test_weather_is_converted_and_joined_to_dates(built):
    [(temp_max, precip, wet, wind)] = rows(
        built,
        "select temp_max_c, precipitation_mm, is_wet_day, wind_avg_kmh "
        "from marts.dim_date where date = '2026-01-05'",
    )
    assert (temp_max, precip, wet, wind) == (-1.5, 2.5, True, 16.2)
    # The flagged 99.9°C reading on 2 Jan is ignored, leaving the valid -1.8°C.
    assert rows(
        built, "select temp_max_c from staging.weather_daily where weather_date = '2026-01-02'"
    ) == [(-1.8,)]


def test_date_dimension_spans_the_loaded_months(built):
    assert rows(built, "select min(date)::varchar, max(date)::varchar from marts.dim_date") == [
        ("2026-01-05", "2026-02-02")
    ]


def test_quality_checks_pass_apart_from_reject_rate(built):
    # The fixture is built from bad rows (7 of 14 rejected), so the reject-rate guard
    # is meant to fire here. Every other check must pass.
    with pytest.raises(quality.DataQualityError, match="reject_rate_below_threshold$"):
        quality.run_checks(built)


def test_failing_check_stops_the_pipeline(built, tmp_path):
    (tmp_path / "always_fails.sql").write_text("select 1 as broken_row")
    with pytest.raises(quality.DataQualityError, match="always_fails"):
        quality.run_checks(built, checks_dir=tmp_path)


def test_warn_check_does_not_stop_the_pipeline(built, tmp_path):
    (tmp_path / "soft.sql").write_text("-- severity: warn\nselect 1 as odd_row")
    [result] = quality.run_checks(built, checks_dir=tmp_path)
    assert result.severity == "warn" and not result.passed


def test_export_writes_every_mart(built, paths):
    written = export.export_marts(built, paths)
    assert {p.name for p in written} >= {"fct_trips.parquet", "dim_station.parquet"}
    exported = (paths.exports / "fct_trips.parquet").as_posix()
    assert rows(built, f"select count(*) from '{exported}'") == [(len(EXPECTED_VALID),)]


def test_analysis_queries_all_run(built, tmp_path):
    dest = report.write_report(built, tmp_path / "results.md")
    text = dest.read_text()
    assert text.count("\n## ") == len(list(report.ANALYSIS_DIR.glob("*.sql")))
