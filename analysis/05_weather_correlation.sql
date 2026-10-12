-- Q: Which weather measure tracks daily ridership most closely?
-- Pearson correlation between trips per day and each weather measure.
with daily as (
    select d.*, count(f.ride_id) as trips
    from marts.dim_date as d
    left join marts.fct_trips as f on f.start_date = d.date
    group by all
)

select measure, round(correlation, 2) as correlation_with_daily_trips
from (
    select
        corr(trips, temp_max_c) as "Max temperature (°C)",
        corr(trips, precipitation_mm) as "Rainfall (mm)",
        corr(trips, wind_avg_kmh) as "Average wind (km/h)",
        corr(trips, snow_depth_mm) as "Snow on the ground (mm)"
    from daily
)
unpivot (correlation for measure in (
    "Max temperature (°C)", "Rainfall (mm)", "Average wind (km/h)", "Snow on the ground (mm)"
))
order by abs(correlation) desc;
