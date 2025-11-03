/**
 * Types for player alerts and notifications system.
 */

export type AlertLevel = 'info' | 'warning' | 'critical';

export type PlayerAlert = {
  id: string;
  player_id: string;
  date: string;
  type: string;
  level: AlertLevel;
  message: string;
  resolved: boolean;
  created_at: string;
};

export type PlayerAlertsList = {
  player_id: string;
  alerts: PlayerAlert[];
};

export type TodayAlert = PlayerAlert & {
  player_name: string;
  jersey_number: number | null;
  role: string;
};

export type TodayAlertsList = {
  date: string;
  alerts: TodayAlert[];
};

export type ResolveAlertResponse = {
  status: string;
  message: string;
};
