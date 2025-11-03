'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface WellnessData {
  id: string
  date: string
  player_id: string
  sleep_hours: number | null
  sleep_quality: number | null
  sleep_start_hhmm: string | null
  wake_time_hhmm: string | null
  hrv_ms: number | null
  resting_hr_bpm: number | null
  body_weight_kg: number | null
  doms_rating: number | null
  fatigue_rating: number | null
  stress_rating: number | null
  mood_rating: number | null
  motivation_rating: number | null
  hydration_rating: number | null
  hydration_pct: number | null
  srpe: number | null
  session_duration_min: number | null
  training_load: number | null
  notes: string | null
}

interface Player {
  id: string
  first_name: string
  last_name: string
}

export default function WellnessDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const [wellness, setWellness] = useState<WellnessData | null>(null)
  const [player, setPlayer] = useState<Player | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Skip authentication in development mode
    if (process.env.NEXT_PUBLIC_SKIP_AUTH === 'true') {
      fetchWellness()
      return
    }

    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    fetchWellness()
  }, [params.id, router])

  const fetchWellness = async () => {
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

      const response = await fetch(`http://localhost:8000/api/v1/wellness/${params.id}`, {
        headers,
      })

      if (!response.ok) {
        throw new Error('Errore nel caricamento dei dati wellness')
      }

      const data = await response.json()
      setWellness(data)

      // Fetch player info
      if (data.player_id) {
        const playerHeaders: HeadersInit = {
          'Content-Type': 'application/json',
        }

        // Add auth header only if not in skip mode
        if (process.env.NEXT_PUBLIC_SKIP_AUTH !== 'true' && token) {
          playerHeaders['Authorization'] = `Bearer ${token}`
        }

        const playerRes = await fetch(`http://localhost:8000/api/v1/players/${data.player_id}`, {
          headers: playerHeaders,
        })

        if (playerRes.ok) {
          const playerData = await playerRes.json()
          setPlayer(playerData)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(date)
  }

  const getRatingColor = (rating: number | null) => {
    if (!rating) return 'bg-gray-200'
    if (rating >= 4) return 'bg-green-500'
    if (rating >= 3) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getRatingLabel = (rating: number | null) => {
    if (!rating) return '-'
    if (rating === 1) return 'Molto Basso'
    if (rating === 2) return 'Basso'
    if (rating === 3) return 'Normale'
    if (rating === 4) return 'Alto'
    if (rating === 5) return 'Molto Alto'
    return rating.toString()
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

  if (error || !wellness) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error || 'Dati wellness non trovati'}
        </div>
        <Link href="/wellness" className="text-blue-600 hover:text-blue-800">
          ← Torna alla lista wellness
        </Link>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6">
        <Link href="/wellness" className="text-blue-600 hover:text-blue-800">
          ← Torna alla lista wellness
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-8">
        {/* Header */}
        <div className="flex justify-between items-start mb-8 pb-6 border-b">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              Monitoraggio Wellness
            </h1>
            <p className="text-lg text-gray-600">
              {formatDate(wellness.date)}
              {player && (
                <span className="ml-2">
                  • {player.first_name} {player.last_name}
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Sleep Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">
            😴 Sonno
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {wellness.sleep_hours !== null && (
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Ore di Sonno</p>
                <p className="text-3xl font-bold text-purple-800">{wellness.sleep_hours}h</p>
              </div>
            )}

            {wellness.sleep_quality !== null && (
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Qualità</p>
                <div className="flex items-center gap-2">
                  <p className="text-2xl font-bold text-purple-800">{wellness.sleep_quality}/5</p>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div
                        key={i}
                        className={`w-2 h-6 rounded ${
                          i <= wellness.sleep_quality! ? getRatingColor(wellness.sleep_quality) : 'bg-gray-200'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {wellness.sleep_start_hhmm && (
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Ora Inizio</p>
                <p className="text-2xl font-bold text-purple-800">{wellness.sleep_start_hhmm}</p>
              </div>
            )}

            {wellness.wake_time_hhmm && (
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Ora Risveglio</p>
                <p className="text-2xl font-bold text-purple-800">{wellness.wake_time_hhmm}</p>
              </div>
            )}
          </div>
        </div>

        {/* Recovery Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">
            💪 Recupero
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {wellness.hrv_ms !== null && (
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">HRV</p>
                <p className="text-3xl font-bold text-green-800">{wellness.hrv_ms?.toFixed(0) || '0'} ms</p>
              </div>
            )}

            {wellness.resting_hr_bpm !== null && (
              <div className="bg-red-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">FC Riposo</p>
                <p className="text-3xl font-bold text-red-800">{wellness.resting_hr_bpm} bpm</p>
              </div>
            )}

            {wellness.body_weight_kg !== null && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Peso</p>
                <p className="text-3xl font-bold text-blue-800">{wellness.body_weight_kg?.toFixed(1) || '0'} kg</p>
              </div>
            )}

            {wellness.doms_rating !== null && (
              <div className="bg-orange-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">DOMS</p>
                <p className="text-2xl font-bold text-orange-800">{wellness.doms_rating}/5</p>
                <p className="text-xs text-gray-600 mt-1">{getRatingLabel(wellness.doms_rating)}</p>
              </div>
            )}
          </div>
        </div>

        {/* Subjective Ratings */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">
            🧠 Stato Percepito
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {wellness.fatigue_rating !== null && (
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">Fatica</p>
                  <p className="text-lg font-bold text-gray-800">{wellness.fatigue_rating}/5</p>
                  <p className="text-sm text-gray-600">{getRatingLabel(wellness.fatigue_rating)}</p>
                </div>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className={`w-3 h-8 rounded ${
                        i <= wellness.fatigue_rating! ? getRatingColor(wellness.fatigue_rating) : 'bg-gray-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            )}

            {wellness.stress_rating !== null && (
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">Stress</p>
                  <p className="text-lg font-bold text-gray-800">{wellness.stress_rating}/5</p>
                  <p className="text-sm text-gray-600">{getRatingLabel(wellness.stress_rating)}</p>
                </div>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className={`w-3 h-8 rounded ${
                        i <= wellness.stress_rating! ? getRatingColor(wellness.stress_rating) : 'bg-gray-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            )}

            {wellness.mood_rating !== null && (
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">Umore</p>
                  <p className="text-lg font-bold text-gray-800">{wellness.mood_rating}/5</p>
                  <p className="text-sm text-gray-600">{getRatingLabel(wellness.mood_rating)}</p>
                </div>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className={`w-3 h-8 rounded ${
                        i <= wellness.mood_rating! ? getRatingColor(wellness.mood_rating) : 'bg-gray-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            )}

            {wellness.motivation_rating !== null && (
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">Motivazione</p>
                  <p className="text-lg font-bold text-gray-800">{wellness.motivation_rating}/5</p>
                  <p className="text-sm text-gray-600">{getRatingLabel(wellness.motivation_rating)}</p>
                </div>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className={`w-3 h-8 rounded ${
                        i <= wellness.motivation_rating! ? getRatingColor(wellness.motivation_rating) : 'bg-gray-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            )}

            {wellness.hydration_rating !== null && (
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">Idratazione</p>
                  <p className="text-lg font-bold text-gray-800">{wellness.hydration_rating}/5</p>
                  {wellness.hydration_pct && (
                    <p className="text-sm text-gray-600">{wellness.hydration_pct?.toFixed(0) || '0'}%</p>
                  )}
                </div>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className={`w-3 h-8 rounded ${
                        i <= wellness.hydration_rating! ? 'bg-blue-500' : 'bg-gray-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Training Load */}
        {(wellness.srpe !== null || wellness.session_duration_min !== null || wellness.training_load !== null) && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">
              🏃 Carico di Allenamento (sRPE)
            </h2>
            <div className="grid grid-cols-3 gap-4">
              {wellness.srpe !== null && (
                <div className="bg-indigo-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">RPE</p>
                  <p className="text-3xl font-bold text-indigo-800">{wellness.srpe}/10</p>
                </div>
              )}

              {wellness.session_duration_min !== null && (
                <div className="bg-indigo-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Durata</p>
                  <p className="text-3xl font-bold text-indigo-800">{wellness.session_duration_min} min</p>
                </div>
              )}

              {wellness.training_load !== null && (
                <div className="bg-indigo-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Carico Totale</p>
                  <p className="text-3xl font-bold text-indigo-800">{wellness.training_load?.toFixed(0) || '0'} AU</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Notes */}
        {wellness.notes && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">📝 Note</h2>
            <p className="text-gray-700 whitespace-pre-line bg-gray-50 p-4 rounded-lg">{wellness.notes}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4 pt-6 border-t">
          {player && (
            <Link
              href={`/players/${player.id}/dashboard`}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Dashboard Giocatore
            </Link>
          )}
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
