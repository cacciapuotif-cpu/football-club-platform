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
  planned_intensity: number | null
  team_id: string
}

export default function SessionsPage() {
  const router = useRouter()
  const [sessions, setSessions] = useState<TrainingSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Skip authentication in development mode
    if (process.env.NEXT_PUBLIC_SKIP_AUTH === 'true') {
      fetchSessions()
      return
    }

    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    fetchSessions()
  }, [router])

  const fetchSessions = async () => {
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

      const response = await fetch('http://localhost:8000/api/v1/sessions/', {
        headers,
      })

      if (!response.ok) {
        throw new Error('Errore nel caricamento delle sessioni')
      }

      const data = await response.json()
      setSessions(data)
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

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Sessioni di Allenamento</h1>
        <Link
          href="/sessions/new"
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          + Nuova Sessione
        </Link>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-600 mb-4">Nessuna sessione registrata</p>
          <Link
            href="/sessions/new"
            className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Aggiungi la prima sessione
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sessions.map((session) => (
            <div key={session.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <span className="px-3 py-1 text-xs rounded-full bg-blue-100 text-blue-800 font-medium">
                  {getSessionTypeName(session.session_type)}
                </span>
                {session.planned_intensity && (
                  <span className="text-sm text-gray-600">
                    Intensità: {session.planned_intensity}/10
                  </span>
                )}
              </div>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                {session.focus || 'Sessione di allenamento'}
              </h3>

              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <div className="flex items-center">
                  <span className="font-medium">Data:</span>
                  <span className="ml-2">{formatDate(session.session_date)}</span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium">Durata:</span>
                  <span className="ml-2">{session.duration_min} minuti</span>
                </div>
              </div>

              <div className="flex gap-2">
                <Link
                  href={`/sessions/${session.id}`}
                  prefetch={false}
                  className="flex-1 text-center px-4 py-2 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors text-sm font-medium"
                >
                  Dettagli
                </Link>
                <Link
                  href={`/sessions/${session.id}/edit`}
                  prefetch={false}
                  className="flex-1 text-center px-4 py-2 bg-gray-50 text-gray-700 rounded hover:bg-gray-100 transition-colors text-sm font-medium"
                >
                  Modifica
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
