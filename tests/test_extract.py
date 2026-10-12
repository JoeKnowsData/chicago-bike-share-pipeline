import gzip
import io
import zipfile

import pytest

from bikeshare import extract
from bikeshare.config import Paths


def test_month_range_crosses_year_end():
    assert extract.month_range("2025-11", "2026-02") == ["202511", "202512", "202601", "202602"]


def test_month_range_rejects_reversed_dates():
    with pytest.raises(ValueError):
        extract.month_range("2026-03", "2026-01")


def test_extract_trip_csv_ignores_mac_metadata_and_misnamed_file(tmp_path):
    # Mirrors the real January 2026 zip: wrong inner file name plus __MACOSX junk.
    zip_path = tmp_path / "202601-divvy-tripdata.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("202501-divvy-tripdata.csv", "ride_id\nABC\n")
        zf.writestr("__MACOSX/._202501-divvy-tripdata.csv", "binary junk")
    dest = tmp_path / "202601-divvy-tripdata.csv"

    extract.extract_trip_csv(zip_path, dest)

    assert dest.read_text() == "ride_id\nABC\n"


def test_extract_trip_csv_fails_loudly_on_unexpected_zip(tmp_path):
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("a.csv", "x")
        zf.writestr("b.csv", "y")
    with pytest.raises(ValueError, match="exactly one CSV"):
        extract.extract_trip_csv(zip_path, tmp_path / "out.csv")


def test_extract_weather_keeps_only_ohare_rows(tmp_path, monkeypatch):
    lines = (
        "ASN00010729,20250101,PRCP,0,,,a,\n"
        "USW00094846,20250101,TMAX,11,,,W,2400\n"
        "USW00094847,20250101,TMAX,99,,,W,2400\n"
    )
    payload = gzip.compress(lines.encode())
    monkeypatch.setattr(extract.urllib.request, "urlopen", lambda url, timeout: io.BytesIO(payload))

    [written] = extract.extract_weather(Paths(tmp_path), [2025], refresh=True)

    assert written.read_text().splitlines() == [
        "id,date,element,data_value,m_flag,q_flag,s_flag,obs_time",
        "USW00094846,20250101,TMAX,11,,,W,2400",
    ]


def test_extract_trips_skips_files_already_on_disk(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    paths.raw_trips.mkdir(parents=True)
    existing = paths.raw_trips / "202601-divvy-tripdata.csv"
    existing.write_text("already here")

    def fail(*args, **kwargs):
        raise AssertionError("should not download")

    monkeypatch.setattr(extract, "_download", fail)
    assert extract.extract_trips(paths, ["202601"]) == [existing]
