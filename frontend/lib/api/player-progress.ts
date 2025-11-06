/**
 * API client for player progress endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export interface PlayerOverview {
  player_id: string
  period_days: number
  wellness_entries: number
  training_sessions: number
  matches: number
  wellness_completeness_pct: number
  training_completeness_pct: number
  match_completeness_pct: number
  family_completeness: Array<{
    family: string
    completeness_pct: number
    days_with_data: number
    total_days: number
  }>
  metric_summaries: Array<{
    metric_key: string
    current_value: number
    avg_value: number
    min_value: number
    max_value: number
    completeness_pct: number
    trend_pct: number
    variance: number
  }>
  data_quality_issues: number
}

export interface ProgressSeriesPoint {
  bucket_start: string
  [key: string]: string | number | null | undefined
}

export interface ProgressResponse {
  bucket: 'daily' | 'weekly' | 'monthly'
  date_from: string
  date_to: string
  series: ProgressSeriesPoint[]
}

export interface TrainingLoadPoint {
  date: string
  srpe: number
  acute: number | null
  chronic: number | null
  acwr: number | null
}

export interface TrainingLoadResponse {
  series: TrainingLoadPoint[]
  window_short: number
  window_long: number
  acwr_latest: number | null
  acwr_series: Array<{ date: string; value: number }>
  monotony_weekly: Array<{ week_start: string; value: number }>
  strain_weekly: Array<{ week_start: string; value: number }>
  flags: Array<{ date: string; risk: string; reason: string }>
}

export interface MatchSummaryPoint {
  match_id: string
  match_date: string
  opponent: string
  is_home: boolean
  minutes_played: number
  pass_accuracy: number | null
  passes_completed: number | null
  duels_won: number | null
  touches: number | null
  dribbles_success: number | null
  interceptions: number | null
  tackles: number | null
  shots_on_target: number | null
  pressures: number | null
  recoveries_def_third: number | null
  progressive_passes: number | null
  line_breaking_passes_conceded: number | null
  xthreat_contrib: number | null
}

export interface MatchSummaryResponse {
  player_id: string
  date_from: string
  date_to: string
  matches: MatchSummaryPoint[]
  aggregates: {
    total_matches?: number
    avg_minutes?: number
    avg_pass_accuracy?: number
    total_passes?: number
    total_duels_won?: number
    total_touches?: number
  }
}

export interface ReadinessPoint {
  date: string
  readiness: number | null
}

export interface ReadinessResponse {
  player_id: string
  date_from: string
  date_to: string
  series: ReadinessPoint[]
  latest_value: number | null
  avg_7d: number | null
}

export interface Alert {
  type: string
  metric: string
  date: string
  value: number
  threshold: string
  severity: string
}

export interface AlertsResponse {
  player_id: string
  date_from: string
  date_to: string
  alerts: Alert[]
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('access_token')
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const response = await fetch(url, { ...options, headers })
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  
  return response.json()
}

export async function getPlayerOverview(
  playerId: string,
  period: '7d' | '28d' | '30d' | '90d' = '28d'
): Promise<PlayerOverview> {
  return fetchWithAuth(`${API_BASE}/players/${playerId}/overview?period=${period}`)
}

export async function getPlayerProgress(
  playerId: string,
  params: {
    date_from?: string
    date_to?: string
    families?: string
    metrics?: string
    grouping?: 'day' | 'week' | 'month'
  }
): Promise<ProgressResponse> {
  const queryParams = new URLSearchParams()
  if (params.date_from) queryParams.set('date_from', params.date_from)
  if (params.date_to) queryParams.set('date_to', params.date_to)
  if (params.families) queryParams.set('families', params.families)
  if (params.metrics) queryParams.set('metrics', params.metrics)
  if (params.grouping) queryParams.set('grouping', params.grouping)
  
  return fetchWithAuth(`${API_BASE}/players/${playerId}/progress?${queryParams.toString()}`)
}

export async function getPlayerTrainingLoad(
  playerId: string,
  params: {
    window_short?: number
    window_long?: number
  } = {}
): Promise<TrainingLoadResponse> {
  const queryParams = new URLSearchParams()
  if (params.window_short) queryParams.set('window_short', params.window_short.toString())
  if (params.window_long) queryParams.set('window_long', params.window_long.toString())
  
  return fetchWithAuth(`${API_BASE}/players/${playerId}/training-load?${queryParams.toString()}`)
}

export async function getPlayerMatchSummary(
  playerId: string,
  params: {
    date_from?: string
    date_to?: string
  } = {}
): Promise<MatchSummaryResponse> {
  const queryParams = new URLSearchParams()
  if (params.date_from) queryParams.set('date_from', params.date_from)
  if (params.date_to) queryParams.set('date_to', params.date_to)
  
  return fetchWithAuth(`${API_BASE}/players/${playerId}/match-summary?${queryParams.toString()}`)
}

export async function getPlayerReadiness(
  playerId: string,
  params: {
    date_from?: string
    date_to?: string
  } = {}
): Promise<ReadinessResponse> {
  const queryParams = new URLSearchParams()
  if (params.date_from) queryParams.set('date_from', params.date_from)
  if (params.date_to) queryParams.set('date_to', params.date_to)
  
  return fetchWithAuth(`${API_BASE}/players/${playerId}/readiness?${queryParams.toString()}`)
}

export async function getPlayerAlerts(
  playerId: string,
  params: {
    date_from?: string
    date_to?: string
  } = {}
): Promise<AlertsResponse> {
  const queryParams = new URLSearchParams()
  if (params.date_from) queryParams.set('date_from', params.date_from)
  if (params.date_to) queryParams.set('date_to', params.date_to)
  
  return fetchWithAuth(`${API_BASE}/players/${playerId}/alerts?${queryParams.toString()}`)
}

