'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface TrainingSession {
  id: string
  session_date: string
  session_type: string
  duration_min: number
  focus: string | null
  description: string | null
  planned_intensity: number | null
  actual_intensity_avg: number | null
  team_id: string
  distance_m: number | null
  hi_distance_m: number | null
  sprints_count: number | null
  top_speed_ms: number | null
  max_acc_ms2: number | null
  hr_avg_bpm: number | null
  hr_max_bpm: number | null
  fatigue_note: string | null
}

export default function SessionDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const [session, setSession] = useState<TrainingSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Skip authentication in development mode
    if (process.env.NEXT_PUBLIC_SKIP_AUTH === 'true') {
      fetchSession()
      return
    }

    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    fetchSession()
  }, [params.id, router])

  const fetchSession = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }

      // Add auth header only if not in skip mode
      if (process.env.NEXT_PUBLIC_SKIP_AUTH !== 'true' && token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`http://localhost:8000/api/v1/sessions/${params.id}`, {
        headers,
      })

      if (!response.ok) {
        throw new Error('Errore nel caricamento della sessione')
      }

      const data = await response.json()
      setSession(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  const getSessionTypeName = (type: string) => {
    const types: Record<string, string> = {
      TRAINING: 'Allenamento',
      FRIENDLY: 'Amichevole',
      RECOVERY: 'Recupero',
      GYM: 'Palestra',
      TACTICAL: 'Tattico',
    }
    return types[type] || type
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="text-xl text-gray-600">Caricamento...</div>
        </div>
      </div>
    )
  }

  if (error || !session) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error || 'Sessione non trovata'}
        </div>
        <Link href="/sessions" className="text-blue-600 hover:text-blue-800">
          ← Torna alla lista sessioni
        </Link>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6">
        <Link href="/sessions" className="text-blue-600 hover:text-blue-800">
          ← Torna alla lista sessioni
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              {session.focus || 'Sessione di Allenamento'}
            </h1>
            <span className="inline-block px-3 py-1 text-sm rounded-full bg-blue-100 text-blue-800 font-medium">
              {getSessionTypeName(session.session_type)}
            </span>
          </div>
          <Link
            href={`/sessions/${session.id}/edit`}
            prefetch={false}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Modifica
          </Link>
        </div>

        {/* Basic Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="border-l-4 border-blue-500 pl-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase mb-1">Data e Ora</h2>
            <p className="text-lg text-gray-800">{formatDate(session.session_date)}</p>
          </div>

          <div className="border-l-4 border-blue-500 pl-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase mb-1">Durata</h2>
            <p className="text-lg text-gray-800">{session.duration_min} minuti</p>
          </div>

          {session.planned_intensity && (
            <div className="border-l-4 border-blue-500 pl-4">
              <h2 className="text-sm font-semibold text-gray-500 uppercase mb-1">Intensità Pianificata</h2>
              <p className="text-lg text-gray-800">{session.planned_intensity}/10</p>
            </div>
          )}

          {session.actual_intensity_avg && (
            <div className="border-l-4 border-green-500 pl-4">
              <h2 className="text-sm font-semibold text-gray-500 uppercase mb-1">Intensità Effettiva</h2>
              <p className="text-lg text-gray-800">{session.actual_intensity_avg.toFixed(1)}/10</p>
            </div>
          )}
        </div>

        {/* Description */}
        {session.description && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3 border-b pb-2">Descrizione</h2>
            <p className="text-gray-700 whitespace-pre-line">{session.description}</p>
          </div>
        )}

        {/* GPS/Physical Data */}
        {(session.distance_m || session.hi_distance_m || session.sprints_count || session.top_speed_ms) && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Dati Fisici (GPS)</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {session.distance_m && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Distanza Totale</p>
                  <p className="text-2xl font-bold text-gray-800">{(session.distance_m / 1000).toFixed(2)} km</p>
                </div>
              )}

              {session.hi_distance_m && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Alta Intensità</p>
                  <p className="text-2xl font-bold text-gray-800">{session.hi_distance_m.toFixed(0)} m</p>
                </div>
              )}

              {session.sprints_count !== null && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Sprint</p>
                  <p className="text-2xl font-bold text-gray-800">{session.sprints_count}</p>
                </div>
              )}

              {session.top_speed_ms && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Velocità Max</p>
                  <p className="text-2xl font-bold text-gray-800">{(session.top_speed_ms * 3.6).toFixed(1)} km/h</p>
                </div>
              )}

              {session.max_acc_ms2 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Acc. Max</p>
                  <p className="text-2xl font-bold text-gray-800">{session.max_acc_ms2.toFixed(2)} m/s²</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Heart Rate Data */}
        {(session.hr_avg_bpm || session.hr_max_bpm) && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Frequenza Cardiaca</h2>
            <div className="grid grid-cols-2 gap-4">
              {session.hr_avg_bpm && (
                <div className="bg-red-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">FC Media</p>
                  <p className="text-2xl font-bold text-red-600">{session.hr_avg_bpm} bpm</p>
                </div>
              )}

              {session.hr_max_bpm && (
                <div className="bg-red-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">FC Massima</p>
                  <p className="text-2xl font-bold text-red-600">{session.hr_max_bpm} bpm</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Fatigue Note */}
        {session.fatigue_note && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3 border-b pb-2">Note Fatica</h2>
            <p className="text-gray-700">{session.fatigue_note}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4 pt-6 border-t">
          <Link
            href={`/sessions/${session.id}/edit`}
            prefetch={false}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Modifica Sessione
          </Link>
          <button
            onClick={() => window.print()}
            className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Stampa
          </button>
        </div>
      </div>
    </div>
  )
}
