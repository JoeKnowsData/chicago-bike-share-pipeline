-- Every raw row is accounted for: loaded, rejected with a reason, or a duplicate.
select
    (select count(*) from raw.trips) as raw_rows,
    (select sum(rows) from marts.data_quality_summary) as accounted_rows,
    (select count(*) from marts.fct_trips) as fct_rows,
    (select count(*) from staging.trips where reject_reason is null) as staged_valid_rows
where raw_rows <> accounted_rows or fct_rows <> staged_valid_rows;
