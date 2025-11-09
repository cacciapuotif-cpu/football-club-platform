/**
 * Wellness data types for the new summary table and detail drawer.
 */

export type WellnessSummary = {
  player_id: string;
  cognome: string;
  nome: string;
  ruolo: string;
  wellness_sessions_count: number;
  last_entry_date: string | null;
};

export type WellnessEntry = {
  date: string;
  sleep_h: number | null;
  sleep_quality: number | null;
  fatigue: number | null;
  stress: number | null;
  mood: number | null;
  doms: number | null;
  weight_kg: number | null;
  notes: string | null;
};

/**
 * Query parameters for wellness summary API
 */
export type WellnessSummaryParams = {
  from?: string; // ISO date string
  to?: string; // ISO date string
  role?: 'GK' | 'DF' | 'MF' | 'FW';
  search?: string;
  page?: number;
  page_size?: number;
  sort?: 'cognome_asc' | 'cognome_desc' | 'sessions_desc' | 'sessions_asc' | 'last_entry_desc' | 'last_entry_asc';
};

/**
 * Query parameters for player wellness entries API
 */
export type PlayerWellnessParams = {
  from?: string; // ISO date string
  to?: string; // ISO date string
  page?: number;
  page_size?: number;
};

export type HeatmapCell = {
  athlete_id: string;
  player_id?: string | null;
  full_name?: string | null;
  role?: string | null;
  readiness_score?: number | null;
  risk_severity?: 'low' | 'medium' | 'high' | 'critical' | null;
  alerts_count: number;
  latest_alert_at?: string | null;
  readiness_delta?: number | null;
};

export type TeamWellnessHeatmap = {
  team_id: string;
  date: string;
  cells: HeatmapCell[];
};

export type ReadinessTrendPoint = {
  event_ts: string;
  readiness_score?: number | null;
  severity?: 'low' | 'medium' | 'high' | 'critical' | null;
};

export type AthleteReadinessSeries = {
  athlete_id: string;
  points: ReadinessTrendPoint[];
};

export type RecentSessionSummary = {
  session_id: string;
  start_ts: string;
  type: 'training' | 'match' | 'recovery' | 'other';
  load?: number | null;
  rpe?: number | null;
  minutes?: number | null;
};

export type FeatureSnapshot = {
  feature_name: string;
  feature_value: number;
  event_ts: string;
};

export type AthleteContextResponse = {
  athlete_id: string;
  player: {
    player_id?: string | null;
    full_name?: string | null;
    role?: string | null;
    team_id?: string | null;
  };
  range_start: string;
  range_end: string;
  latest_features: FeatureSnapshot[];
  readiness_trend: ReadinessTrendPoint[];
  recent_sessions: RecentSessionSummary[];
  alerts: {
    id: string;
    athlete_id: string;
    session_id?: string | null;
    status: 'open' | 'acknowledged' | 'closed';
    severity: 'low' | 'medium' | 'high' | 'critical';
    opened_at: string;
    closed_at?: string | null;
    policy_id?: string | null;
  }[];
};

export type WellnessPolicy = {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  thresholds?: Record<string, unknown> | null;
  cooldown_hours: number;
  min_data_completeness: number;
  created_at: string;
  updated_at: string;
};