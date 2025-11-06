'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface Player {
  id: string
  first_name: string
  last_name: string
  date_of_birth: string
  role_primary: string
  jersey_number: number | null
  is_active: boolean
  is_injured: boolean
}

export default function PlayersPage() {
  const router = useRouter()
  const [players, setPlayers] = useState<Player[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Skip authentication in development mode
    if (process.env.NEXT_PUBLIC_SKIP_AUTH === 'true') {
      fetchPlayers()
      return
    }

    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    fetchPlayers()
  }, [router])

  const fetchPlayers = async () => {
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

  const calculateAge = (birthDate: string) => {
    const today = new Date()
    const birth = new Date(birthDate)
    let age = today.getFullYear() - birth.getFullYear()
    const monthDiff = today.getMonth() - birth.getMonth()
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--
    }
    return age
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
        <h1 className="text-3xl font-bold text-gray-800">Giocatori</h1>
        <Link
          href="/players/new"
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          + Nuovo Giocatore
        </Link>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {players.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-600 mb-4">Nessun giocatore registrato</p>
          <Link
            href="/players/new"
            className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Aggiungi il primo giocatore
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  #
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nome
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Età
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ruolo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Stato
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Azioni
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {players.map((player) => (
                <tr key={player.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {player.jersey_number || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {player.first_name} {player.last_name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {calculateAge(player.date_of_birth)} anni
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {getRoleName(player.role_primary)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex gap-2">
                      {player.is_injured && (
                        <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                          Infortunato
                        </span>
                      )}
                      {!player.is_active && (
                        <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                          Non attivo
                        </span>
                      )}
                      {player.is_active && !player.is_injured && (
                        <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                          Attivo
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <Link
                      href={`/players/${player.id}/profile`}
                      className="text-green-600 hover:text-green-900 mr-3"
                    >
                      Dashboard
                    </Link>
                    <Link
                      href={`/data/player/${player.id}`}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      Dati
                    </Link>
                    <Link
                      href={`/report/player/${player.id}`}
                      className="text-purple-600 hover:text-purple-900 mr-3"
                    >
                      Report
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
