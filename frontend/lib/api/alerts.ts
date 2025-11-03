/**
 * API client for player alerts and notifications.
 */

import { http } from '@/lib/http';
import type { PlayerAlertsList, TodayAlertsList, ResolveAlertResponse } from '@/types/alerts';

/**
 * Get alerts for a specific player.
 * @param playerId - UUID of the player
 * @param days - Number of days to retrieve (default: 14)
 */
export async function getPlayerAlerts(playerId: string, days: number = 14): Promise<PlayerAlertsList> {
  const response = await http.get<PlayerAlertsList>(`/alerts/player/${playerId}?days=${days}`);
  return response.data;
}

/**
 * Get all alerts for today across all players.
 * @param resolved - Include resolved alerts (default: false)
 */
export async function getTodayAlerts(resolved: boolean = false): Promise<TodayAlertsList> {
  const response = await http.get<TodayAlertsList>(`/alerts/today?resolved=${resolved}`);
  return response.data;
}

/**
 * Mark an alert as resolved.
 * @param alertId - UUID of the alert to resolve
 */
export async function resolveAlert(alertId: string): Promise<ResolveAlertResponse> {
  const response = await http.patch<ResolveAlertResponse>(`/alerts/${alertId}/resolve`);
  return response.data;
}

/**
 * Manually trigger alert generation for all players.
 * Used by admins or for testing.
 */
export async function triggerAlertGeneration(): Promise<{ status: string; message: string }> {
  const response = await http.post<{ status: string; message: string }>('/alerts/generate');
  return response.data;
}
