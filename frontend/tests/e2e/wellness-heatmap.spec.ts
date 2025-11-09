import { test, expect } from '@playwright/test'

const mockTeams = [{ id: 'team-1', name: 'Primavera' }]

const mockPolicies = [
  {
    id: 'policy-1',
    tenant_id: 'tenant-1',
    name: 'Carico elevato',
    description: 'Alert quando ACWR > 1.5',
    cooldown_hours: 24,
    min_data_completeness: 0.8,
    thresholds: { acwr: 1.5 },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

const heatmapResponse = {
  team_id: 'team-1',
  date: '2025-11-09',
  cells: [
    {
      athlete_id: 'athlete-1',
      player_id: 'player-1',
      full_name: 'Luca Demo',
      role: 'DF',
      readiness_score: 62,
      risk_severity: 'medium',
      alerts_count: 1,
      latest_alert_at: new Date().toISOString(),
      readiness_delta: -4.5,
    },
  ],
}

const athleteContext = {
  athlete_id: 'athlete-1',
  player: {
    player_id: 'player-1',
    full_name: 'Luca Demo',
    role: 'DF',
    team_id: 'team-1',
  },
  range_start: new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString(),
  range_end: new Date().toISOString(),
  latest_features: [
    { feature_name: 'readiness_score', feature_value: 62.5, event_ts: new Date().toISOString() },
    { feature_name: 'acute_chronic_ratio_7_28', feature_value: 1.32, event_ts: new Date().toISOString() },
  ],
  readiness_trend: [
    { event_ts: new Date(Date.now() - 2 * 24 * 3600 * 1000).toISOString(), readiness_score: 67, severity: 'medium' },
    { event_ts: new Date(Date.now() - 24 * 3600 * 1000).toISOString(), readiness_score: 64, severity: 'medium' },
    { event_ts: new Date().toISOString(), readiness_score: 62, severity: 'medium' },
  ],
  recent_sessions: [
    {
      session_id: 'session-123',
      start_ts: new Date().toISOString(),
      type: 'training',
      load: 430,
      rpe: 6.5,
      minutes: 90,
    },
  ],
  alerts: [
    {
      id: 'alert-1',
      athlete_id: 'athlete-1',
      session_id: 'session-123',
      status: 'open',
      severity: 'high',
      opened_at: new Date().toISOString(),
      closed_at: null,
      policy_id: 'policy-1',
    },
  ],
}

test.describe('Wellness heatmap experience', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/teams', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTeams),
      })
    )

    await page.route('**/api/v1/wellness/policies', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPolicies),
      })
    )

    await page.route('**/api/v1/wellness/teams/team-1/heatmap**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(heatmapResponse),
      })
    )

    await page.route('**/api/v1/wellness/athletes/athlete-1/context**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(athleteContext),
      })
    )

    await page.route('**/api/v1/wellness/alerts/alert-1/ack', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok' }),
      })
    )
  })

  test('navigates from wellness heatmap to athlete 360 and resolves alert', async ({ page }) => {
    await page.goto('/wellness')

    await expect(page.getByRole('heading', { name: /Wellness Heatmap/i })).toBeVisible()
    await expect(page.getByText('Luca Demo')).toBeVisible()

    await page.getByRole('link', { name: /Apri Athlete 360/i }).click()
    await expect(page).toHaveURL(/\/athletes\/athlete-1/)

    await expect(page.getByRole('heading', { name: /Luca Demo/i })).toBeVisible()
    await page.getByRole('button', { name: /Prendi in carico/i }).click()

    await expect(page.getByText(/Alert risolti/)).toBeVisible()
  })
})

