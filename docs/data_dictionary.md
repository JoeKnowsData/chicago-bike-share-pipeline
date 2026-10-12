# Data dictionary

The `marts` schema is a star schema: one fact table of trips and two dimensions.
Every table is also exported to `data/exports/<table>.parquet` by `bikeshare export`.

```mermaid
erDiagram
    dim_date ||--o{ fct_trips : "start_date"
    dim_station ||--o{ fct_trips : "start_station_id"
    dim_station ||--o{ fct_trips : "end_station_id"
    dim_date ||--o{ daily_summary : "date"
```

## marts.fct_trips

One row per valid trip (about 6 million rows for twelve months).

| Column | Type | Description |
| --- | --- | --- |
| ride_id | text | Divvy's trip id. Unique. |
| start_date | date | Local date the trip started. Joins to `dim_date.date`. |
| start_hour | integer | Hour the trip started, 0–23. |
| started_at / ended_at | timestamp | Local Chicago time, to the millisecond. |
| duration_minutes | decimal | Always between 1 and 1,440 (24 hours). |
| distance_km | decimal | Straight-line distance from start to end point. 0 for round trips. Real route distance is longer. |
| rideable_type | text | `classic_bike` or `electric_bike` (`electric_scooter` is accepted if Divvy brings scooters back). |
| member_type | text | `member` (annual pass) or `casual` (single ride or day pass). |
| start_station_id / end_station_id | text | Joins to `dim_station.station_id`. `DOCKLESS` when an e-bike was picked up or left away from a station. |
| is_round_trip | boolean | Started and ended at the same docking station. |
| source_month | text | Monthly file the row came from (`YYYYMM`), for lineage. |

## marts.dim_station

One row per docking station, plus a `DOCKLESS` row.

| Column | Type | Description |
| --- | --- | --- |
| station_id | text | Divvy station id, e.g. `CHI00878`. Unique. |
| station_name | text | Most recently used name, cleaned. |
| station_label | text | The name, with the id added when two stations share a name (110 stations). Use this in slicers. |
| latitude / longitude | decimal | Median of every trip start and end at the station. Null for `DOCKLESS`. |
| is_public_rack | boolean | A public bike rack rather than a Divvy dock. |
| first_seen / last_seen | date | First and last trip at the station in the loaded months. |

## marts.dim_date

One row per day in the loaded months, with that day's weather at O'Hare airport.

| Column | Type | Description |
| --- | --- | --- |
| date | date | Unique. Mark as the date table in Power BI. |
| date_key | integer | `YYYYMMDD`. |
| year, quarter, month_number, month_name | | Calendar attributes. |
| month_label | text | e.g. `Oct 2025`. Sort by `month_start` in Power BI. |
| month_start, week_start | date | First day of the month / ISO week (Monday). |
| day_of_week_number, day_name | | 1 = Monday … 7 = Sunday. Sort `day_name` by `day_of_week_number`. |
| is_weekend | boolean | Saturday or Sunday. |
| season | text | Meteorological season (Winter = Dec–Feb). |
| temp_max_c, temp_min_c, temp_avg_c | decimal | °C. `temp_avg_c` is the midpoint of max and min. |
| precipitation_mm | decimal | Rain and melted snow, mm. |
| snowfall_mm, snow_depth_mm | integer | New snow, and snow on the ground, mm. |
| wind_avg_kmh | decimal | Average wind speed, km/h. |
| is_wet_day | boolean | 1 mm or more of precipitation. |
| temp_band | text | Max temperature bucket. The number prefix keeps the bands in order. |

## marts.daily_summary

Trips pre-aggregated to one row per day, rider type and bike type: about 1,500 rows.
Use it for trend visuals when the trip-level detail is not needed.

| Column | Description |
| --- | --- |
| date, member_type, rideable_type | The grain. |
| trips, round_trips | Counts. |
| total_minutes, avg_duration_minutes, median_duration_minutes | Ride time. Do not average the averages in Power BI: divide `total_minutes` by `trips` instead. |
| avg_distance_km | Average straight-line distance. |

## marts.data_quality_summary

What happened to every raw row: loaded, or rejected with a reason. See the README for the rules.
