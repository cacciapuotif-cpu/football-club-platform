with sessions as (
    select
        session_id,
        tenant_id,
        team_id,
        start_ts::date as session_date,
        load,
        rpe_avg
    from {{ ref('stg_sessions') }}
),
participation as (
    select
        session_id,
        athlete_id,
        load_default,
        rpe_default
    from {{ ref('stg_session_participation') }}
),
wellness as (
    select
        athlete_id,
        tenant_id,
        event_ts::date as event_date,
        metric,
        value
    from {{ ref('stg_wellness') }}
),
joined as (
    select
        p.athlete_id,
        s.tenant_id,
        s.team_id,
        s.session_date,
        s.load as team_load,
        p.load_default as athlete_load,
        p.rpe_default as athlete_rpe,
        w.metric,
        w.value as wellness_value
    from participation p
    join sessions s on p.session_id = s.session_id
    left join wellness w on p.athlete_id = w.athlete_id
        and s.tenant_id = w.tenant_id
        and s.session_date = w.event_date
)

select
    athlete_id,
    tenant_id,
    team_id,
    session_date,
    avg(athlete_load) over (
        partition by athlete_id
        order by session_date
        rows between 6 preceding and current row
    ) as acute_load_7d,
    avg(athlete_load) over (
        partition by athlete_id
        order by session_date
        rows between 27 preceding and current row
    ) as chronic_load_28d,
    case
        when chronic_load_28d = 0 then null
        else acute_load_7d / nullif(chronic_load_28d, 0)
    end as acwr_7_28,
    avg(athlete_rpe) over (
        partition by athlete_id
        order by session_date
        rows between 6 preceding and current row
    ) as rpe_avg_7d,
    max(case when metric = 'READINESS' then wellness_value end) as readiness_score
from joined
group by athlete_id, tenant_id, team_id, session_date, acute_load_7d, chronic_load_28d, acwr_7_28

