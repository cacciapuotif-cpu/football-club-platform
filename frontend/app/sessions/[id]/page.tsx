'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { it } from 'date-fns/locale'
import {
  fetchSessionDetail,
  fetchSessionSnapshot,
} from '@/lib/api/sessions'
import {
  acknowledgeAlert,
  fetchAthleteContext,
} from '@/lib/api/wellness'
import type {
  SessionDetail,
  SessionWellnessSnapshot,
  SnapshotAlert,
  SnapshotPrediction,
} from '@/types/sessions'
import type { AthleteContextResponse } from '@/types/wellness'

type Props = {
  params: { id: string }
}

type ParticipantInfo = {
  athleteId: string
  fullName?: string | null
  role?: string | null
  playerId?: string | null
}

const severityBadgeClass: Record<string, string> = {
  low: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

const formatDateTime = (value: string) =>
  format(new Date(value), "EEEE d MMMM yyyy 'alle' HH:mm", { locale: it })

const formatDate = (value: string) =>
  format(new Date(value), "d MMM yyyy • HH:mm", { locale: it })

const uniqueAthletes = (snapshot?: SessionWellnessSnapshot) =>
  snapshot ? Array.from(new Set(snapshot.athletes)) : []

export default function SessionDetailPage({ params }: Props) {
  const [detail, setDetail] = useState<SessionDetail | null>(null)
  const [snapshot, setSnapshot] = useState<SessionWellnessSnapshot | null>(null)
  const [participantProfiles, setParticipantProfiles] = useState<Record<string, ParticipantInfo>>({})
  const [loading, setLoading] = useState(true)
  const [loadingSnapshot, setLoadingSnapshot] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [ackPending, setAckPending] = useState<string | null>(null)

  const loadSession = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [detailResponse, snapshotResponse] = await Promise.all([
        fetchSessionDetail(params.id),
        fetchSessionSnapshot(params.id, 2),
      ])
      setDetail(detailResponse)
      setSnapshot(snapshotResponse)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Impossibile caricare la sessione'
      setError(message)
    } finally {
      setLoading(false)
      setLoadingSnapshot(false)
    }
  }, [params.id])

  useEffect(() => {
    loadSession()
  }, [loadSession])

  useEffect(() => {
    const loadProfiles = async () => {
      if (!snapshot) {
        setParticipantProfiles({})
        return
      }

      const athleteIds = uniqueAthletes(snapshot)
      if (!athleteIds.length) {
        setParticipantProfiles({})
        return
      }

      const entries = await Promise.all(
        athleteIds.map(async (athleteId) => {
          try {
            const context = await fetchAthleteContext(athleteId, 14)
            return [athleteId, context] as const
          } catch (err) {
            console.warn(`[Session Detail] Impossibile caricare il contesto per ${athleteId}`, err)
            return [athleteId, null] as const
          }
        })
      )

      const map = entries.reduce<Record<string, ParticipantInfo>>((acc, [athleteId, context]) => {
        if (context) {
          acc[athleteId] = {
            athleteId,
            fullName: context.player.full_name,
            role: context.player.role,
            playerId: context.player.player_id,
          }
        } else {
          acc[athleteId] = { athleteId }
        }
        return acc
      }, {})

      setParticipantProfiles(map)
    }

    loadProfiles()
  }, [snapshot])

  const handleAcknowledge = async (alertId: string) => {
    try {
      setAckPending(alertId)
      await acknowledgeAlert(alertId)
      await loadSession()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Errore nella presa in carico dell’allerta'
      setError(message)
    } finally {
      setAckPending(null)
    }
  }

  const participationWithProfile = useMemo(() => {
    if (!detail) return []
    return detail.participation.map((item) => ({
      ...item,
      profile: participantProfiles[item.athlete_id],
    }))
  }, [detail, participantProfiles])

  const predictionsMap = useMemo(() => {
    if (!snapshot) return {}
    return snapshot.predictions.reduce<Record<string, SnapshotPrediction>>((acc, prediction) => {
      acc[prediction.athlete_id] = prediction
      return acc
    }, {})
  }, [snapshot])

  const alertsByAthlete = useMemo(() => {
    if (!snapshot) return {}
    return snapshot.alerts.reduce<Record<string, SnapshotAlert[]>>((acc, alert) => {
      acc[alert.athlete_id] = acc[alert.athlete_id] ? [...acc[alert.athlete_id], alert] : [alert]
      return acc
    }, {})
  }, [snapshot])

  if (loading && !detail) {
    return (
      <div className="container mx-auto px-4 py-10">
        <div className="mx-auto max-w-4xl space-y-4">
          <div className="h-6 w-40 animate-pulse rounded bg-gray-200" />
          <div className="h-11 animate-pulse rounded-lg bg-gray-100" />
          <div className="h-32 animate-pulse rounded-lg bg-gray-100" />
          <div className="h-64 animate-pulse rounded-lg bg-gray-100" />
        </div>
      </div>
    )
  }

  if (error && !detail) {
    return (
      <div className="container mx-auto px-4 py-10">
        <div className="mx-auto max-w-3xl rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          <p className="font-semibold">Errore nel caricamento</p>
          <p className="mt-2">{error}</p>
          <div className="mt-4">
            <Link href="/sessions" className="text-blue-600 hover:underline">
              ← Torna alla lista sessioni
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (!detail) return null

  const session = detail.session

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 lg:flex-row">
        <div className="flex-1 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Link href="/sessions" className="text-sm font-medium text-blue-600 hover:text-blue-800">
                ← Torna alla lista
              </Link>
              <h1 className="mt-2 text-2xl font-semibold text-gray-900">
                {session.notes ? session.notes : `Sessione ${session.type}`}
              </h1>
              <p className="mt-1 text-sm text-gray-500">{formatDateTime(session.start_ts)}</p>
            </div>
            <div className="flex gap-3">
              {session.load && (
                <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-semibold text-violet-700">
                  Load {Math.round(session.load)}
                </span>
              )}
              {session.rpe_avg && (
                <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                  RPE {session.rpe_avg.toFixed(1)}
                </span>
              )}
            </div>
          </div>

          <section className="rounded-lg border border-gray-200 bg-white shadow-sm">
            <header className="border-b border-gray-200 px-4 py-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-600">Partecipanti</h2>
            </header>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-100 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">
                      Atleta
                    </th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">
                      Carico
                    </th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">
                      RPE
                    </th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-500">
                      Stato
                    </th>
                    <th scope="col" className="px-4 py-3 text-right font-medium text-gray-500">
                      Azioni
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {participationWithProfile.map((participant) => {
                    const profile = participant.profile
                    return (
                      <tr key={participant.athlete_id}>
                        <td className="px-4 py-3">
                          <div>
                            <p className="font-medium text-gray-900">
                              {profile?.fullName ?? `Athlete ${participant.athlete_id.slice(0, 8)}`}
                            </p>
                            {profile?.role && <p className="text-xs text-gray-500">{profile.role}</p>}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {participant.load ? Math.round(participant.load) : '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {participant.rpe ? participant.rpe.toFixed(1) : '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-700 capitalize">{participant.status.toLowerCase()}</td>
                        <td className="px-4 py-3 text-right">
                          <Link
                            href={`/athletes/${participant.athlete_id}`}
                            className="text-sm font-medium text-blue-600 hover:text-blue-800"
                          >
                            Apri Athlete 360 →
                          </Link>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        <aside className="w-full space-y-6 lg:w-96">
          <section className="rounded-lg border border-blue-100 bg-blue-50/50 p-5">
            <header className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wide text-blue-700">
                  Wellness Snapshot
                </h2>
                <p className="text-xs text-blue-600">
                  Finestra ±{snapshot?.window_days ?? 2} giorni •{' '}
                  {snapshot ? formatDate(snapshot.window_start) : '—'} →{' '}
                  {snapshot ? formatDate(snapshot.window_end) : '—'}
                </p>
              </div>
            </header>
            {loadingSnapshot ? (
              <p className="text-sm text-blue-700">Caricamento dati wellness…</p>
            ) : snapshot && snapshot.athletes.length ? (
              <div className="space-y-4">
                {snapshot.athletes.map((athleteId) => {
                  const profile = participantProfiles[athleteId]
                  const prediction = predictionsMap[athleteId]
                  const alerts = alertsByAthlete[athleteId] ?? []
                  const openAlerts = alerts.filter((alert) => alert.status === 'open')

                  return (
                    <div key={athleteId} className="rounded-md bg-white/70 p-4 shadow-sm">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-gray-900">
                            {profile?.fullName ?? `Athlete ${athleteId.slice(0, 8)}`}
                          </p>
                          {profile?.role && (
                            <p className="text-xs text-gray-500 uppercase">{profile.role}</p>
                          )}
                        </div>
                        {prediction && (
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${
                              severityBadgeClass[prediction.severity] ?? 'bg-gray-100 text-gray-700'
                            }`}
                          >
                            {Math.round(prediction.score)} • {prediction.severity}
                          </span>
                        )}
                      </div>

                      {prediction?.drivers && (
                        <div className="mt-3 text-xs text-gray-600">
                          <p className="font-semibold text-gray-700">Driver principali</p>
                          <ul className="mt-1 space-y-1">
                            {Object.entries(prediction.drivers)
                              .slice(0, 3)
                              .map(([driver, value]) => (
                                <li key={driver} className="flex justify-between">
                                  <span className="text-gray-500">{driver}</span>
                                  <span className="font-medium text-gray-700">{String(value)}</span>
                                </li>
                              ))}
                          </ul>
                        </div>
                      )}

                      {alerts.length > 0 && (
                        <div className="mt-3 space-y-2">
                          {alerts.map((alert) => (
                            <div
                              key={alert.id}
                              className="flex items-center justify-between rounded-md border border-red-100 bg-red-50 px-3 py-2 text-xs"
                            >
                              <div>
                                <p className="font-semibold text-red-700">{alert.policy_id ?? 'Alert'}</p>
                                <p className="text-[11px] text-red-600">
                                  Aperto il {formatDate(alert.opened_at)}
                                </p>
                              </div>
                              {alert.status === 'open' ? (
                                <button
                                  type="button"
                                  onClick={() => handleAcknowledge(alert.id)}
                                  disabled={ackPending === alert.id}
                                  className="rounded bg-red-600 px-2 py-1 text-[11px] font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-red-300"
                                >
                                  {ackPending === alert.id ? '...' : 'Prendi in carico'}
                                </button>
                              ) : (
                                <span className="text-[11px] font-medium uppercase text-red-500">
                                  {alert.status}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="mt-3 border-t border-gray-100 pt-3">
                        <Link
                          href={`/athletes/${athleteId}`}
                          className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700"
                        >
                          Vai a Athlete 360 →
                        </Link>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="text-sm text-blue-700">
                Nessun dato wellness disponibile per questa sessione nel periodo selezionato.
              </p>
            )}
          </section>
        </aside>
      </div>
    </div>
  )
}
