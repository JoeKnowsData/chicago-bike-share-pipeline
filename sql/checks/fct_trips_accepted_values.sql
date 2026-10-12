-- Category columns only hold known values.
select ride_id, member_type, rideable_type
from marts.fct_trips
where member_type not in ('member', 'casual')
    or rideable_type not in ('classic_bike', 'electric_bike', 'electric_scooter');
