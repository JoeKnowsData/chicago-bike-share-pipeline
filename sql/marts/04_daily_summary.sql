-- marts.daily_summary: trips pre-aggregated to day x rider type x bike type.
-- A light alternative to fct_trips for Power BI visuals that never need trip detail.

create or replace table marts.daily_summary as
select
    start_date as date,
    member_type,
    rideable_type,
    count(*) as trips,
    round(sum(duration_minutes), 1) as total_minutes,
    round(avg(duration_minutes), 2) as avg_duration_minutes,
    round(median(duration_minutes), 2) as median_duration_minutes,
    round(avg(distance_km), 3) as avg_distance_km,
    count(*) filter (where is_round_trip) as round_trips
from marts.fct_trips
group by all;
