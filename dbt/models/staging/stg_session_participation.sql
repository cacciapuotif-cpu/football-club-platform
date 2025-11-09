with source as (
    select
        id,
        tenant_id,
        session_id,
        athlete_id,
        status,
        rpe,
        load
    from {{ source('fcp', 'session_participation') }}
)

select
    id,
    tenant_id,
    session_id,
    athlete_id,
    status,
    rpe,
    load,
    coalesce(load, 0) as load_default,
    coalesce(rpe, 0) as rpe_default
from source

