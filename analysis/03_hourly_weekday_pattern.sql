-- Q: When do people ride? Busiest hours on weekdays vs weekends.
-- Members peak at commuting times on weekdays; casual riders peak in the afternoon.
-- Shows each rider type's top three hours for weekdays and weekends.
with hourly as (
    select
        f.member_type,
        case when d.is_weekend then 'Weekend' else 'Weekday' end as day_type,
        f.start_hour,
        count(*) as trips
    from marts.fct_trips as f
    join marts.dim_date as d on d.date = f.start_date
    group by all
),

ranked as (
    select
        *,
        round(100.0 * trips / sum(trips) over (partition by member_type, day_type), 1)
            as pct_of_day_type_trips,
        row_number() over (partition by member_type, day_type order by trips desc) as rank
    from hourly
)

select
    member_type,
    day_type,
    rank,
    format('{:02d}:00', start_hour) as hour,
    trips,
    pct_of_day_type_trips
from ranked
where rank <= 3
order by member_type, day_type, rank;
