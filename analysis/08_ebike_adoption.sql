-- Q: What do riders choose e-bikes for?
-- E-bike share of trips by distance band and rider type: do people pay the e-bike
-- premium mostly for longer journeys?
with banded as (
    select
        member_type,
        rideable_type,
        case
            when distance_km < 1 then '1. Under 1 km'
            when distance_km < 3 then '2. 1–3 km'
            when distance_km < 5 then '3. 3–5 km'
            else '4. 5 km and over'
        end as distance_band
    from marts.fct_trips
    where not is_round_trip
)

pivot banded
on member_type
using round(100.0 * avg((rideable_type = 'electric_bike')::int), 1) as pct_ebike
group by distance_band
order by distance_band;
