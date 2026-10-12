-- marts.data_quality_summary: what happened to every raw row, for the README and for
-- a "data quality" page in Power BI.

create or replace table marts.data_quality_summary as
with raw_rows as (
    select count(*) as n from raw.trips
),

outcomes as (
    select coalesce(reject_reason, 'loaded_to_fct_trips') as outcome, count(*) as rows
    from staging.trips
    group by all
    union all
    select 'duplicate_across_monthly_files', (select n from raw_rows) - count(*)
    from staging.trips
)

select
    outcome,
    rows,
    round(100.0 * rows / (select n from raw_rows), 3) as pct_of_raw_rows
from outcomes
order by rows desc;
