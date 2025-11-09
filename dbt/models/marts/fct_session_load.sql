with participation as (
    select
        tenant_id,
        athlete_id,
        session_id,
        rpe,
        load,
        minutes
    from {{ source('core', 'session_participation') }}
),
sessions as (
    select
        session_id,
        tenant_id,
        date_trunc('day', start_ts) as session_date,
        session_type
    from {{ ref('stg_sessions') }}
)

select
    p.tenant_id,
    p.athlete_id,
    s.session_date,
    s.session_type,
    p.load as load_au,
    p.rpe as rpe_session,
    p.minutes as minutes_played
from participation p
join sessions s on s.session_id = p.session_id and s.tenant_id = p.tenant_id

