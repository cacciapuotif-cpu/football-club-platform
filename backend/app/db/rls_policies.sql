-- ============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Football Club Platform - Multi-tenant Isolation
-- ============================================

-- This file contains Row Level Security policies for multi-tenant data isolation.
-- Each policy ensures that users can only access data belonging to their organization.
-- The tenant_id is set via current_setting('app.tenant_id') in the middleware.

-- ============================================
-- 1. ORGANIZATIONS TABLE
-- ============================================

-- Enable RLS on organizations table
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only view their own organization
CREATE POLICY organizations_tenant_isolation ON organizations
    FOR ALL
    USING (id::text = current_setting('app.tenant_id', true))
    WITH CHECK (id::text = current_setting('app.tenant_id', true));

-- Policy: Super admins can view all organizations
CREATE POLICY organizations_superadmin_access ON organizations
    FOR ALL
    USING (
        current_setting('app.user_role', true) = 'superadmin'
    );


-- ============================================
-- 2. PLAYERS TABLE
-- ============================================

ALTER TABLE players ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access players from their organization
CREATE POLICY players_tenant_isolation ON players
    FOR ALL
    USING (organization_id::text = current_setting('app.tenant_id', true))
    WITH CHECK (organization_id::text = current_setting('app.tenant_id', true));

-- Policy: Coaches can view players from teams they manage
CREATE POLICY players_coach_access ON players
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM teams t
            WHERE t.id = players.team_id
            AND t.head_coach_id::text = current_setting('app.user_id', true)
        )
    );


-- ============================================
-- 3. TEAMS TABLE
-- ============================================

ALTER TABLE teams ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access teams from their organization
CREATE POLICY teams_tenant_isolation ON teams
    FOR ALL
    USING (organization_id::text = current_setting('app.tenant_id', true))
    WITH CHECK (organization_id::text = current_setting('app.tenant_id', true));

-- Policy: Coaches can view and update their own teams
CREATE POLICY teams_coach_access ON teams
    FOR ALL
    USING (head_coach_id::text = current_setting('app.user_id', true))
    WITH CHECK (head_coach_id::text = current_setting('app.user_id', true));


-- ============================================
-- 4. TRAINING SESSIONS TABLE
-- ============================================

ALTER TABLE training_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access training sessions from their organization
CREATE POLICY training_sessions_tenant_isolation ON training_sessions
    FOR ALL
    USING (organization_id::text = current_setting('app.tenant_id', true))
    WITH CHECK (organization_id::text = current_setting('app.tenant_id', true));

-- Policy: Coaches can manage sessions for their teams
CREATE POLICY training_sessions_coach_access ON training_sessions
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM teams t
            WHERE t.id = training_sessions.team_id
            AND t.head_coach_id::text = current_setting('app.user_id', true)
        )
    );


-- ============================================
-- 5. MATCHES TABLE
-- ============================================

ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access matches from their organization
CREATE POLICY matches_tenant_isolation ON matches
    FOR ALL
    USING (
        home_team_id IN (
            SELECT id FROM teams WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
        OR
        away_team_id IN (
            SELECT id FROM teams WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    )
    WITH CHECK (
        home_team_id IN (
            SELECT id FROM teams WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    );


-- ============================================
-- 6. WELLNESS DATA TABLE
-- ============================================

ALTER TABLE wellness_data ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access wellness data for players in their organization
CREATE POLICY wellness_data_tenant_isolation ON wellness_data
    FOR ALL
    USING (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    )
    WITH CHECK (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    );

-- Policy: Players can only view and update their own wellness data
CREATE POLICY wellness_data_player_self_access ON wellness_data
    FOR ALL
    USING (player_id::text = current_setting('app.user_id', true))
    WITH CHECK (player_id::text = current_setting('app.user_id', true));


-- ============================================
-- 7. INJURIES TABLE
-- ============================================

ALTER TABLE injuries ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access injuries for players in their organization
CREATE POLICY injuries_tenant_isolation ON injuries
    FOR ALL
    USING (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    )
    WITH CHECK (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    );

-- Policy: Medical staff can view all injuries in their organization
CREATE POLICY injuries_medical_staff_access ON injuries
    FOR SELECT
    USING (
        current_setting('app.user_role', true) IN ('medical_staff', 'physio')
        AND
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    );


-- ============================================
-- 8. TRAINING PLANS TABLE
-- ============================================

ALTER TABLE training_plans ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access training plans for their organization
CREATE POLICY training_plans_tenant_isolation ON training_plans
    FOR ALL
    USING (
        team_id IN (
            SELECT id FROM teams WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    )
    WITH CHECK (
        team_id IN (
            SELECT id FROM teams WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    );

-- Policy: Coaches can manage plans for their teams
CREATE POLICY training_plans_coach_access ON training_plans
    FOR ALL
    USING (
        created_by_id::text = current_setting('app.user_id', true)
        OR
        team_id IN (
            SELECT id FROM teams WHERE head_coach_id::text = current_setting('app.user_id', true)
        )
    );


-- ============================================
-- 9. REPORTS TABLE
-- ============================================

ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access reports for their organization
CREATE POLICY reports_tenant_isolation ON reports
    FOR ALL
    USING (organization_id::text = current_setting('app.tenant_id', true))
    WITH CHECK (organization_id::text = current_setting('app.tenant_id', true));

-- Policy: Coaches can view reports for their teams
CREATE POLICY reports_coach_access ON reports
    FOR SELECT
    USING (
        team_id IN (
            SELECT id FROM teams WHERE head_coach_id::text = current_setting('app.user_id', true)
        )
    );


-- ============================================
-- 10. SENSOR DATA TABLE
-- ============================================

ALTER TABLE sensor_data ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access sensor data for their organization's players
CREATE POLICY sensor_data_tenant_isolation ON sensor_data
    FOR ALL
    USING (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    )
    WITH CHECK (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    );


-- ============================================
-- 11. PLAYER SESSION TRACKING TABLE
-- ============================================

ALTER TABLE player_session_tracking ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access player session tracking for their organization
CREATE POLICY player_session_tracking_tenant_isolation ON player_session_tracking
    FOR ALL
    USING (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    )
    WITH CHECK (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    );


-- ============================================
-- 12. PHYSICAL TESTS TABLE
-- ============================================

ALTER TABLE physical_tests ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access physical tests for their organization's players
CREATE POLICY physical_tests_tenant_isolation ON physical_tests
    FOR ALL
    USING (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    )
    WITH CHECK (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    );


-- ============================================
-- 13. TECHNICAL STATS TABLE
-- ============================================

ALTER TABLE technical_stats ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access technical stats for their organization
CREATE POLICY technical_stats_tenant_isolation ON technical_stats
    FOR ALL
    USING (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
        OR
        match_id IN (
            SELECT id FROM matches
            WHERE home_team_id IN (
                SELECT id FROM teams WHERE organization_id::text = current_setting('app.tenant_id', true)
            )
        )
    )
    WITH CHECK (
        player_id IN (
            SELECT id FROM players WHERE organization_id::text = current_setting('app.tenant_id', true)
        )
    );


-- ============================================
-- UTILITY FUNCTIONS
-- ============================================

-- Function to set tenant context for a session
CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id TEXT, p_user_id TEXT DEFAULT NULL, p_user_role TEXT DEFAULT NULL)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.tenant_id', p_tenant_id, false);

    IF p_user_id IS NOT NULL THEN
        PERFORM set_config('app.user_id', p_user_id, false);
    END IF;

    IF p_user_role IS NOT NULL THEN
        PERFORM set_config('app.user_role', p_user_role, false);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to clear tenant context
CREATE OR REPLACE FUNCTION clear_tenant_context()
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.tenant_id', '', false);
    PERFORM set_config('app.user_id', '', false);
    PERFORM set_config('app.user_role', '', false);
END;
$$ LANGUAGE plpgsql;

-- Function to get current tenant context
CREATE OR REPLACE FUNCTION get_tenant_context()
RETURNS TABLE(tenant_id TEXT, user_id TEXT, user_role TEXT) AS $$
BEGIN
    RETURN QUERY SELECT
        current_setting('app.tenant_id', true),
        current_setting('app.user_id', true),
        current_setting('app.user_role', true);
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- To verify RLS policies are enabled:
-- SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' AND rowsecurity = true;

-- To list all policies:
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
-- FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename, policyname;

-- To test tenant isolation (run as app user):
-- SELECT set_tenant_context('org-uuid-here', 'user-uuid-here', 'coach');
-- SELECT * FROM players; -- Should only return players from the specified organization
-- SELECT clear_tenant_context();
