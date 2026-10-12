# Building the Power BI report

The pipeline leaves a star schema ready for Power BI. There are two ways to connect.

## Option A: Parquet files (easiest, no drivers)

1. Run the pipeline: `bikeshare run`. The tables are written to `data/exports/`.
2. In Power BI Desktop: **Get data → More… → Parquet**.
3. Paste the full path to `fct_trips.parquet`, e.g.
   `C:\Users\you\chicago-bike-share-pipeline\data\exports\fct_trips.parquet`, and load it.
4. Repeat for `dim_date.parquet`, `dim_station.parquet`, and optionally
   `daily_summary.parquet` and `data_quality_summary.parquet`.

To refresh after re-running the pipeline, click **Refresh** in Power BI.

If the Parquet connector gives you trouble, run `bikeshare export --format csv` and use
**Get data → Text/CSV** instead.

## Option B: Connect straight to the DuckDB database (ODBC)

This is closer to how a BI tool reads from a real warehouse.

1. Install the DuckDB ODBC driver for Windows from <https://duckdb.org/docs/installation/>
   (choose ODBC).
2. Open **ODBC Data Sources (64-bit)** → **Add** → **DuckDB Driver**. Name the DSN
   `bikeshare` and set **Database** to the full path of `data\warehouse\bikeshare.duckdb`.
3. In Power BI: **Get data → ODBC → DSN: bikeshare**, then pick the tables under `marts`.

Close Power BI (or the connection) before re-running the pipeline, since DuckDB allows
only one writer at a time.

## Model setup

In **Model view**, create these relationships (all many-to-one, single direction):

| From | To | Active |
| --- | --- | --- |
| `fct_trips[start_date]` | `dim_date[date]` | Yes |
| `fct_trips[start_station_id]` | `dim_station[station_id]` | Yes |
| `fct_trips[end_station_id]` | `dim_station[station_id]` | **No** (used by the Arrivals measure) |
| `daily_summary[date]` | `dim_date[date]` | Yes |

Then:

- Select `dim_date` → **Mark as date table** → `date`.
- Sort `dim_date[month_label]` by `month_start`, and `dim_date[day_name]` by `day_of_week_number`.
- Set `dim_station[latitude]` and `[longitude]` to the Latitude / Longitude data categories for maps.
- Hide the key columns on `fct_trips` (`start_date`, station ids) so report builders use the dimensions.

## Starter measures

Put these in a `_Measures` table.

```DAX
Trips = COUNTROWS ( fct_trips )

Member Trips = CALCULATE ( [Trips], fct_trips[member_type] = "member" )

Casual Trips = CALCULATE ( [Trips], fct_trips[member_type] = "casual" )

Casual Share = DIVIDE ( [Casual Trips], [Trips] )

Avg Duration (min) = AVERAGE ( fct_trips[duration_minutes] )

Median Duration (min) = MEDIAN ( fct_trips[duration_minutes] )

Days = COUNTROWS ( dim_date )

Trips per Day = DIVIDE ( [Trips], [Days] )

E-bike Share =
DIVIDE ( CALCULATE ( [Trips], fct_trips[rideable_type] = "electric_bike" ), [Trips] )

Trips MoM % =
VAR PriorMonth = CALCULATE ( [Trips], DATEADD ( dim_date[date], -1, MONTH ) )
RETURN DIVIDE ( [Trips] - PriorMonth, PriorMonth )

Arrivals =
CALCULATE (
    [Trips],
    USERELATIONSHIP ( fct_trips[end_station_id], dim_station[station_id] )
)

Net Flow = [Arrivals] - [Trips]   -- by station: negative means the station loses bikes
```

## Suggested report pages

These follow the questions in [analysis_results.md](analysis_results.md), so each page
has a SQL query to check its numbers against.

1. **Overview**: cards for Trips, Casual Share, Median Duration, Trips per Day; a line chart
   of Trips by `month_label` split by `member_type`.
2. **When people ride**: a matrix of `start_hour` (rows) by `day_name` (columns) showing
   Trips, with background conditional formatting as a heatmap; a slicer on `member_type`.
3. **Weather**: a scatter chart of Trips per Day against `temp_max_c` with `date` as the
   detail and `is_wet_day` as the legend; a column chart of Trips per Day by `temp_band`.
4. **Stations**: a map (or Azure Map) of `dim_station` with bubble size = Trips and
   tooltips for Casual Share; a table of the top stations by Net Flow.
5. **Data quality**: a bar chart from `data_quality_summary` showing how many rows each
   cleaning rule removed. Hiring managers like seeing that you checked.

## Saving to GitHub

A `.pbix` embeds the data (about 6 million rows), which is too big for GitHub and is
ignored by `.gitignore`. Instead:

- **File → Export → Power BI template** and commit the `.pbit` (model and visuals, no data).
- Add screenshots of each page to `docs/images/` and show them in the README.
