'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { it } from 'date-fns/locale'
import { acknowledgeAlert, fetchAthleteContext } from '@/lib/api/wellness'
import type { AthleteContextResponse, ReadinessTrendPoint } from '@/types/wellness'
import { useI18n } from '@/lib/i18n/I18nProvider'
import { useTheme } from '@/lib/theme/ThemeProvider'

type Props = {
  params: { athleteId: string }
}

type TabKey = 'wellness' | 'sessions'

const severityClass: Record<string, string> = {
  low: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

const formatTimestamp = (value: string) => format(new Date(value), "d MMM yyyy 'alle' HH:mm", { locale: it })

const buildTrendPolyline = (points: ReadinessTrendPoint[]): string => {
  if (!points.length) return ''
  const scores = points.map((point) => point.readiness_score ?? 0)
  const max = Math.max(...scores)
  const min = Math.min(...scores)
  const range = max - min || 1
  return points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * 100
      const y = 100 - (((point.readiness_score ?? 0) - min) / range) * 100
      return `${x},${y}`
    })
    .join(' ')
}

export default function AthletePage({ params }: Props) {
  const [context, setContext] = useState<AthleteContextResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<TabKey>('wellness')
  const [ackPending, setAckPending] = useState<string | null>(null)

  const { t } = useI18n()
  const { accentColor } = useTheme()

  const loadContext = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetchAthleteContext(params.athleteId, 14)
      setContext(response)
    } catch (err) {
      const message = t('athlete360.error', 'Impossibile caricare i dati athlete 360')
      setError(message)
      setContext(null)
    } finally {
      setLoading(false)
    }
  }, [params.athleteId, t])

  useEffect(() => {
    loadContext()
  }, [loadContext])

  const handleAcknowledge = async (alertId: string) => {
    try {
      setAckPending(alertId)
      await acknowledgeAlert(alertId)
      await loadContext()
    } catch (err) {
      const message = t('athlete360.alerts.error', 'Errore nella presa in carico dell’allerta')
      setError(message)
    } finally {
      setAckPending(null)
    }
  }

  const readinessPolyline = useMemo(
    () => (context ? buildTrendPolyline(context.readiness_trend) : ''),
    [context]
  )

  if (loading && !context) {
    return (
      <div className="container mx-auto px-4 py-10">
        <div className="space-y-4">
          <div className="h-8 w-56 animate-pulse rounded bg-gray-200" />
          <div className="h-56 animate-pulse rounded-lg bg-gray-100" />
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="h-32 animate-pulse rounded-lg bg-gray-100" />
            <div className="h-32 animate-pulse rounded-lg bg-gray-100" />
          </div>
        </div>
      </div>
    )
  }

  if (error && !context) {
    return (
      <div className="container mx-auto px-4 py-10">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          <p className="font-semibold">Impossibile caricare Athlete 360</p>
          <p className="mt-2">{error}</p>
          <div className="mt-4">
            <button
              type="button"
              onClick={loadContext}
              className="rounded bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-700"
            >
              Riprova
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!context) return null

  const openAlerts = context.alerts.filter((alert) => alert.status === 'open')
  const closedAlerts = context.alerts.filter((alert) => alert.status !== 'open')

  return (
    <div className="container mx-auto px-4 py-10">
      <header className="mb-8 border-b border-gray-200 pb-6">
        <p className="text-sm text-gray-500">{t('athlete360.title', 'Athlete 360')}</p>
        <h1 className="mt-1 text-3xl font-semibold text-gray-900">
          {context.player.full_name ?? `Athlete ${context.athlete_id.slice(0, 8)}`}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          {context.player.role ?? 'Ruolo non assegnato'} • Range analizzato:{' '}
          {formatTimestamp(context.range_start)} → {formatTimestamp(context.range_end)}
        </p>
        {error && (
          <p className="mt-3 rounded bg-red-50 px-3 py-2 text-xs text-red-600">
            {error}
          </p>
        )}
      </header>

      <div className="mb-6 flex gap-2">
        <button
          type="button"
          onClick={() => setTab('wellness')}
          className={`rounded-md px-4 py-2 text-sm font-semibold ${
            tab === 'wellness'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 shadow-sm ring-1 ring-gray-200 hover:bg-gray-50'
          }`}
        >
          {t('athlete360.tabs.wellness', 'Wellness & Readiness')}
        </button>
        <button
          type="button"
          onClick={() => setTab('sessions')}
          className={`rounded-md px-4 py-2 text-sm font-semibold ${
            tab === 'sessions'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 shadow-sm ring-1 ring-gray-200 hover:bg-gray-50'
          }`}
        >
          {t('athlete360.tabs.sessions', 'Sessioni recenti')}
        </button>
      </div>

      {tab === 'wellness' && (
        <div className="space-y-6">
          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <header className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wide" style={{ color: accentColor }}>
                  Readiness Trend
                </h2>
                <p className="text-xs text-gray-500">
                  Valori readiness (0-100) • ultimi {context.readiness_trend.length} punti
                </p>
              </div>
            </header>
            {context.readiness_trend.length ? (
              <div className="relative h-40 w-full">
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-full w-full text-blue-500">
                  <polyline
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    points={readinessPolyline}
                  />
                </svg>
                <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-gray-500">
                  <span>{format(new Date(context.readiness_trend[0].event_ts), 'd MMM', { locale: it })}</span>
                  <span>
                    {format(
                      new Date(context.readiness_trend[context.readiness_trend.length - 1].event_ts),
                      'd MMM',
                      { locale: it }
                    )}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500">Nessun dato readiness disponibile.</p>
            )}
          </section>

          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <header className="mb-4">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                Feature Snapshot
              </h2>
            </header>
            {context.latest_features.length ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {context.latest_features.map((feature) => (
                  <div key={`${feature.feature_name}-${feature.event_ts}`} className="rounded border border-gray-100 bg-gray-50 p-4">
                    <p className="text-xs uppercase text-gray-500">{feature.feature_name}</p>
                    <p className="mt-2 text-xl font-semibold text-gray-900">{feature.feature_value.toFixed(2)}</p>
                    <p className="mt-1 text-[11px] text-gray-500">
                      Aggiornato il {formatTimestamp(feature.event_ts)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">Feature non disponibili.</p>
            )}
          </section>

          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <header className="mb-4 flex items-start justify-between">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-600">Alert</h2>
                <p className="text-xs text-gray-500">
                  {openAlerts.length} aperti · {closedAlerts.length} storici
                </p>
              </div>
            </header>
            <div className="space-y-3">
              {openAlerts.length === 0 && (
                <p className="text-sm text-gray-500">{t('athlete360.alerts.none', 'Nessun alert aperto 🎉')}</p>
              )}
              {openAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex flex-col gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700 md:flex-row md:items-center md:justify-between"
                >
                  <div>
                    <p className="font-semibold">{alert.policy_id ?? 'Alert'}</p>
                    <p className="text-xs text-red-600">Aperto il {formatTimestamp(alert.opened_at)}</p>
                    {alert.session_id && (
                      <Link
                        href={`/sessions/${alert.session_id}`}
                        className="mt-1 inline-flex items-center text-xs font-semibold text-red-600 underline"
                      >
                        Vai alla sessione →
                      </Link>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleAcknowledge(alert.id)}
                    disabled={ackPending === alert.id}
                    className="rounded bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-red-300"
                  >
                    {ackPending === alert.id
                      ? '...'
                      : t('athlete360.alerts.resolve', 'Prendi in carico')}
                  </button>
                </div>
              ))}

              {closedAlerts.length > 0 && (
                <details className="rounded-md border border-gray-100 bg-gray-50 p-3 text-xs text-gray-600">
                  <summary className="cursor-pointer font-semibold text-gray-700">Alert risolti ({closedAlerts.length})</summary>
                  <ul className="mt-2 space-y-1">
                    {closedAlerts.map((alert) => (
                      <li key={alert.id} className="flex items-center justify-between">
                        <span>
                          {alert.policy_id ?? 'Alert'} · chiuso il{' '}
                          {alert.closed_at ? formatTimestamp(alert.closed_at) : '—'}
                        </span>
                        <span className={`rounded-full px-2 py-0.5 ${severityClass[alert.severity] ?? 'bg-gray-100 text-gray-700'}`}>
                          {alert.severity}
                        </span>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          </section>
        </div>
      )}

      {tab === 'sessions' && (
        <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <header className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-600">
                Sessioni recenti
              </h2>
              <p className="text-xs text-gray-500">Ultime {context.recent_sessions.length} sessioni registrate</p>
            </div>
          </header>
          {context.recent_sessions.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-100 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">
                      Data
                    </th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">
                      Tipo
                    </th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">
                      Load
                    </th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">
                      RPE
                    </th>
                    <th scope="col" className="px-4 py-3 text-right font-medium text-gray-500">
                      Azioni
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {context.recent_sessions.map((session) => (
                    <tr key={session.session_id}>
                      <td className="px-4 py-3 text-gray-700">{formatTimestamp(session.start_ts)}</td>
                      <td className="px-4 py-3 text-gray-700 capitalize">{session.type.toLowerCase()}</td>
                      <td className="px-4 py-3 text-gray-700">{session.load ? Math.round(session.load) : '—'}</td>
                      <td className="px-4 py-3 text-gray-700">{session.rpe ? session.rpe.toFixed(1) : '—'}</td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={`/sessions/${session.session_id}`}
                          className="text-sm font-medium text-blue-600 hover:text-blue-800"
                        >
                          Apri sessione →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Nessuna sessione recente registrata.</p>
          )}
        </section>
      )}
    </div>
  )
}

