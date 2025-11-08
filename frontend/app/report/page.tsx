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

export default function ReportPage() {
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

  const getRoleColor = (role: string) => {
    const colors: Record<string, string> = {
      GK: 'bg-yellow-100 text-yellow-800',
      DF: 'bg-blue-100 text-blue-800',
      MF: 'bg-green-100 text-green-800',
      FW: 'bg-red-100 text-red-800',
    }
    return colors[role] || 'bg-gray-100 text-gray-800'
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">Report Wellness</h1>
        <p className="text-gray-600">
          Seleziona un giocatore per visualizzare i report analitici con grafici e KPI
        </p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Info Card */}
      <div className="bg-purple-50 border-l-4 border-purple-400 p-6 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-purple-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-purple-800">Report Disponibili</h3>
            <div className="mt-2 text-sm text-purple-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Grafici di tendenza per metriche wellness e performance</li>
                <li>KPI aggregati: min, max, media, trend percentuale</li>
                <li>Raggruppamento dati per giorno, settimana o mese</li>
                <li>Export CSV dei dati analizzati</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filtra per ruolo
            </label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
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
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
        <div className="flex items-center space-x-2">
          <svg
            className="h-5 w-5 text-purple-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <span className="text-sm text-purple-800">
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
            className="text-purple-600 hover:text-purple-800"
          >
            Rimuovi filtri
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlayers.map((player) => (
            <div
              key={player.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-t-4 border-purple-500"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-800 mb-1">
                    {player.first_name} {player.last_name}
                  </h3>
                  <span className={`inline-block px-2 py-1 text-xs rounded-full ${getRoleColor(player.role_primary)}`}>
                    {getRoleName(player.role_primary)}
                  </span>
                </div>
                {player.jersey_number && (
                  <div className="bg-purple-100 text-purple-800 font-bold text-2xl w-12 h-12 rounded-full flex items-center justify-center">
                    {player.jersey_number}
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <Link
                  href={`/report/player/${player.id}`}
                  className="block w-full bg-purple-600 text-white text-center px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium"
                >
                  📈 Visualizza Report
                </Link>

                <div className="grid grid-cols-2 gap-2">
                  <Link
                    href={`/data/player/${player.id}`}
                    className="block text-center text-sm text-gray-600 hover:text-gray-800 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Dati
                  </Link>
                  <Link
                    href={`/players/${player.id}/profile`}
                    className="block text-center text-sm text-gray-600 hover:text-gray-800 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Dashboard
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
