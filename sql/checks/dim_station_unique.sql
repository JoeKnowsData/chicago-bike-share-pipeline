-- One row per station id.
select station_id, count(*) as copies
from marts.dim_station
group by station_id
having count(*) > 1;
