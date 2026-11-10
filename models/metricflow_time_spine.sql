-- One row per day. MetricFlow uses this calendar for running totals
-- and to fill in days with no activity. Ends at the reporting as-of date.
select cast(range as date) as date_day
from range(date '2025-01-01', date '2026-11-01', interval 1 day)