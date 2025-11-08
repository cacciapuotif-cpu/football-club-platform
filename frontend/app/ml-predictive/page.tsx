'use client'

import { useEffect, useState } from 'react'

interface Player {
  id: string
  first_name: string
  last_name: string
  name: string
  role: string
}

interface PlayerMLSummary {
  player_id: string
  last_10_matches: number
  avg_xg: number
  avg_key_passes: number
  avg_duels_won: number
  trend_form_last_10: number
}

interface Prediction {
  player_id: string
  date: string
  target: string
  model_name: string
  model_version: string
  y_pred: number
  y_proba: number | null
}

interface PredictionsResponse {
  player_id: string
  items: Prediction[]
}

export default function MLPredictivePage() {
  const [players, setPlayers] = useState<Player[]>([])
  const [selectedPlayerId, setSelectedPlayerId] = useState<string>('')
  const [summary, setSummary] = useState<PlayerMLSummary | null>(null)
  const [predictions, setPredictions] = useState<PredictionsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingSummary, setLoadingSummary] = useState(false)
  const [loadingPredictions, setLoadingPredictions] = useState(false)
  const [retraining, setRetraining] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPlayers()
  }, [])

  useEffect(() => {
    if (selectedPlayerId) {
      fetchPlayerData()
    } else {
      setSummary(null)
      setPredictions(null)
    }
  }, [selectedPlayerId])

  const fetchPlayers = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/v1/analytics/players')
      if (!response.ok) throw new Error('Errore nel caricamento dei giocatori')
      const data = await response.json()
      setPlayers(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  const fetchPlayerData = async () => {
    setError(null)
    await Promise.all([fetchSummary(), fetchPredictions()])
  }

  const fetchSummary = async () => {
    try {
      setLoadingSummary(true)
      const response = await fetch(
        `http://localhost:8000/api/v1/analytics/player/${selectedPlayerId}/summary`
      )
      if (!response.ok) throw new Error('Errore nel caricamento del summary')
      const data = await response.json()
      setSummary(data)
    } catch (err) {
      console.error('Error fetching summary:', err)
      setSummary(null)
    } finally {
      setLoadingSummary(false)
    }
  }

  const fetchPredictions = async () => {
    try {
      setLoadingPredictions(true)
      const response = await fetch(
        `http://localhost:8000/api/v1/analytics/player/${selectedPlayerId}/predictions`
      )
      if (!response.ok) throw new Error('Errore nel caricamento delle predizioni')
      const data = await response.json()
      setPredictions(data)
    } catch (err) {
      console.error('Error fetching predictions:', err)
      setPredictions(null)
    } finally {
      setLoadingPredictions(false)
    }
  }

  const handleRetrain = async () => {
    try {
      setRetraining(true)
      setError(null)
      const response = await fetch('http://localhost:8000/api/v1/analytics/retrain', {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Errore nel retrain dei modelli')
      const result = await response.json()
      alert(`Retrain completato: ${JSON.stringify(result)}`)
      if (selectedPlayerId) {
        fetchPlayerData()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore nel retrain')
    } finally {
      setRetraining(false)
    }
  }

  const getTrendColor = (trend: number) => {
    if (trend > 0.1) return 'text-green-600'
    if (trend < -0.1) return 'text-red-600'
    return 'text-gray-600'
  }

  const getTrendIcon = (trend: number) => {
    if (trend > 0.1) return '📈'
    if (trend < -0.1) return '📉'
    return '➡️'
  }

  const selectedPlayer = players.find((p) => p.id === selectedPlayerId)

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">ML Predittivo</h1>
        <p className="text-gray-600">
          Analisi predittive basate su Machine Learning per performance e statistiche giocatori
        </p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <div className="flex justify-between items-center">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-700 hover:text-red-900">
              ×
            </button>
          </div>
        </div>
      )}

      {/* Info Card */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-500 p-6 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <span className="text-3xl">🤖</span>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-gray-800">Funzionalità ML</h3>
            <div className="mt-2 text-sm text-gray-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Summary statistiche ultimi 10 match (xG, key passes, duels won)</li>
                <li>Predizioni automatiche basate su modelli ML</li>
                <li>Trend form giocatore</li>
                <li>Retrain modelli on-demand</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Player Selection + Retrain */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Seleziona Giocatore
            </label>
            <select
              value={selectedPlayerId}
              onChange={(e) => setSelectedPlayerId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              <option value="">-- Seleziona un giocatore --</option>
              {players.map((player) => (
                <option key={player.id} value={player.id}>
                  {player.name} ({player.role})
                </option>
              ))}
            </select>
          </div>

          <div>
            <button
              onClick={handleRetrain}
              disabled={retraining}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 transition-colors font-medium"
            >
              {retraining ? '⏳ Retrain in corso...' : '🔄 Retrain Modelli'}
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {(loadingSummary || loadingPredictions) && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Player Data */}
      {selectedPlayerId && !loadingSummary && !loadingPredictions && (
        <>
          {/* Summary Section */}
          {summary && (
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                📊 Summary ML - {selectedPlayer?.name}
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Partite Analizzate</h3>
                  <p className="text-2xl font-bold text-gray-800">
                    {summary.last_10_matches}
                  </p>
                </div>

                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Media xG</h3>
                  <p className="text-2xl font-bold text-gray-800">
                    {summary.avg_xg.toFixed(2)}
                  </p>
                </div>

                <div className="bg-yellow-50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Media Key Passes</h3>
                  <p className="text-2xl font-bold text-gray-800">
                    {summary.avg_key_passes.toFixed(2)}
                  </p>
                </div>

                <div className="bg-purple-50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Media Duels Won</h3>
                  <p className="text-2xl font-bold text-gray-800">
                    {summary.avg_duels_won.toFixed(2)}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-600 mb-1">
                    Trend Form {getTrendIcon(summary.trend_form_last_10)}
                  </h3>
                  <p className={`text-2xl font-bold ${getTrendColor(summary.trend_form_last_10)}`}>
                    {summary.trend_form_last_10 > 0 ? '+' : ''}
                    {summary.trend_form_last_10.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Predictions Section */}
          {predictions && predictions.items.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                🔮 Predizioni ML
              </h2>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Data
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Target
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Modello
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Versione
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Predizione
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Probabilità
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {predictions.items.map((pred, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(pred.date).toLocaleDateString('it-IT')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {pred.target}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {pred.model_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {pred.model_version}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-1 text-sm font-medium bg-blue-100 text-blue-800 rounded">
                            {pred.y_pred.toFixed(3)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {pred.y_proba !== null ? `${(pred.y_proba * 100).toFixed(1)}%` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {predictions.items.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  Nessuna predizione disponibile per questo giocatore
                </div>
              )}
            </div>
          )}

          {/* No Data Message */}
          {!summary && !predictions && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
              <p className="text-gray-700">
                Nessun dato ML disponibile per questo giocatore.
                <br />
                Potrebbero non esserci abbastanza dati storici o il giocatore non ha partite registrate.
              </p>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!selectedPlayerId && !loading && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-6xl mb-4">🤖</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Seleziona un giocatore
          </h2>
          <p className="text-gray-600">
            Scegli un giocatore dal menu a tendina per visualizzare le analisi predittive ML
          </p>
        </div>
      )}
    </div>
  )
}

