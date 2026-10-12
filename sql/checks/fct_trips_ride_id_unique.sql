-- Every trip appears once in the fact table.
select ride_id, count(*) as copies
from marts.fct_trips
group by ride_id
having count(*) > 1;
