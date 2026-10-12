-- staging.weather_daily: one row per day of O'Hare weather, pivoted from NOAA's long
-- format (one row per day per measurement) and converted to everyday units.
-- GHCN stores temperatures in tenths of °C, precipitation in tenths of mm,
-- snow in mm and wind in tenths of m/s.

create or replace table staging.weather_daily as
with observations as (
    select
        strptime(date, '%Y%m%d')::date as weather_date,
        element,
        try_cast(data_value as integer) as value
    from raw.weather
    where element in ('TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD', 'AWND')
        -- A non-empty quality flag means the value failed one of NOAA's checks.
        and nullif(trim(q_flag), '') is null
)

select
    weather_date,
    max(value) filter (where element = 'TMAX') / 10.0 as temp_max_c,
    max(value) filter (where element = 'TMIN') / 10.0 as temp_min_c,
    max(value) filter (where element = 'PRCP') / 10.0 as precipitation_mm,
    max(value) filter (where element = 'SNOW') as snowfall_mm,
    max(value) filter (where element = 'SNWD') as snow_depth_mm,
    round(max(value) filter (where element = 'AWND') / 10.0 * 3.6, 1) as wind_avg_kmh
from observations
group by weather_date;
