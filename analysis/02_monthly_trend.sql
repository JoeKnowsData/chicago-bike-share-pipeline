-- Q: How does ridership change through the year?
-- Monthly trips by rider type, the casual share, and month-on-month growth.
with monthly as (
    select
        d.month_start,
        d.month_label,
        count(*) as trips,
        count(*) filter (where f.member_type = 'member') as member_trips,
        count(*) filter (where f.member_type = 'casual') as casual_trips
    from marts.fct_trips as f
    join marts.dim_date as d on d.date = f.start_date
    group by all
)

select
    month_label as month,
    trips,
    member_trips,
    casual_trips,
    round(100.0 * casual_trips / trips, 1) as pct_casual,
    round(100.0 * (trips - lag(trips) over w) / lag(trips) over w, 1) as pct_change_vs_prior_month
from monthly
window w as (order by month_start)
order by month_start;
