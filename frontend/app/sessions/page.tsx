'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { SessionCalendar } from '@/components/sessions/SessionCalendar'
import { SessionFilters } from '@/components/sessions/SessionFilters'
import { SessionList } from '@/components/sessions/SessionList'
import { fetchSessions, fetchTeams } from '@/lib/api/sessions'
import type { SessionListItem } from '@/types/sessions'
import type { Team } from '@/types/teams'
import { useI18n } from '@/lib/i18n/I18nProvider'
import { useTheme } from '@/lib/theme/ThemeProvider'

type ViewMode = 'list' | 'calendar'

const PAGE_SIZE = 25

export default function SessionsPage() {
  const [sessions, setSessions] = useState<SessionListItem[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingTeams, setLoadingTeams] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>('list')

  const [filters, setFilters] = useState<{
    teamId?: string
    type: 'all' | 'training' | 'match' | 'recovery' | 'other'
    from?: string
    to?: string
  }>({
    teamId: undefined,
    type: 'all',
    from: undefined,
    to: undefined,
  })

  const loadSessions = useCallback(
    async (opts?: { append?: boolean; pageOverride?: number }) => {
      try {
        setLoading(true)
        setError(null)

        const currentPage = opts?.pageOverride ?? page
        const response = await fetchSessions({
          teamId: filters.teamId || undefined,
          type: filters.type !== 'all' ? filters.type : undefined,
          from: filters.from || undefined,
          to: filters.to || undefined,
          page: currentPage,
          pageSize: PAGE_SIZE,
        })

        setHasNext(response.has_next)
        setSessions((prev) => (opts?.append ? [...prev, ...response.items] : response.items))
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Errore durante il caricamento delle sessioni'
        setError(message)
        setSessions([])
        setHasNext(false)
      } finally {
        setLoading(false)
      }
    },
    [filters.teamId, filters.type, filters.from, filters.to, page]
  )

  useEffect(() => {
    const initializeTeams = async () => {
      try {
        setLoadingTeams(true)
        const fetchedTeams = await fetchTeams()
        setTeams(
          fetchedTeams.map((team) => ({
            id: team.id,
            name: team.name,
          }))
        )
      } catch (err) {
        console.warn('[Sessions] Impossibile caricare le squadre', err)
      } finally {
        setLoadingTeams(false)
      }
    }
    initializeTeams()
  }, [])

  useEffect(() => {
    setPage(1)
    loadSessions({ append: false, pageOverride: 1 })
  }, [filters.teamId, filters.type, filters.from, filters.to, loadSessions])

  useEffect(() => {
    if (page === 1) return
    loadSessions({ append: true, pageOverride: page })
  }, [page, loadSessions])

  const teamOptions = useMemo(
    () =>
      teams.map((team) => ({
        id: team.id,
        name: team.name,
      })),
    [teams]
  )

  const { t } = useI18n()
  const { primaryColor } = useTheme()

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold" style={{ color: primaryColor }}>
          {t('sessions.title', 'Programmazione Sessioni')}
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          {t(
            'sessions.subtitle',
            'Visualizza e filtra le sessioni di allenamento e partita. Passa rapidamente alla visuale calendario per pianificare microcicli e collegarti alle analisi Wellness.'
          )}
        </p>
      </header>

      <SessionFilters
        teamId={filters.teamId}
        onTeamChange={(value) => setFilters((prev) => ({ ...prev, teamId: value || undefined }))}
        sessionType={filters.type}
        onTypeChange={(value) => setFilters((prev) => ({ ...prev, type: value }))}
        from={filters.from}
        to={filters.to}
        onDateChange={(range) => setFilters((prev) => ({ ...prev, ...range }))}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        teams={teamOptions}
        loadingTeams={loadingTeams}
      />

      {viewMode === 'list' ? (
        <>
          <SessionList sessions={sessions} loading={loading && page === 1} error={error} />
          {hasNext && (
            <div className="mt-6 flex justify-center">
              <button
                type="button"
                onClick={() => setPage((prev) => prev + 1)}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
                disabled={loading}
              >
                {loading
                  ? t('sessions.loadMoreLoading', 'Caricamento…')
                  : t('sessions.loadMore', 'Carica altre sessioni')}
              </button>
            </div>
          )}
        </>
      ) : (
        <div className={loading && page === 1 ? 'opacity-60' : ''}>
          <SessionCalendar sessions={sessions} />
        </div>
      )}
    </div>
  )
}
