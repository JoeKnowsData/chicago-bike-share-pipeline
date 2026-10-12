-- Q: How much does the weather move demand?
-- Average trips per day by temperature band, split into dry and wet (1 mm+ rain) days.
with daily as (
    select
        d.date,
        d.temp_band,
        d.is_wet_day,
        count(f.ride_id) as trips
    from marts.dim_date as d
    left join marts.fct_trips as f on f.start_date = d.date
    group by all
)

select
    temp_band,
    count(*) filter (where not is_wet_day) as dry_days,
    round(avg(trips) filter (where not is_wet_day))::int as avg_trips_dry_day,
    count(*) filter (where is_wet_day) as wet_days,
    round(avg(trips) filter (where is_wet_day))::int as avg_trips_wet_day,
    round(
        100.0 * (avg(trips) filter (where is_wet_day) - avg(trips) filter (where not is_wet_day))
        / avg(trips) filter (where not is_wet_day),
        1
    ) as pct_change_when_wet
from daily
group by temp_band
order by temp_band;
