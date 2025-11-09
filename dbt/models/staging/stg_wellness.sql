with normalized as (
    select
        id,
        tenant_id,
        athlete_id,
        metric,
        case
            when metric = 'SLEEP_HOURS' then value
            when metric = 'RESTING_HR' then value
            when metric = 'HRV' then value
            else value
        end as value,
        unit,
        event_ts,
        date_trunc('day', event_ts) as event_date,
        source,
        quality_score
    from {{ source('core', 'wellness_readings') }}
)

select * from normalized
with source as (
    select
        id,
        tenant_id,
        athlete_id,
        metric,
        value,
        unit,
        event_ts,
        ingest_ts,
        quality_score
    from {{ source('fcp', 'wellness_readings') }}
)

select
    id,
    tenant_id,
    athlete_id,
    metric,
    value,
    unit,
    event_ts,
    ingest_ts,
    quality_score,
    case
        when quality_score is null then 'UNKNOWN'
        when quality_score >= 0.8 then 'GOOD'
        when quality_score >= 0.6 then 'OK'
        else 'LOW'
    end as quality_band
from source

