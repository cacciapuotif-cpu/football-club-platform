'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { format } from 'date-fns'
import { it } from 'date-fns/locale'
import { HeatmapGrid } from '@/components/wellness/HeatmapGrid'
import { fetchTeamHeatmap, fetchWellnessPolicies } from '@/lib/api/wellness'
import { fetchTeams } from '@/lib/api/sessions'
import type { HeatmapCell, WellnessPolicy } from '@/types/wellness'
import type { TeamOption } from '@/types/sessions'
import { useI18n } from '@/lib/i18n/I18nProvider'
import { useTheme } from '@/lib/theme/ThemeProvider'

const formatDate = (value: string | Date) =>
  format(new Date(value), "EEEE d MMM yyyy", { locale: it })

export default function WellnessPage() {
  const { t } = useI18n()
  const { primaryColor, accentColor } = useTheme()
  const [teams, setTeams] = useState<TeamOption[]>([])
  const [teamId, setTeamId] = useState<string>('')
  const [targetDate, setTargetDate] = useState<string>(() => new Date().toISOString().slice(0, 10))

  const [cells, setCells] = useState<HeatmapCell[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [policies, setPolicies] = useState<WellnessPolicy[]>([])

  const loadTeams = useCallback(async () => {
    try {
      const fetchedTeams = await fetchTeams()
      setTeams(fetchedTeams)
      if (!teamId && fetchedTeams.length) {
        setTeamId(fetchedTeams[0].id)
      }
    } catch (err) {
      console.warn('[Wellness] Impossibile caricare le squadre', err)
      setTeams([])
    }
  }, [teamId])

  const loadHeatmap = useCallback(async () => {
    if (!teamId) return
    try {
      setLoading(true)
      setError(null)
      const response = await fetchTeamHeatmap(teamId, targetDate)
      setCells(response.cells)
    } catch (err) {
      const message = t('wellness.error', 'Impossibile caricare la heatmap wellness')
      setError(message)
      setCells([])
    } finally {
      setLoading(false)
    }
  }, [teamId, targetDate, t])

  const loadPolicies = useCallback(async () => {
    try {
      const data = await fetchWellnessPolicies()
      setPolicies(data)
    } catch (err) {
      console.warn('[Wellness] Impossibile caricare le policy wellness', err)
    }
  }, [])

  useEffect(() => {
    loadTeams()
    loadPolicies()
  }, [loadTeams, loadPolicies])

  useEffect(() => {
    loadHeatmap()
  }, [loadHeatmap])

  const selectedTeamName = useMemo(() => teams.find((team) => team.id === teamId)?.name ?? '—', [teams, teamId])

  return (
    <div className="container mx-auto px-4 py-10">
      <header className="mb-8">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold" style={{ color: primaryColor }}>
              {t('wellness.title', 'Wellness Heatmap')}
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-gray-600">
              {t(
                'wellness.subtitle',
                'Controlla readiness, alert attivi e variazioni giorno su giorno per ogni atleta. Seleziona la squadra e il giorno di interesse per preparare il briefing di staff o seguire l’andamento di microcicli e viaggi.'
              )}
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <label className="flex items-center gap-2 text-sm text-gray-600">
              {t('sessions.header.team', 'Squadra')}
              <select
                value={teamId}
                onChange={(event) => setTeamId(event.target.value)}
                className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-600">
              {t('sessions.header.date', 'Data')}
              <input
                type="date"
                value={targetDate}
                onChange={(event) => setTargetDate(event.target.value)}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </label>
          </div>
        </div>
        <p className="mt-4 text-xs text-gray-500">
          Vista corrente: <span className="font-semibold text-gray-700">{selectedTeamName}</span> •{' '}
          {formatDate(targetDate)}
        </p>
      </header>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <div className="flex items-center justify-between">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => {
                setError(null)
                loadHeatmap()
              }}
              className="text-xs font-semibold text-red-700 underline"
            >
              {t('common.retry', 'Riprova')}
            </button>
          </div>
        </div>
      )}

      <HeatmapGrid cells={cells} loading={loading && !cells.length} emptyMessage={t('wellness.empty', 'Nessun atleta registrato per questa squadra.')} />

      {policies.length > 0 && (
        <section className="mt-10 rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <header className="mb-4">
            <h2 className="text-sm font-semibold uppercase tracking-wide" style={{ color: accentColor }}>
              {t('wellness.policy.heading', 'Policy di alert e soglie')}
            </h2>
          </header>
          <div className="grid gap-4 md:grid-cols-2">
            {policies.map((policy) => (
              <div key={policy.id} className="rounded-md border border-gray-100 bg-gray-50/80 p-4">
                <p className="text-sm font-semibold text-gray-900">{policy.name}</p>
                {policy.description && <p className="mt-1 text-xs text-gray-600">{policy.description}</p>}
                <div className="mt-3 text-xs text-gray-500">
                  <p>Cooldown: {policy.cooldown_hours}h</p>
                  <p>Completezza minima dati: {(policy.min_data_completeness * 100).toFixed(0)}%</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
