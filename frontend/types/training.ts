/**
 * Training types for RPE tracking and session load management
 */

export type RpeUpsertPayload = {
  player_id: string;
  session_id: string;
  rpe: number; // 0..10
};

export type RpeUpsertResponse = {
  player_id: string;
  session_id: string;
  rpe: number;
  duration_min: number;
  session_load: number;
  updated_at: string;
};

export type WeeklyLoadPoint = {
  week_start: string;      // ISO date (YYYY-MM-DD)
  weekly_load: number;     // sum session_load in that week
};

export type WeeklyLoadResponse = {
  player_id: string;
  weeks: WeeklyLoadPoint[];
  total_current_week: number;
};

export type TrainingSession = {
  id: string;
  session_date: string;
  session_type: string;
  duration_min: number;
  focus?: string;
  description?: string;
};
