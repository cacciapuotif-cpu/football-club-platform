export type SessionType = 'training' | 'match' | 'recovery' | 'other'

export type SessionListItem = {
  session_id: string
  team_id: string
  type: SessionType
  start_ts: string
  end_ts?: string | null
  rpe_avg?: number | null
  load?: number | null
  notes?: string | null
}

export type SessionsPageResponse = {
  items: SessionListItem[]
  page: number
  page_size: number
  total: number
  has_next: boolean
}

export type SessionParticipation = {
  athlete_id: string
  rpe?: number | null
  load?: number | null
  status: string
}

export type SessionDetail = {
  session: SessionListItem
  participation: SessionParticipation[]
}

export type SnapshotMetric = {
  athlete_id: string
  metric: string
  value: number
  unit?: string | null
  event_ts: string
}

export type SnapshotPrediction = {
  athlete_id: string
  score: number
  severity: 'low' | 'medium' | 'high' | 'critical'
  model_version: string
  event_ts: string
  drivers?: Record<string, unknown> | null
}

export type SnapshotAlert = {
  id: string
  athlete_id: string
  session_id?: string | null
  status: 'open' | 'acknowledged' | 'closed'
  severity: 'low' | 'medium' | 'high' | 'critical'
  opened_at: string
  closed_at?: string | null
  policy_id?: string | null
}

export type SessionWellnessSnapshot = {
  session_id: string
  window_days: number
  window_start: string
  window_end: string
  athletes: string[]
  metrics: SnapshotMetric[]
  predictions: SnapshotPrediction[]
  alerts: SnapshotAlert[]
}

export type TeamOption = {
  id: string
  name: string
}

