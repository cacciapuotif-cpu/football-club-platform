'use client'

import { useState, useEffect } from 'react'
import { upsertRpe, getRecentSessions } from '@/lib/api/training'
import type { TrainingSession } from '@/types/training'

interface RpeQuickAddProps {
  playerId: string
  onSuccess?: () => void
}

export default function RpeQuickAdd({ playerId, onSuccess }: RpeQuickAddProps) {
  const [sessions, setSessions] = useState<TrainingSession[]>([])
  const [selectedSession, setSelectedSession] = useState<string>('')
  const [rpe, setRpe] = useState<number>(5)
  const [loading, setLoading] = useState(false)
  const [loadingSessions, setLoadingSessions] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    fetchSessions()
  }, [])

  const fetchSessions = async () => {
    try {
      setLoadingSessions(true)
      const data = await getRecentSessions(7)
      setSessions(data)
      if (data.length > 0) {
        setSelectedSession(data[0].id)
      }
    } catch (err) {
      console.error('Error fetching sessions:', err)
    } finally {
      setLoadingSessions(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedSession) {
      setError('Seleziona una sessione')
      return
    }

    try {
      setLoading(true)
      setError(null)
      setSuccess(false)

      await upsertRpe({
        player_id: playerId,
        session_id: selectedSession,
        rpe: rpe,
      })

      setSuccess(true)

      // Reset form
      setTimeout(() => {
        setSuccess(false)
        if (onSuccess) {
          onSuccess()
        }
      }, 2000)
    } catch (err) {
      console.error('Error saving RPE:', err)
      setError(err instanceof Error ? err.message : 'Errore nel salvare l\'RPE')
    } finally {
      setLoading(false)
    }
  }

  if (loadingSessions) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-10 bg-gray-100 rounded"></div>
        </div>
      </div>
    )
  }

  if (sessions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Aggiungi RPE</h3>
        <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
          <p className="text-yellow-800 text-sm">
            Nessuna sessione di allenamento disponibile negli ultimi 7 giorni.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Aggiungi RPE</h3>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded p-3">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-4 bg-green-50 border border-green-200 rounded p-3">
          <p className="text-green-800 text-sm">✓ RPE salvato con successo!</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="session" className="block text-sm font-medium text-gray-700 mb-2">
            Sessione
          </label>
          <select
            id="session"
            value={selectedSession}
            onChange={(e) => setSelectedSession(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          >
            {sessions.map((session) => (
              <option key={session.id} value={session.id}>
                {formatSessionLabel(session)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="rpe" className="block text-sm font-medium text-gray-700 mb-2">
            RPE (Rate of Perceived Exertion): {rpe}
          </label>
          <div className="flex items-center space-x-4">
            <span className="text-xs text-gray-500">0</span>
            <input
              type="range"
              id="rpe"
              min="0"
              max="10"
              step="0.5"
              value={rpe}
              onChange={(e) => setRpe(Number(e.target.value))}
              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              disabled={loading}
            />
            <span className="text-xs text-gray-500">10</span>
          </div>
          <div className="mt-2 flex justify-between text-xs text-gray-500">
            <span>Molto leggero</span>
            <span>Moderato</span>
            <span>Massimo</span>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !selectedSession}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {loading ? 'Salvataggio...' : 'Salva RPE'}
        </button>
      </form>
    </div>
  )
}

function formatSessionLabel(session: TrainingSession): string {
  const date = new Date(session.session_date)
  const dateStr = new Intl.DateTimeFormat('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)

  const focus = session.focus || session.session_type
  const duration = session.duration_min ? ` (${session.duration_min} min)` : ''

  return `${dateStr} - ${focus}${duration}`
}
