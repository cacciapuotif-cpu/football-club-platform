/**
 * Metrics API client for ACWR, Monotony, Strain, and Readiness
 */

import http from '../http'
import type { PlayerMetricsSummary, PlayerMetricsLatest } from '@/types/metrics'

/**
 * Get player metrics summary for the last N days
 */
export async function getPlayerMetricsSummary(playerId: string, days = 30): Promise<PlayerMetricsSummary> {
  const response = await http.get<PlayerMetricsSummary>(
    `/metrics/player/${playerId}/summary?days=${days}`
  )
  return response.data
}

/**
 * Get latest metrics for a player
 */
export async function getPlayerMetricsLatest(playerId: string): Promise<PlayerMetricsLatest> {
  const response = await http.get<PlayerMetricsLatest>(
    `/metrics/player/${playerId}/latest`
  )
  return response.data
}

/**
 * Trigger manual recalculation of all metrics
 */
export async function recalculateMetrics(): Promise<void> {
  await http.post('/metrics/recalculate')
}
