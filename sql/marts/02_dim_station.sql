-- marts.dim_station: one row per docking station id.
-- Station ids are stable but names drift (renames, '*' suffixes, retired names), so the
-- name is the most recently used one. Coordinates are the median of every trip that
-- started or ended there, which smooths out GPS noise.
-- A few names belong to two ids (a station that moved and was given a new id), so
-- station_label adds the id to those names to keep them apart in Power BI slicers.
-- An extra 'DOCKLESS' row stands in for e-bike trips that start or end away from a
-- station, so the fact table never has a blank station key.

create or replace table marts.dim_station as
with station_events as (
    select start_station_id as station_id, start_station_name as station_name,
        start_lat as lat, start_lng as lng, started_at as event_at
    from staging.trips
    where reject_reason is null and start_station_id is not null
    union all
    select end_station_id, end_station_name, end_lat, end_lng, ended_at
    from staging.trips
    where reject_reason is null and end_station_id is not null
),

stations as (
    select
        station_id,
        arg_max(station_name, event_at) as station_name,
        round(median(lat), 6) as latitude,
        round(median(lng), 6) as longitude,
        min(event_at)::date as first_seen,
        max(event_at)::date as last_seen
    from station_events
    group by station_id
)

select
    station_id,
    station_name,
    case
        when count(*) over (partition by station_name) > 1
            then station_name || ' (' || station_id || ')'
        else station_name
    end as station_label,
    latitude,
    longitude,
    station_name ilike '%public rack%' as is_public_rack,
    first_seen,
    last_seen
from stations

union all

select
    'DOCKLESS', 'No station (dockless e-bike)', 'No station (dockless e-bike)',
    null, null, false, null, null;
