-- Reusable SQL functions used by the staging and mart models.

create schema if not exists staging;

-- Station names arrive with stray whitespace, a trailing '*' on some stations
-- (e.g. 'Morgan St & Lake St*' and 'Morgan St & Lake St' share one station id)
-- and an '[Archived] ' prefix on retired names.
create or replace macro clean_station_name(name) as
    nullif(
        trim(
            regexp_replace(
                regexp_replace(regexp_replace(name, '^\s*\[Archived\]\s*', ''), '\*+\s*$', ''),
                '\s+', ' ', 'g'
            )
        ),
        ''
    );

-- Straight-line distance in km between two points.
create or replace macro haversine_km(lat1, lon1, lat2, lon2) as
    2 * 6371 * asin(sqrt(
        pow(sin(radians(lat2 - lat1) / 2), 2)
        + cos(radians(lat1)) * cos(radians(lat2)) * pow(sin(radians(lon2 - lon1) / 2), 2)
    ));
