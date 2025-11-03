/**
 * Wellness API client
 * Centralizes all wellness-related API calls
 */

import http from '../http'
import type { WellnessSummary, WellnessEntry, WellnessSummaryParams, PlayerWellnessParams } from '@/types/wellness'

/**
 * Get wellness summary (player list with session counts)
 */
export async function getWellnessSummary(params: WellnessSummaryParams = {}): Promise<WellnessSummary[]> {
  const queryParams = new URLSearchParams()

  if (params.from) queryParams.set('from', params.from)
  if (params.to) queryParams.set('to', params.to)
  if (params.role) queryParams.set('role', params.role)
  if (params.search) queryParams.set('search', params.search)
  if (params.page) queryParams.set('page', params.page.toString())
  if (params.page_size) queryParams.set('page_size', params.page_size.toString())
  if (params.sort) queryParams.set('sort', params.sort)

  const queryString = queryParams.toString()
  const url = queryString ? `/wellness/summary?${queryString}` : '/wellness/summary'

  // DIAGNOSTICS: Log API call
  console.info('[API][GET]', http.defaults.baseURL + url, { params })

  const response = await http.get<WellnessSummary[]>(url)
  console.info('[API][RESPONSE]', url, { count: response.data.length })
  return response.data
}

/**
 * Get wellness entries for a specific player
 */
export async function getPlayerWellnessEntries(
  playerId: string,
  params: PlayerWellnessParams = {}
): Promise<WellnessEntry[]> {
  const queryParams = new URLSearchParams()

  if (params.from) queryParams.set('from', params.from)
  if (params.to) queryParams.set('to', params.to)
  if (params.page) queryParams.set('page', params.page.toString())
  if (params.page_size) queryParams.set('page_size', params.page_size.toString())

  const queryString = queryParams.toString()
  const url = queryString
    ? `/wellness/player/${playerId}?${queryString}`
    : `/wellness/player/${playerId}`

  // DIAGNOSTICS: Log API call
  console.info('[API][GET]', http.defaults.baseURL + url, { playerId, params })

  const response = await http.get<WellnessEntry[]>(url)
  console.info('[API][RESPONSE]', url, { count: response.data.length })
  return response.data
}

/**
 * API base URL (for direct fetch if needed)
 */
export const API_BASE = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
