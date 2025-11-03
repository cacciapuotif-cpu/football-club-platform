'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function NewSessionPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
    session_date: '',
    session_time: '',
    session_type: 'TRAINING',
    duration_min: '90',
    team_id: '',
    focus: '',
    description: '',
    planned_intensity: '5',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Combine date and time into ISO string
      const dateTime = new Date(`${formData.session_date}T${formData.session_time}`)

      const apiData = {
        session_date: dateTime.toISOString(),
        session_type: formData.session_type,
        duration_min: parseInt(formData.duration_min),
        team_id: formData.team_id || '00000000-0000-0000-0000-000000000000', // Placeholder team_id
        focus: formData.focus || null,
        description: formData.description || null,
        planned_intensity: formData.planned_intensity ? parseInt(formData.planned_intensity) : null,
      }

      const token = localStorage.getItem('access_token')

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }

      // Add auth header only if not in skip mode
      if (process.env.NEXT_PUBLIC_SKIP_AUTH !== 'true' && token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('http://localhost:8000/api/v1/sessions', {
        method: 'POST',
        headers,
        body: JSON.stringify(apiData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore nella creazione della sessione')
      }

      router.push('/sessions')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  // Get current date and time for defaults
  const now = new Date()
  const defaultDate = now.toISOString().split('T')[0]
  const defaultTime = now.toTimeString().slice(0, 5)

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="mb-6">
        <Link href="/sessions" className="text-blue-600 hover:text-blue-800">
          ← Torna alla lista
        </Link>
      </div>

      <h1 className="text-3xl font-bold text-gray-800 mb-6">Nuova Sessione di Allenamento</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-6 space-y-6">
        {/* Data e Ora */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Data e Ora</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data *
              </label>
              <input
                type="date"
                name="session_date"
                value={formData.session_date || defaultDate}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ora *
              </label>
              <input
                type="time"
                name="session_time"
                value={formData.session_time || defaultTime}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Tipo e Durata */}
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Dettagli Sessione</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo di Sessione *
              </label>
              <select
                name="session_type"
                value={formData.session_type}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="TRAINING">Allenamento</option>
                <option value="FRIENDLY">Amichevole</option>
                <option value="RECOVERY">Recupero</option>
                <option value="GYM">Palestra</option>
                <option value="TACTICAL">Tattico</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Durata (minuti) *
              </label>
              <input
                type="number"
                name="duration_min"
                value={formData.duration_min}
                onChange={handleChange}
                required
                min="1"
                max="480"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Focus e Intensità */}
        <div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Focus (es: Tecnico, Tattico, Fisico)
              </label>
              <input
                type="text"
                name="focus"
                value={formData.focus}
                onChange={handleChange}
                placeholder="es: Lavoro tecnico sui passaggi"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Intensità Pianificata (1-10)
              </label>
              <input
                type="number"
                name="planned_intensity"
                value={formData.planned_intensity}
                onChange={handleChange}
                min="1"
                max="10"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descrizione
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={6}
              placeholder="Descrivi gli esercizi e le attività della sessione..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Submit Buttons */}
        <div className="flex justify-end gap-4 pt-4">
          <Link
            href="/sessions"
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Annulla
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Salvataggio...' : 'Salva Sessione'}
          </button>
        </div>
      </form>
    </div>
  )
}
