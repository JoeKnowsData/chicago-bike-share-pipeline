-- Every trip date has a row in dim_date.
select f.ride_id, f.start_date
from marts.fct_trips as f
anti join marts.dim_date as d on d.date = f.start_date;
