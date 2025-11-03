'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import PlayerStatusBadge from '@/components/alerts/PlayerStatusBadge'
import PlayerAlertsList from '@/components/alerts/PlayerAlertsList'

interface Player {
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
  weight_kg: number | null
  is_active: boolean
  is_injured: boolean
  is_minor: boolean
  guardian_name: string | null
  guardian_email: string | null
  guardian_phone: string | null
  consent_given: boolean
  consent_date: string | null
  notes: string | null
}

interface TrainingSession {
  id: string
  session_date: string
  session_type: string
  duration_min: number
  focus: string | null
  description: string | null
}

export default function PlayerDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const [player, setPlayer] = useState<Player | null>(null)
  const [sessions, setSessions] = useState<TrainingSession[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingSessions, setLoadingSessions] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Skip authentication in development mode
    if (process.env.NEXT_PUBLIC_SKIP_AUTH === 'true') {
      fetchPlayer()
      return
    }

    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    fetchPlayer()
  }, [params.id, router])

  const fetchPlayer = async () => {
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

      const response = await fetch(`http://localhost:8000/api/v1/players/${params.id}`, {
        headers,
      })

      if (!response.ok) {
        throw new Error('Errore nel caricamento del giocatore')
      }

      const data = await response.json()
      setPlayer(data)
      fetchSessions()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  const fetchSessions = async () => {
    try {
      setLoadingSessions(true)
      const token = localStorage.getItem('access_token')

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }

      // Add auth header only if not in skip mode
      if (process.env.NEXT_PUBLIC_SKIP_AUTH !== 'true' && token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`http://localhost:8000/api/v1/players/${params.id}/sessions`, {
        headers,
      })

      if (response.ok) {
        const data = await response.json()
        setSessions(data)
      }
    } catch (err) {
      console.error('Error loading sessions:', err)
    } finally {
      setLoadingSessions(false)
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

  const getFootName = (foot: string) => {
    const feet: Record<string, string> = {
      LEFT: 'Sinistro',
      RIGHT: 'Destro',
      BOTH: 'Entrambi',
    }
    return feet[foot] || foot
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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(date)
  }

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
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

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="text-xl text-gray-600">Caricamento...</div>
        </div>
      </div>
    )
  }

  if (error || !player) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error || 'Giocatore non trovato'}
        </div>
        <Link href="/players" className="text-blue-600 hover:text-blue-800">
          ← Torna alla lista giocatori
        </Link>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-6">
        <Link href="/players" className="text-blue-600 hover:text-blue-800">
          ← Torna alla lista giocatori
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-8">
        {/* Header */}
        <div className="flex justify-between items-start mb-8 pb-6 border-b">
          <div className="flex items-center gap-6">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center text-white text-4xl font-bold">
              {player.jersey_number || '?'}
            </div>
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-4xl font-bold text-gray-800">
                  {player.first_name} {player.last_name}
                </h1>
                <PlayerStatusBadge playerId={player.id} size="md" />
              </div>
              <div className="flex gap-2 flex-wrap">
                <span className="px-3 py-1 text-sm rounded-full bg-blue-100 text-blue-800 font-medium">
                  {getRoleName(player.role_primary)}
                </span>
                {player.role_secondary && (
                  <span className="px-3 py-1 text-sm rounded-full bg-gray-100 text-gray-800 font-medium">
                    {getRoleName(player.role_secondary)}
                  </span>
                )}
                {player.is_injured && (
                  <span className="px-3 py-1 text-sm rounded-full bg-red-100 text-red-800 font-medium">
                    Infortunato
                  </span>
                )}
                {!player.is_active && (
                  <span className="px-3 py-1 text-sm rounded-full bg-gray-100 text-gray-800 font-medium">
                    Non attivo
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Link
              href={`/players/${player.id}/dashboard`}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Dashboard
            </Link>
            <Link
              href={`/players/${player.id}/load`}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Carico RPE
            </Link>
            <Link
              href={`/players/${player.id}/edit`}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Modifica
            </Link>
          </div>
        </div>

        {/* Basic Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Dati Anagrafici</h2>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Data di Nascita</p>
                <p className="text-lg font-medium text-gray-800">
                  {formatDate(player.date_of_birth)} ({calculateAge(player.date_of_birth)} anni)
                </p>
              </div>
              {player.place_of_birth && (
                <div>
                  <p className="text-sm text-gray-600">Luogo di Nascita</p>
                  <p className="text-lg font-medium text-gray-800">{player.place_of_birth}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-gray-600">Nazionalità</p>
                <p className="text-lg font-medium text-gray-800">{player.nationality}</p>
              </div>
              {player.tax_code && (
                <div>
                  <p className="text-sm text-gray-600">Codice Fiscale</p>
                  <p className="text-lg font-medium text-gray-800">{player.tax_code}</p>
                </div>
              )}
            </div>
          </div>

          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Dati Tecnici</h2>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Ruolo Primario</p>
                <p className="text-lg font-medium text-gray-800">{getRoleName(player.role_primary)}</p>
              </div>
              {player.role_secondary && (
                <div>
                  <p className="text-sm text-gray-600">Ruolo Secondario</p>
                  <p className="text-lg font-medium text-gray-800">{getRoleName(player.role_secondary)}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-gray-600">Piede Dominante</p>
                <p className="text-lg font-medium text-gray-800">{getFootName(player.dominant_foot)}</p>
              </div>
              {player.jersey_number && (
                <div>
                  <p className="text-sm text-gray-600">Numero Maglia</p>
                  <p className="text-lg font-medium text-gray-800">{player.jersey_number}</p>
                </div>
              )}
            </div>
          </div>

          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Dati Fisici</h2>
            <div className="space-y-3">
              {player.height_cm && (
                <div>
                  <p className="text-sm text-gray-600">Altezza</p>
                  <p className="text-lg font-medium text-gray-800">{player.height_cm} cm</p>
                </div>
              )}
              {player.weight_kg && (
                <div>
                  <p className="text-sm text-gray-600">Peso</p>
                  <p className="text-lg font-medium text-gray-800">{player.weight_kg} kg</p>
                </div>
              )}
              {player.height_cm && player.weight_kg && (
                <div>
                  <p className="text-sm text-gray-600">BMI</p>
                  <p className="text-lg font-medium text-gray-800">
                    {(player.weight_kg / Math.pow(player.height_cm / 100, 2)).toFixed(1)}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Contact Info */}
        {(player.email || player.phone || player.address) && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Contatti</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {player.email && (
                <div>
                  <p className="text-sm text-gray-600">Email</p>
                  <p className="text-lg font-medium text-gray-800">{player.email}</p>
                </div>
              )}
              {player.phone && (
                <div>
                  <p className="text-sm text-gray-600">Telefono</p>
                  <p className="text-lg font-medium text-gray-800">{player.phone}</p>
                </div>
              )}
              {player.address && (
                <div>
                  <p className="text-sm text-gray-600">Indirizzo</p>
                  <p className="text-lg font-medium text-gray-800">{player.address}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Guardian Info (for minors) */}
        {player.is_minor && (player.guardian_name || player.guardian_email || player.guardian_phone) && (
          <div className="mb-8 bg-yellow-50 p-6 rounded-lg">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b border-yellow-200 pb-2">
              Dati Tutore (Minorenne)
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {player.guardian_name && (
                <div>
                  <p className="text-sm text-gray-600">Nome Tutore</p>
                  <p className="text-lg font-medium text-gray-800">{player.guardian_name}</p>
                </div>
              )}
              {player.guardian_email && (
                <div>
                  <p className="text-sm text-gray-600">Email Tutore</p>
                  <p className="text-lg font-medium text-gray-800">{player.guardian_email}</p>
                </div>
              )}
              {player.guardian_phone && (
                <div>
                  <p className="text-sm text-gray-600">Telefono Tutore</p>
                  <p className="text-lg font-medium text-gray-800">{player.guardian_phone}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Consent Info */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Consensi</h2>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-4 h-4 rounded-full ${player.consent_given ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-gray-700">
                {player.consent_given ? 'Consenso GDPR dato' : 'Consenso GDPR non dato'}
              </span>
            </div>
            {player.consent_date && (
              <span className="text-sm text-gray-600">
                Data: {formatDate(player.consent_date)}
              </span>
            )}
          </div>
        </div>

        {/* Player Alerts */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">
            Alert e Notifiche
          </h2>
          <PlayerAlertsList playerId={player.id} days={14} />
        </div>

        {/* Notes */}
        {player.notes && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Note</h2>
            <p className="text-gray-700 whitespace-pre-line">{player.notes}</p>
          </div>
        )}

        {/* Training Sessions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">
            Sessioni di Allenamento ({sessions.length})
          </h2>
          {loadingSessions ? (
            <div className="text-gray-600">Caricamento sessioni...</div>
          ) : sessions.length === 0 ? (
            <div className="text-gray-600">Nessuna sessione registrata</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sessions.map((session) => (
                <div key={session.id} className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <span className="px-3 py-1 text-xs rounded-full bg-blue-100 text-blue-800 font-medium">
                      {getSessionTypeName(session.session_type)}
                    </span>
                    <span className="text-xs text-gray-600">{session.duration_min} min</span>
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-1">
                    {session.focus || 'Sessione di allenamento'}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">{formatDateTime(session.session_date)}</p>
                  {session.description && (
                    <p className="text-xs text-gray-500">{session.description}</p>
                  )}
                  <Link
                    href={`/sessions/${session.id}`}
                    prefetch={false}
                    className="inline-block mt-3 text-xs text-blue-600 hover:text-blue-800"
                  >
                    Dettagli →
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-4 pt-6 border-t">
          <Link
            href={`/players/${player.id}/dashboard`}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Vedi Dashboard
          </Link>
          <Link
            href={`/players/${player.id}/edit`}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Modifica Giocatore
          </Link>
          <button
            onClick={() => window.print()}
            className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Stampa Scheda
          </button>
        </div>
      </div>
    </div>
  )
}
