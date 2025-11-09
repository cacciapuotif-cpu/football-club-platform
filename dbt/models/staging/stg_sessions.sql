with base as (
    select
        session_id,
        tenant_id,
        team_id,
        session_type,
        start_ts,
        end_ts,
        rpe_avg,
        load,
        notes,
        date_trunc('day', start_ts) as session_date
    from {{ source('core', 'sessions') }}
)

select
    *,
    extract(epoch from (end_ts - start_ts)) / 60.0 as duration_minutes
from base
with source as (
    select
        session_id,
        tenant_id,
        team_id,
        session_type,
        start_ts,
        end_ts,
        rpe_avg,
        load,
        notes
    from {{ source('fcp', 'sessions') }}
)

select
    session_id,
    tenant_id,
    team_id,
    session_type,
    start_ts,
    end_ts,
    rpe_avg,
    load,
    notes,
    datediff('minute', start_ts, end_ts) as duration_min
from source
where start_ts is not null

