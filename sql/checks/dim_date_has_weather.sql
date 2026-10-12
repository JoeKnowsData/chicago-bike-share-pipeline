-- severity: warn
-- NOAA publishes with a lag of a few days, so recent dates may not have weather yet.
-- Worth knowing, but not a reason to fail the run.
select date
from marts.dim_date
where temp_max_c is null or precipitation_mm is null;
