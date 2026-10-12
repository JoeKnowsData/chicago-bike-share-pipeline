-- marts.fct_trips: one row per valid trip. The grain Power BI's measures are built on.

create or replace table marts.fct_trips as
select
    ride_id,
    started_at::date as start_date,
    hour(started_at) as start_hour,
    started_at,
    ended_at,
    round(duration_seconds / 60.0, 2) as duration_minutes,
    round(haversine_km(start_lat, start_lng, end_lat, end_lng), 2) as distance_km,
    rideable_type,
    member_type,
    coalesce(start_station_id, 'DOCKLESS') as start_station_id,
    coalesce(end_station_id, 'DOCKLESS') as end_station_id,
    coalesce(start_station_id = end_station_id, false) as is_round_trip,
    source_month
from staging.trips
where reject_reason is null;
