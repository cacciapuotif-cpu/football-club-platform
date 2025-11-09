with latest_features as (
    select
        tenant_id,
        athlete_id,
        feature_name,
        feature_value,
        event_ts,
        row_number() over (partition by tenant_id, athlete_id, feature_name, event_ts order by computation_ts desc) as rn
    from {{ source('core', 'features') }}
)

select
    tenant_id,
    athlete_id,
    event_ts as event_date,
    max(case when feature_name = 'readiness_score' then feature_value end) as readiness_score,
    max(case when feature_name = 'acute_chronic_ratio_7_28' then feature_value end) as acr_7_28,
    max(case when feature_name = 'rolling_hrv_baseline_28d' then feature_value end) as hrv_baseline,
    max(case when feature_name = 'sleep_debt_hours_7d' then feature_value end) as sleep_debt_hours,
    max(case when feature_name = 'wellness_survey_z' then feature_value end) as wellness_survey_z
from latest_features
where rn = 1
group by tenant_id, athlete_id, event_ts

