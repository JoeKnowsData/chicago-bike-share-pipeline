-- marts.dim_date: one row per calendar day covered by the trips, with the day's weather
-- attached so Power BI can slice any measure by temperature or rain.

create schema if not exists marts;

create or replace table marts.dim_date as
with bounds as (
    select min(started_at)::date as first_day, max(started_at)::date as last_day
    from staging.trips
    where reject_reason is null
),

days as (
    select unnest(generate_series(first_day, last_day, interval 1 day))::date as date
    from bounds
)

select
    d.date,
    cast(strftime(d.date, '%Y%m%d') as integer) as date_key,
    year(d.date) as year,
    quarter(d.date) as quarter,
    month(d.date) as month_number,
    strftime(d.date, '%B') as month_name,
    strftime(d.date, '%b %Y') as month_label,
    date_trunc('month', d.date)::date as month_start,
    date_trunc('week', d.date)::date as week_start,
    isodow(d.date) as day_of_week_number,
    strftime(d.date, '%A') as day_name,
    isodow(d.date) in (6, 7) as is_weekend,
    case
        when month(d.date) in (12, 1, 2) then 'Winter'
        when month(d.date) in (3, 4, 5) then 'Spring'
        when month(d.date) in (6, 7, 8) then 'Summer'
        else 'Autumn'
    end as season,
    w.temp_max_c,
    w.temp_min_c,
    round((w.temp_max_c + w.temp_min_c) / 2, 1) as temp_avg_c,
    w.precipitation_mm,
    w.snowfall_mm,
    w.snow_depth_mm,
    w.wind_avg_kmh,
    w.precipitation_mm >= 1 as is_wet_day,
    case
        when w.temp_max_c is null then 'Unknown'
        when w.temp_max_c < 0 then '1. Below 0°C'
        when w.temp_max_c < 10 then '2. 0–10°C'
        when w.temp_max_c < 20 then '3. 10–20°C'
        when w.temp_max_c < 28 then '4. 20–28°C'
        else '5. 28°C and above'
    end as temp_band
from days as d
left join staging.weather_daily as w on w.weather_date = d.date;
