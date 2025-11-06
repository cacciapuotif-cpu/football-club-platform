'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

interface PlayerProfile {
  id: string
  first_name: string
  last_name: string
  date_of_birth: string
  place_of_birth: string | null
  nationality: string
  tax_code: string | null
  email: string | null
  phone: string | null
  address: string | null
  role_primary: string
  role_secondary: string | null
  dominant_foot: string
  dominant_arm: string
  jersey_number: number | null
  height_cm: number | null
  foto_url: string | null
  notes: string | null
  consent_given: boolean
  consent_date: string | null
  last_weight_kg: number | null
  last_weight_date: string | null
}

export default function PlayerProfilePage() {
  const params = useParams()
  const router = useRouter()
  const playerId = params.id as string

  const [profile, setProfile] = useState<PlayerProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [weightDate, setWeightDate] = useState('')
  const [weightKg, setWeightKg] = useState('')

  useEffect(() => {
    fetchProfile()
  }, [playerId])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`http://localhost:8000/api/v1/players/${playerId}/profile`, { headers })
      if (!response.ok) throw new Error('Errore nel caricamento del profilo')
      const data = await response.json()
      setProfile(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!profile) return
    try {
      setSaving(true)
      const token = localStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`http://localhost:8000/api/v1/players/${playerId}/profile`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(profile),
      })
      if (!response.ok) throw new Error('Errore nel salvataggio')
      const updated = await response.json()
      setProfile(updated)
      setEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore nel salvataggio')
    } finally {
      setSaving(false)
    }
  }

  const handleAddWeight = async () => {
    if (!weightDate || !weightKg) {
      alert('Inserisci data e peso')
      return
    }
    try {
      const token = localStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`http://localhost:8000/api/v1/players/${playerId}/weight`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          date: weightDate,
          weight_kg: parseFloat(weightKg),
        }),
      })
      if (!response.ok) throw new Error('Errore nell\'aggiunta del peso')
      setWeightDate('')
      setWeightKg('')
      fetchProfile() // Refresh to get updated last_weight
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore nell\'aggiunta del peso')
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error || 'Impossibile caricare il profilo'}
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6">
        <Link href="/players" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
          ← Torna ai giocatori
        </Link>
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-800">
            Profilo: {profile.first_name} {profile.last_name}
          </h1>
          <div className="flex gap-2">
            {!editing ? (
              <>
                <button
                  onClick={() => setEditing(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Modifica
                </button>
                <Link
                  href={`/data/player/${playerId}`}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Vai ai Dati
                </Link>
              </>
            ) : (
              <>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {saving ? 'Salvataggio...' : 'Salva'}
                </button>
                <button
                  onClick={() => {
                    setEditing(false)
                    fetchProfile()
                  }}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Annulla
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Dati Anagrafici</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
            {editing ? (
              <input
                type="text"
                value={profile.first_name}
                onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            ) : (
              <p className="text-gray-900">{profile.first_name}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cognome</label>
            {editing ? (
              <input
                type="text"
                value={profile.last_name}
                onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            ) : (
              <p className="text-gray-900">{profile.last_name}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data di Nascita</label>
            {editing ? (
              <input
                type="date"
                value={profile.date_of_birth}
                onChange={(e) => setProfile({ ...profile, date_of_birth: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            ) : (
              <p className="text-gray-900">{new Date(profile.date_of_birth).toLocaleDateString('it-IT')}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Luogo di Nascita</label>
            {editing ? (
              <input
                type="text"
                value={profile.place_of_birth || ''}
                onChange={(e) => setProfile({ ...profile, place_of_birth: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            ) : (
              <p className="text-gray-900">{profile.place_of_birth || '-'}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nazionalità</label>
            {editing ? (
              <input
                type="text"
                value={profile.nationality}
                onChange={(e) => setProfile({ ...profile, nationality: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                maxLength={2}
              />
            ) : (
              <p className="text-gray-900">{profile.nationality}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Codice Fiscale</label>
            {editing ? (
              <input
                type="text"
                value={profile.tax_code || ''}
                onChange={(e) => setProfile({ ...profile, tax_code: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            ) : (
              <p className="text-gray-900">{profile.tax_code || '-'}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            {editing ? (
              <input
                type="email"
                value={profile.email || ''}
                onChange={(e) => setProfile({ ...profile, email: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            ) : (
              <p className="text-gray-900">{profile.email || '-'}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Telefono</label>
            {editing ? (
              <input
                type="tel"
                value={profile.phone || ''}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            ) : (
              <p className="text-gray-900">{profile.phone || '-'}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ruolo Principale</label>
            {editing ? (
              <select
                value={profile.role_primary}
                onChange={(e) => setProfile({ ...profile, role_primary: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="GK">Portiere</option>
                <option value="DF">Difensore</option>
                <option value="MF">Centrocampista</option>
                <option value="FW">Attaccante</option>
              </select>
            ) : (
              <p className="text-gray-900">{profile.role_primary}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Piede Dominante</label>
            {editing ? (
              <select
                value={profile.dominant_foot}
                onChange={(e) => setProfile({ ...profile, dominant_foot: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="LEFT">Sinistro</option>
                <option value="RIGHT">Destro</option>
                <option value="BOTH">Ambidestro</option>
              </select>
            ) : (
              <p className="text-gray-900">{profile.dominant_foot}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Numero Maglia</label>
            {editing ? (
              <input
                type="number"
                value={profile.jersey_number || ''}
                onChange={(e) => setProfile({ ...profile, jersey_number: e.target.value ? parseInt(e.target.value) : null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            ) : (
              <p className="text-gray-900">{profile.jersey_number || '-'}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Altezza (cm)</label>
            {editing ? (
              <input
                type="number"
                value={profile.height_cm || ''}
                onChange={(e) => setProfile({ ...profile, height_cm: e.target.value ? parseFloat(e.target.value) : null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            ) : (
              <p className="text-gray-900">{profile.height_cm ? `${profile.height_cm} cm` : '-'}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Foto URL</label>
            {editing ? (
              <input
                type="url"
                value={profile.foto_url || ''}
                onChange={(e) => setProfile({ ...profile, foto_url: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="https://..."
              />
            ) : (
              <div>
                {profile.foto_url ? (
                  <img src={profile.foto_url} alt="Foto" className="w-24 h-24 object-cover rounded" />
                ) : (
                  <p className="text-gray-500">Nessuna foto</p>
                )}
              </div>
            )}
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Note</label>
            {editing ? (
              <textarea
                value={profile.notes || ''}
                onChange={(e) => setProfile({ ...profile, notes: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                rows={3}
              />
            ) : (
              <p className="text-gray-900">{profile.notes || '-'}</p>
            )}
          </div>
        </div>
      </div>

      {/* Weight Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Peso</h2>
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            Ultimo peso registrato: {profile.last_weight_kg ? `${profile.last_weight_kg} kg` : 'Nessun dato'} 
            {profile.last_weight_date && ` (${new Date(profile.last_weight_date).toLocaleDateString('it-IT')})`}
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data</label>
            <input
              type="date"
              value={weightDate}
              onChange={(e) => setWeightDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Peso (kg)</label>
            <input
              type="number"
              step="0.1"
              value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              placeholder="70.5"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleAddWeight}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Aggiungi Peso
            </button>
          </div>
        </div>
      </div>

      {/* GDPR Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Consenso GDPR</h2>
        <div className="space-y-2">
          <p className="text-sm text-gray-600">
            Consenso dato: {profile.consent_given ? 'Sì' : 'No'}
          </p>
          {profile.consent_date && (
            <p className="text-sm text-gray-600">
              Data consenso: {new Date(profile.consent_date).toLocaleDateString('it-IT')}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

