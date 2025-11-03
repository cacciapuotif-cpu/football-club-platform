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
