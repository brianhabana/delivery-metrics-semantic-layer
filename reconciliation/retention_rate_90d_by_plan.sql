-- Expected 90-day retention by plan, computed from staging (not the mart's
-- flags) so the mart's retention logic is checked too.
-- As-of date 2026-10-31, per specs/metric_specs.md.
select
    plan,
    sum(case when started_at <= date '2026-10-31' - interval 90 day
              and (cancelled_at is null or cancelled_at >= started_at + interval 90 day)
             then 1 else 0 end)
    / sum(case when started_at <= date '2026-10-31' - interval 90 day
               then 1 else 0 end) as expected
from main.stg_subscriptions
group by 1
