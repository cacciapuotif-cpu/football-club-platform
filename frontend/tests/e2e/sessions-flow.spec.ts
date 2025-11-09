import { test, expect } from '@playwright/test'

const mockTeams = [
  { id: 'team-1', name: 'Primavera' },
  { id: 'team-2', name: 'U18 Elite' },
]

const sessionsPageResponse = {
  items: [
    {
      session_id: 'session-123',
      team_id: 'team-1',
      type: 'training',
      start_ts: new Date().toISOString(),
      end_ts: null,
      rpe_avg: 6.2,
      load: 420,
      notes: 'Rifinitura tecnico-tattica',
    },
  ],
  page: 1,
  page_size: 25,
  total: 1,
  has_next: false,
}

const sessionDetailResponse = {
  session: sessionsPageResponse.items[0],
  participation: [
    { athlete_id: 'athlete-1', rpe: 6.5, load: 430, status: 'COMPLETED' },
    { athlete_id: 'athlete-2', rpe: 5.5, load: 380, status: 'COMPLETED' },
  ],
}

const sessionSnapshotResponse = {
  session_id: 'session-123',
  window_days: 2,
  window_start: new Date(Date.now() - 2 * 24 * 3600 * 1000).toISOString(),
  window_end: new Date(Date.now() + 2 * 24 * 3600 * 1000).toISOString(),
  athletes: ['athlete-1', 'athlete-2'],
  metrics: [],
  predictions: [
    { athlete_id: 'athlete-1', score: 62, severity: 'medium', model_version: '1.0', event_ts: new Date().toISOString(), drivers: { acwr: 1.4 } },
  ],
  alerts: [
    {
      id: 'alert-10',
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
  ],
  readiness_trend: [
    { event_ts: new Date(Date.now() - 24 * 3600 * 1000).toISOString(), readiness_score: 64, severity: 'medium' },
    { event_ts: new Date().toISOString(), readiness_score: 62, severity: 'medium' },
  ],
  recent_sessions: [
    {
      session_id: 'session-123',
      start_ts: new Date().toISOString(),
      type: 'training',
      load: 420,
      rpe: 6.2,
      minutes: 90,
    },
  ],
  alerts: sessionSnapshotResponse.alerts,
}

test.describe('Sessions to Athlete 360 flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/teams', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockTeams) })
    )

    await page.route('**/api/v1/sessions?**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(sessionsPageResponse) })
    )

    await page.route('**/api/v1/sessions/session-123', (route) => {
      const url = route.request().url()
      if (url.endsWith('/wellness_snapshot') || url.includes('/wellness_snapshot?')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(sessionSnapshotResponse),
        })
      }

      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(sessionDetailResponse),
      })
    })

    await page.route('**/api/v1/wellness/athletes/athlete-1/context**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(athleteContext) })
    )

    await page.route('**/api/v1/wellness/alerts/alert-10/ack', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok' }),
      })
    )
  })

  test('opens session detail and deep-links into Athlete 360', async ({ page }) => {
    await page.goto('/sessions')

    await expect(page.getByRole('heading', { name: /Programmazione Sessioni/i })).toBeVisible()
    await expect(page.getByText(/Rifinitura tecnico-tattica/i)).toBeVisible()

    await page.getByRole('link', { name: /Rifinitura tecnico-tattica/i }).click()
    await expect(page).toHaveURL(/\/sessions\/session-123/)

    await expect(page.getByRole('heading', { name: /Wellness Snapshot/i })).toBeVisible()
    await expect(page.getByText(/Load 420/)).toBeVisible()

    await page.getByRole('link', { name: /Vai a Athlete 360/i }).click()
    await expect(page).toHaveURL(/\/athletes\/athlete-1/)
    await expect(page.getByRole('heading', { name: /Luca Demo/i })).toBeVisible()
  })
})

