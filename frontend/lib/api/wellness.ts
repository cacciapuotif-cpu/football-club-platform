/**
 * Wellness API client
 * Centralizes all wellness-related API calls
 */

import http from '../http'
import type {
  WellnessSummary,
  WellnessEntry,
  WellnessSummaryParams,
  PlayerWellnessParams,
  TeamWellnessHeatmap,
  AthleteReadinessSeries,
  AthleteContextResponse,
  WellnessPolicy,
} from '@/types/wellness'
import { API_URL } from '../api'

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

const BASE_URL = API_URL || 'http://localhost:8000/api/v1'

const authHeaders = (): HeadersInit => {
  const headers: HeadersInit = { 'Content-Type': 'application/json' }
  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_SKIP_AUTH !== 'true') {
    const token = window.localStorage.getItem('access_token')
    if (token) headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

const buildUrl = (path: string, params?: Record<string, string | number | undefined | null>) => {
  const url = new URL(path, BASE_URL)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value))
      }
    })
  }
  return url.toString()
}

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `API request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const fetchTeamHeatmap = async (teamId: string, targetDate: string): Promise<TeamWellnessHeatmap> => {
  const url = buildUrl(`/wellness/teams/${teamId}/heatmap`, { target_date: targetDate })
  const res = await fetch(url, { headers: authHeaders() })
  return handleResponse<TeamWellnessHeatmap>(res)
}

export const fetchAthleteReadiness = async (
  athleteId: string,
  range?: { from?: string; to?: string }
): Promise<AthleteReadinessSeries> => {
  const url = buildUrl(`/wellness/athletes/${athleteId}/readiness`, {
    from: range?.from,
    to: range?.to,
  })
  const res = await fetch(url, { headers: authHeaders() })
  return handleResponse<AthleteReadinessSeries>(res)
}

export const fetchAthleteContext = async (athleteId: string, days = 7): Promise<AthleteContextResponse> => {
  const url = buildUrl(`/wellness/athletes/${athleteId}/context`, { days })
  const res = await fetch(url, { headers: authHeaders() })
  return handleResponse<AthleteContextResponse>(res)
}

export const acknowledgeAlert = async (alertId: string): Promise<void> => {
  const url = buildUrl(`/wellness/alerts/${alertId}/ack`)
  const res = await fetch(url, {
    method: 'POST',
    headers: authHeaders(),
  })
  await handleResponse<{ status: string }>(res)
}

export const fetchWellnessPolicies = async (): Promise<WellnessPolicy[]> => {
  const url = buildUrl('/wellness/policies')
  const res = await fetch(url, { headers: authHeaders() })
  return handleResponse<WellnessPolicy[]>(res)
}
