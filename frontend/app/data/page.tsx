'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

interface Player {
  id: string
  first_name: string
  last_name: string
  role_primary: string
  jersey_number: number | null
  is_active: boolean
}

export default function DataPage() {
  const [players, setPlayers] = useState<Player[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('')

  useEffect(() => {
    fetchPlayers()
  }, [])

  const fetchPlayers = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }

      if (process.env.NEXT_PUBLIC_SKIP_AUTH !== 'true' && token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('http://localhost:8000/api/v1/players/', {
        headers,
      })

      if (!response.ok) {
        throw new Error('Errore nel caricamento dei giocatori')
      }

      const data = await response.json()
      setPlayers(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  const getRoleName = (role: string) => {
    const roles: Record<string, string> = {
      GK: 'Portiere',
      DF: 'Difensore',
      MF: 'Centrocampista',
      FW: 'Attaccante',
    }
    return roles[role] || role
  }

  // Filter players
  const filteredPlayers = players.filter((player) => {
    const matchesSearch = searchQuery === '' ||
      `${player.first_name} ${player.last_name}`.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesRole = roleFilter === '' || player.role_primary === roleFilter
    return matchesSearch && matchesRole && player.is_active
  })

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">Dati Giocatori</h1>
        <p className="text-gray-600">
          Seleziona un giocatore per visualizzare i suoi dati wellness e performance
        </p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cerca giocatore
            </label>
            <input
              type="text"
              placeholder="Nome o cognome..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filtra per ruolo
            </label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tutti i ruoli</option>
              <option value="GK">Portiere (GK)</option>
              <option value="DF">Difensore (DF)</option>
              <option value="MF">Centrocampista (MF)</option>
              <option value="FW">Attaccante (FW)</option>
            </select>
          </div>
        </div>

        {(searchQuery || roleFilter) && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={() => {
                setSearchQuery('')
                setRoleFilter('')
              }}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 underline"
            >
              Azzera filtri
            </button>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-center space-x-2">
          <svg
            className="h-5 w-5 text-blue-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="text-sm text-blue-800">
            <strong>{filteredPlayers.length}</strong> giocator{filteredPlayers.length === 1 ? 'e' : 'i'}
            {(searchQuery || roleFilter) && ' (filtrati)'}
          </span>
        </div>
      </div>

      {/* Players Grid */}
      {filteredPlayers.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-600 mb-4">Nessun giocatore trovato</p>
          <button
            onClick={() => {
              setSearchQuery('')
              setRoleFilter('')
            }}
            className="text-blue-600 hover:text-blue-800"
          >
            Rimuovi filtri
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlayers.map((player) => (
            <div
              key={player.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-800 mb-1">
                    {player.first_name} {player.last_name}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {getRoleName(player.role_primary)}
                  </p>
                </div>
                {player.jersey_number && (
                  <div className="bg-blue-100 text-blue-800 font-bold text-2xl w-12 h-12 rounded-full flex items-center justify-center">
                    {player.jersey_number}
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <Link
                  href={`/data/player/${player.id}`}
                  className="block w-full bg-blue-600 text-white text-center px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  📊 Visualizza Dati
                </Link>

                <div className="grid grid-cols-2 gap-2">
                  <Link
                    href={`/players/${player.id}/profile`}
                    className="block text-center text-sm text-gray-600 hover:text-gray-800 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Dashboard
                  </Link>
                  <Link
                    href={`/wellness`}
                    className="block text-center text-sm text-gray-600 hover:text-gray-800 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Wellness
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
