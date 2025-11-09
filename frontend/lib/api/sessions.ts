import type {
  SessionDetail,
  SessionWellnessSnapshot,
  SessionsPageResponse,
  TeamOption,
} from '@/types/sessions'
import type { Team } from '@/types/teams'
import { API_URL } from '../api'

const BASE_URL = API_URL || 'http://localhost:8000/api/v1'

const withAuthHeaders = (): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_SKIP_AUTH !== 'true') {
    const token = window.localStorage.getItem('access_token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
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

export const fetchSessions = async (params: {
  teamId?: string
  type?: string
  from?: string
  to?: string
  page?: number
  pageSize?: number
}): Promise<SessionsPageResponse> => {
  const url = buildUrl('/sessions', {
    teamId: params.teamId,
    type: params.type,
    from: params.from,
    to: params.to,
    page: params.page,
    pageSize: params.pageSize,
  })

  const res = await fetch(url, {
    headers: withAuthHeaders(),
  })
  return handleResponse<SessionsPageResponse>(res)
}

export const fetchSessionDetail = async (sessionId: string): Promise<SessionDetail> => {
  const url = buildUrl(`/sessions/${sessionId}`)
  const res = await fetch(url, { headers: withAuthHeaders() })
  return handleResponse<SessionDetail>(res)
}

export const fetchSessionSnapshot = async (
  sessionId: string,
  windowDays = 2
): Promise<SessionWellnessSnapshot> => {
  const url = buildUrl(`/sessions/${sessionId}/wellness_snapshot`, { window_days: windowDays })
  const res = await fetch(url, { headers: withAuthHeaders() })
  return handleResponse<SessionWellnessSnapshot>(res)
}

export const fetchTeams = async (): Promise<TeamOption[]> => {
  const url = buildUrl('/teams')
  const res = await fetch(url, { headers: withAuthHeaders() })
  const teams = await handleResponse<Team[]>(res)
  return teams.map((team) => ({
    id: team.id,
    name: [team.name, team.category].filter(Boolean).join(' • ') || 'Team',
  }))
}

