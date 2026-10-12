-- Durations stay inside the cleaning rules: 1 minute to 24 hours.
select ride_id, duration_minutes
from marts.fct_trips
where duration_minutes < 1 or duration_minutes > 1440 or duration_minutes is null;
