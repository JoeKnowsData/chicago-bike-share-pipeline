-- Every station key in the fact table has a row in dim_station (no orphan keys,
-- so Power BI relationships never show blank members).
select f.ride_id, f.start_station_id, f.end_station_id
from marts.fct_trips as f
left join marts.dim_station as s on s.station_id = f.start_station_id
left join marts.dim_station as e on e.station_id = f.end_station_id
where s.station_id is null or e.station_id is null;
