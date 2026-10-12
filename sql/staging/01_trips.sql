-- staging.trips: every raw trip, typed, cleaned and de-duplicated, with a reject_reason
-- on rows that should not reach the marts. Nothing is silently dropped: rejected rows
-- stay here so the data quality summary can account for every raw row.

create or replace table staging.trips as
with typed as (
    select
        trim(ride_id) as ride_id,
        lower(trim(rideable_type)) as rideable_type,
        lower(trim(member_casual)) as member_type,
        try_cast(started_at as timestamp) as started_at,
        try_cast(ended_at as timestamp) as ended_at,
        nullif(trim(start_station_id), '') as start_station_id,
        clean_station_name(start_station_name) as start_station_name,
        nullif(trim(end_station_id), '') as end_station_id,
        clean_station_name(end_station_name) as end_station_name,
        try_cast(start_lat as double) as start_lat,
        try_cast(start_lng as double) as start_lng,
        try_cast(end_lat as double) as end_lat,
        try_cast(end_lng as double) as end_lng,
        source_month
    from raw.trips
),

deduplicated as (
    -- A ride that crosses midnight at month end can appear in two monthly files.
    -- The copies are identical, so keep the one from the later file.
    select *
    from typed
    qualify row_number() over (partition by ride_id order by source_month desc) = 1
),

with_duration as (
    select
        *,
        date_diff('second', started_at, ended_at) as duration_seconds,
        regexp_matches(
            lower(coalesce(start_station_name, '') || '|' || coalesce(end_station_name, '')),
            'test station|warehouse|staff & visitors|repair'
        ) as touches_internal_station
    from deduplicated
),

period as (
    -- The requested months, e.g. 2025-10-01 up to (not including) 2026-10-01.
    select
        strptime(min(source_month) || '01', '%Y%m%d') as period_start,
        strptime(max(source_month) || '01', '%Y%m%d') + interval 1 month as period_end
    from raw.trips
)

select
    with_duration.*,
    case
        when started_at is null or ended_at is null then 'unparseable_timestamp'
        -- The first monthly file also holds a few rides from the last day of the
        -- month before. That month is not loaded, so leave them out rather than
        -- reporting a near-empty day.
        when started_at < period.period_start or started_at >= period.period_end
            then 'outside_period'
        when member_type not in ('member', 'casual') then 'unknown_member_type'
        when rideable_type not in ('classic_bike', 'electric_bike', 'electric_scooter')
            then 'unknown_rideable_type'
        when duration_seconds < 0 then 'negative_duration'
        -- Divvy's own guidance: rides under 60s are false starts or re-docking attempts.
        when duration_seconds < 60 then 'under_1_minute'
        -- Bikes out for over a day are lost, stolen or not docked properly.
        when duration_seconds > 86400 then 'over_24_hours'
        when touches_internal_station then 'internal_station'
        when end_lat is null or end_lng is null then 'missing_end_location'
    end as reject_reason
from with_duration
cross join period;
