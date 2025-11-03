'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface Player {
  id: string
  first_name: string
  last_name: string
}

export default function NewWellnessPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [players, setPlayers] = useState<Player[]>([])

  // Check authentication first
  useEffect(() => {
    // Skip authentication in development mode
    if (process.env.NEXT_PUBLIC_SKIP_AUTH === 'true') {
      return
    }

    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
    }
  }, [router])

  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    player_id: '',
    sleep_hours: '',
    sleep_quality: '3',
    hrv_ms: '',
    resting_hr_bpm: '',
    doms_rating: '3',
    fatigue_rating: '3',
    stress_rating: '3',
    mood_rating: '3',
    motivation_rating: '3',
    hydration_rating: '3',
    srpe: '',
    session_duration_min: '',
    notes: '',
  })

  // Fetch players after auth check
  useEffect(() => {
    // In skip mode, always fetch players
    if (process.env.NEXT_PUBLIC_SKIP_AUTH === 'true') {
      fetchPlayers()
      return
    }

    const token = localStorage.getItem('access_token')
    if (token) {
      fetchPlayers()
    }
  }, [])

  const fetchPlayers = async () => {
    try {
      const token = localStorage.getItem('access_token')

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }

      // Add auth header only if not in skip mode
      if (process.env.NEXT_PUBLIC_SKIP_AUTH !== 'true' && token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('http://localhost:8000/api/v1/players', {
        headers,
      })

      if (response.ok) {
        const data = await response.json()
        setPlayers(data)
      }
    } catch (err) {
      console.error('Error fetching players:', err)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Calculate training load if sRPE and duration are provided
      let trainingLoad = null
      if (formData.srpe && formData.session_duration_min) {
        trainingLoad = parseInt(formData.srpe) * parseInt(formData.session_duration_min)
      }

      const apiData = {
        date: formData.date,
        player_id: formData.player_id,
        sleep_hours: formData.sleep_hours ? parseFloat(formData.sleep_hours) : null,
        sleep_quality: formData.sleep_quality ? parseInt(formData.sleep_quality) : null,
        hrv_ms: formData.hrv_ms ? parseFloat(formData.hrv_ms) : null,
        resting_hr_bpm: formData.resting_hr_bpm ? parseInt(formData.resting_hr_bpm) : null,
        doms_rating: formData.doms_rating ? parseInt(formData.doms_rating) : null,
        fatigue_rating: formData.fatigue_rating ? parseInt(formData.fatigue_rating) : null,
        stress_rating: formData.stress_rating ? parseInt(formData.stress_rating) : null,
        mood_rating: formData.mood_rating ? parseInt(formData.mood_rating) : null,
        motivation_rating: formData.motivation_rating ? parseInt(formData.motivation_rating) : null,
        hydration_rating: formData.hydration_rating ? parseInt(formData.hydration_rating) : null,
        srpe: formData.srpe ? parseInt(formData.srpe) : null,
        session_duration_min: formData.session_duration_min ? parseInt(formData.session_duration_min) : null,
        training_load: trainingLoad,
        notes: formData.notes || null,
      }

      const token = localStorage.getItem('access_token')

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }

      // Add auth header only if not in skip mode
      if (process.env.NEXT_PUBLIC_SKIP_AUTH !== 'true' && token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('http://localhost:8000/api/v1/wellness', {
        method: 'POST',
        headers,
        body: JSON.stringify(apiData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore nella creazione dei dati wellness')
      }

      router.push('/wellness')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6">
        <Link href="/wellness" className="text-blue-600 hover:text-blue-800">
          ← Torna alla lista
        </Link>
      </div>

      <h1 className="text-3xl font-bold text-gray-800 mb-6">Nuovo Monitoraggio Wellness</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-6 space-y-6">
        {/* Informazioni Base */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Informazioni Base</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data *
              </label>
              <input
                type="date"
                name="date"
                value={formData.date}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Giocatore *
              </label>
              <select
                name="player_id"
                value={formData.player_id}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Seleziona un giocatore</option>
                {players.map((player) => (
                  <option key={player.id} value={player.id}>
                    {player.first_name} {player.last_name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Sonno */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Sonno</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ore di sonno
              </label>
              <input
                type="number"
                name="sleep_hours"
                value={formData.sleep_hours}
                onChange={handleChange}
                min="0"
                max="24"
                step="0.5"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Qualità del sonno (1-5)
              </label>
              <select
                name="sleep_quality"
                value={formData.sleep_quality}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1">1 - Pessimo</option>
                <option value="2">2 - Scarso</option>
                <option value="3">3 - Normale</option>
                <option value="4">4 - Buono</option>
                <option value="5">5 - Ottimo</option>
              </select>
            </div>
          </div>
        </div>

        {/* Recupero */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Recupero</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                HRV (ms)
              </label>
              <input
                type="number"
                name="hrv_ms"
                value={formData.hrv_ms}
                onChange={handleChange}
                min="0"
                step="0.1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                FC a riposo (bpm)
              </label>
              <input
                type="number"
                name="resting_hr_bpm"
                value={formData.resting_hr_bpm}
                onChange={handleChange}
                min="30"
                max="220"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                DOMS (1-5)
              </label>
              <select
                name="doms_rating"
                value={formData.doms_rating}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1">1 - Nessuno</option>
                <option value="2">2 - Leggero</option>
                <option value="3">3 - Moderato</option>
                <option value="4">4 - Forte</option>
                <option value="5">5 - Molto forte</option>
              </select>
            </div>
          </div>
        </div>

        {/* Stato Percepito */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Stato Percepito</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Fatica (1-5)
              </label>
              <select
                name="fatigue_rating"
                value={formData.fatigue_rating}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1">1 - Molto bassa</option>
                <option value="2">2 - Bassa</option>
                <option value="3">3 - Normale</option>
                <option value="4">4 - Alta</option>
                <option value="5">5 - Molto alta</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stress (1-5)
              </label>
              <select
                name="stress_rating"
                value={formData.stress_rating}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1">1 - Molto basso</option>
                <option value="2">2 - Basso</option>
                <option value="3">3 - Normale</option>
                <option value="4">4 - Alto</option>
                <option value="5">5 - Molto alto</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Umore (1-5)
              </label>
              <select
                name="mood_rating"
                value={formData.mood_rating}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1">1 - Pessimo</option>
                <option value="2">2 - Scarso</option>
                <option value="3">3 - Normale</option>
                <option value="4">4 - Buono</option>
                <option value="5">5 - Ottimo</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Motivazione (1-5)
              </label>
              <select
                name="motivation_rating"
                value={formData.motivation_rating}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1">1 - Molto bassa</option>
                <option value="2">2 - Bassa</option>
                <option value="3">3 - Normale</option>
                <option value="4">4 - Alta</option>
                <option value="5">5 - Molto alta</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Idratazione (1-5)
              </label>
              <select
                name="hydration_rating"
                value={formData.hydration_rating}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1">1 - Pessima</option>
                <option value="2">2 - Scarsa</option>
                <option value="3">3 - Normale</option>
                <option value="4">4 - Buona</option>
                <option value="5">5 - Ottima</option>
              </select>
            </div>
          </div>
        </div>

        {/* Session RPE */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Carico di Allenamento (sRPE)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                RPE (1-10)
              </label>
              <input
                type="number"
                name="srpe"
                value={formData.srpe}
                onChange={handleChange}
                min="1"
                max="10"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Durata sessione (minuti)
              </label>
              <input
                type="number"
                name="session_duration_min"
                value={formData.session_duration_min}
                onChange={handleChange}
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          {formData.srpe && formData.session_duration_min && (
            <div className="mt-2 p-3 bg-blue-50 rounded-md">
              <p className="text-sm text-gray-700">
                Carico di allenamento calcolato:{' '}
                <span className="font-bold">
                  {parseInt(formData.srpe) * parseInt(formData.session_duration_min)} AU
                </span>
              </p>
            </div>
          )}
        </div>

        {/* Note */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Note
          </label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows={4}
            placeholder="Note aggiuntive, sintomi particolari, ecc..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Submit Buttons */}
        <div className="flex justify-end gap-4 pt-4">
          <Link
            href="/wellness"
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Annulla
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Salvataggio...' : 'Salva Dati'}
          </button>
        </div>
      </form>
    </div>
  )
}
