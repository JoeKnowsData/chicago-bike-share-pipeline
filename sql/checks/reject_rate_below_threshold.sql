-- If cleaning throws away more than 10% of rows, the source has probably changed shape
-- (a renamed column or a new date format) and the pipeline should stop, not publish.
select sum(pct_of_raw_rows) as rejected_pct
from marts.data_quality_summary
where outcome <> 'loaded_to_fct_trips'
having sum(pct_of_raw_rows) > 10;
