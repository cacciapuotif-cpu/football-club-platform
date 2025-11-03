/**
 * Training API client for RPE tracking and session load management
 */

import http from '../http'
import type { RpeUpsertPayload, RpeUpsertResponse, WeeklyLoadResponse, TrainingSession } from '@/types/training'

/**
 * Upsert RPE for a player session
 */
export async function upsertRpe(payload: RpeUpsertPayload): Promise<RpeUpsertResponse> {
  const response = await http.post<RpeUpsertResponse>('/training/rpe', payload)
  return response.data
}

/**
 * Get weekly load aggregates for a player
 */
export async function getPlayerWeeklyLoad(playerId: string, weeks = 8): Promise<WeeklyLoadResponse> {
  const response = await http.get<WeeklyLoadResponse>(
    `/training/players/${playerId}/weekly-load?weeks=${weeks}`
  )
  return response.data
}

/**
 * Get recent training sessions (for RPE form)
 * Note: This uses the existing sessions endpoint
 */
export async function getRecentSessions(daysBack = 7): Promise<TrainingSession[]> {
  const fromDate = new Date()
  fromDate.setDate(fromDate.getDate() - daysBack)

  const response = await http.get<TrainingSession[]>(
    `/sessions/?from=${fromDate.toISOString().split('T')[0]}`
  )
  return response.data
}
