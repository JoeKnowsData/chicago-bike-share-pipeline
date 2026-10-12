-- Q: Which stations need bikes moved to or from them?
-- Net flow = arrivals minus departures over the year. Stations that lose bikes
-- (negative) need restocking; stations that gain them need emptying.
with flows as (
    select start_station_id as station_id, -1 as flow from marts.fct_trips
    union all
    select end_station_id, 1 from marts.fct_trips
),

net as (
    select
        station_id,
        count(*) filter (where flow = -1) as departures,
        count(*) filter (where flow = 1) as arrivals,
        sum(flow) as net_flow
    from flows
    where station_id <> 'DOCKLESS'
    group by station_id
),

ranked as (
    select
        *,
        row_number() over (order by net_flow) as most_drained,
        row_number() over (order by net_flow desc) as most_filled
    from net
)

select
    case when most_drained <= 5 then 'Loses bikes' else 'Gains bikes' end as direction,
    s.station_label as station,
    departures,
    arrivals,
    net_flow,
    round(net_flow / 365.0, 1) as net_bikes_per_day
from ranked as r
join marts.dim_station as s using (station_id)
where most_drained <= 5 or most_filled <= 5
order by net_flow;
