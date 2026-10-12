-- Q: How do members and casual riders use the service differently?
-- Share of trips, typical ride length and distance, and how often each group rides
-- an e-bike or brings the bike back to where it started (a sign of leisure riding).
select
    member_type,
    count(*) as trips,
    round(100.0 * count(*) / sum(count(*)) over (), 1) as pct_of_trips,
    round(median(duration_minutes), 1) as median_minutes,
    round(avg(duration_minutes), 1) as avg_minutes,
    round(median(distance_km), 2) as median_km,
    round(100.0 * avg((rideable_type = 'electric_bike')::int), 1) as pct_ebike,
    round(100.0 * avg(is_round_trip::int), 1) as pct_round_trip
from marts.fct_trips
group by member_type
order by trips desc;
