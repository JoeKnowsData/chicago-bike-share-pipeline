-- Q: Where should a membership campaign target casual riders?
-- Stations with the most casual-rider departures, with each station's casual share.
-- A high casual share at a busy station is the best place to convert riders to members.
with station_trips as (
    select
        start_station_id,
        count(*) as trips,
        count(*) filter (where member_type = 'casual') as casual_trips
    from marts.fct_trips
    where start_station_id <> 'DOCKLESS'
    group by start_station_id
)

select
    dense_rank() over (order by t.casual_trips desc) as rank,
    s.station_label as station,
    t.casual_trips,
    t.trips as all_trips,
    round(100.0 * t.casual_trips / t.trips, 1) as pct_casual
from station_trips as t
join marts.dim_station as s on s.station_id = t.start_station_id
qualify rank <= 10
order by rank;
