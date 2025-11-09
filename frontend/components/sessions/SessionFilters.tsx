'use client'

import { useMemo } from 'react'
import type { SessionType, TeamOption } from '@/types/sessions'
import { useI18n } from '@/lib/i18n/I18nProvider'

type SessionFiltersProps = {
  teamId?: string
  onTeamChange: (teamId: string) => void
  sessionType?: SessionType | 'all'
  onTypeChange: (type: SessionType | 'all') => void
  from?: string
  to?: string
  onDateChange: (range: { from?: string; to?: string }) => void
  viewMode: 'list' | 'calendar'
  onViewModeChange: (mode: 'list' | 'calendar') => void
  teams: TeamOption[]
  loadingTeams?: boolean
}

export function SessionFilters({
  teamId,
  onTeamChange,
  sessionType = 'all',
  onTypeChange,
  from,
  to,
  onDateChange,
  viewMode,
  onViewModeChange,
  teams,
  loadingTeams = false,
}: SessionFiltersProps) {
  const { t } = useI18n()
  const fallbackTypeLabels: Record<SessionType, string> = {
    training: 'Allenamento',
    match: 'Partita',
    recovery: 'Recupero',
    other: 'Altro',
  }
  const typeOptions = useMemo(() => ['all', 'training', 'match', 'recovery', 'other'] as const, [])

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6 mb-6 space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <div>
          <label htmlFor="team" className="block text-sm font-medium text-gray-700 mb-1">
            {t('sessions.header.team', 'Squadra')}
          </label>
          <select
            id="team"
            value={teamId ?? ''}
            onChange={(event) => onTeamChange(event.target.value)}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            disabled={loadingTeams}
          >
            <option value="">Tutte le squadre</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-1">
            {t('sessions.header.date', 'Data')}
          </span>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={from ?? ''}
              onChange={(event) => onDateChange({ from: event.target.value, to })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <span className="text-gray-500 text-sm">→</span>
            <input
              type="date"
              value={to ?? ''}
              onChange={(event) => onDateChange({ from, to: event.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-1">
            {t('sessions.header.type', 'Tipo di sessione')}
          </label>
          <select
            id="type"
            value={sessionType}
            onChange={(event) => onTypeChange(event.target.value as SessionType | 'all')}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {typeOptions.map((type) => (
              <option key={type} value={type}>
                {type === 'all'
                  ? t('sessions.filter.all', 'Tutte le squadre')
                  : t(`sessions.type.${type}`, fallbackTypeLabels[type as SessionType])}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-500">
          {t('sessions.view.current', 'Vista corrente')}: <span className="font-medium text-gray-700">{t(
            viewMode === 'list' ? 'sessions.view.list' : 'sessions.view.calendar',
            viewMode === 'list' ? 'Lista' : 'Calendario'
          )}</span>
        </div>
        <div className="inline-flex rounded-md shadow-sm" role="group">
          <button
            type="button"
            onClick={() => onViewModeChange('list')}
            className={`px-3 py-2 text-sm font-medium border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              viewMode === 'list' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            {t('sessions.view.list', 'Lista')}
          </button>
          <button
            type="button"
            onClick={() => onViewModeChange('calendar')}
            className={`px-3 py-2 text-sm font-medium border border-gray-300 rounded-r-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              viewMode === 'calendar'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            {t('sessions.view.calendar', 'Calendario')}
          </button>
        </div>
      </div>
    </div>
  )
}

