'use client'

import { use, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface TrendData {
  session_date: string
  performance_index: number
  progress_index_rolling: number | null
  distance_km: number | null
  pass_accuracy_pct: number | null
  sprints_over_25kmh: number | null
  rpe: number | null
  coach_rating: number | null
}

interface MLPrediction {
  expected_performance: number
  confidence_lower: number
  confidence_upper: number
  threshold: string
  overload_risk: {
    level: string
    probability: number
  }
  explanation: {
    natural_language: string
  }
}

interface SummaryData {
  player_id: string
  player_name: string
  total_sessions: number
  avg_performance_index: number
  max_performance_index: number
  min_performance_index: number
  training_stats: any
  match_stats: any
}

export default function PlayerDashboardEnhanced({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const router = useRouter()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<SummaryData | null>(null)
  const [trendData, setTrendData] = useState<TrendData[]>([])
  const [mlPrediction, setMlPrediction] = useState<MLPrediction | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [resolvedParams.id])

  const loadDashboardData = async () => {
    try {
      setLoading(true)

      // Load summary
      const summaryRes = await fetch(`http://localhost:8000/api/v1/analytics/player/${resolvedParams.id}/summary`)
      if (summaryRes.ok) {
        const summaryData = await summaryRes.json()
        setSummary(summaryData)
      }

      // Load trend
      const trendRes = await fetch(`http://localhost:8000/api/v1/analytics/player/${resolvedParams.id}/trend?limit=20`)
      if (trendRes.ok) {
        const trend = await trendRes.json()
        setTrendData(trend)
      }

      // Load ML prediction
      const mlRes = await fetch(`http://localhost:8000/api/v1/ml/predict/${resolvedParams.id}?recent_sessions=10`, {
        method: 'POST'
      })
      if (mlRes.ok) {
        const prediction = await mlRes.json()
        setMlPrediction(prediction)
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore nel caricamento dati')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Caricamento dashboard...</p>
        </div>
      </div>
    )
  }

  if (error || !summary) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error || 'Dati non trovati'}
        </div>
      </div>
    )
  }

  // Calculate statistics for visualization
  const performanceValues = trendData.map(d => d.performance_index)
  const avgPerformance = performanceValues.reduce((a, b) => a + b, 0) / performanceValues.length
  const maxPerformance = Math.max(...performanceValues)

  // Threshold colors
  const thresholdColor = {
    'attenzione': 'red',
    'neutro': 'yellow',
    'in_crescita': 'green'
  }[mlPrediction?.threshold || 'neutro']

  const riskColor = {
    'low': 'green',
    'medium': 'yellow',
    'high': 'red'
  }[mlPrediction?.overload_risk.level || 'low']

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <Link href="/players" className="text-blue-600 hover:text-blue-800">
          ← Torna ai giocatori
        </Link>
      </div>

      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">{summary.player_name}</h1>
        <p className="text-gray-600">Dashboard Completa - Analisi Performance & Predizioni ML</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="text-sm font-medium text-gray-500 mb-1">Sessioni Totali</div>
          <div className="text-3xl font-bold text-blue-600">{summary.total_sessions}</div>
          <div className="text-xs text-gray-500 mt-1">
            Training: {summary.training_stats.count} | Match: {summary.match_stats.count}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="text-sm font-medium text-gray-500 mb-1">Performance Media</div>
          <div className="text-3xl font-bold text-green-600">{summary.avg_performance_index}</div>
          <div className="text-xs text-gray-500 mt-1">
            Range: {summary.min_performance_index} - {summary.max_performance_index}
          </div>
        </div>

        {/* Z-Score Baseline card temporaneamente rimossa - proprietà non disponibile nel backend */}

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="text-sm font-medium text-gray-500 mb-1">Training vs Match</div>
          <div className="text-xl font-bold text-purple-600">
            {summary.training_stats.avg_performance} / {summary.match_stats.avg_performance}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Performance media
          </div>
        </div>
      </div>

      {/* ML Prediction Card */}
      {mlPrediction && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">🤖 Predizione Machine Learning</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Performance Prediction */}
            <div>
              <div className="bg-white rounded-lg p-4">
                <div className="text-sm font-medium text-gray-600 mb-2">Performance Attesa</div>
                <div className="flex items-baseline gap-3 mb-3">
                  <div className="text-4xl font-bold text-blue-600">
                    {mlPrediction.expected_performance.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-500">
                    [{mlPrediction.confidence_lower.toFixed(1)} - {mlPrediction.confidence_upper.toFixed(1)}]
                  </div>
                </div>

                {/* Threshold indicator */}
                <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold
                  ${mlPrediction.threshold === 'in_crescita' ? 'bg-green-100 text-green-800' :
                    mlPrediction.threshold === 'attenzione' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'}`}>
                  {mlPrediction.threshold === 'in_crescita' ? '↗ In Crescita' :
                   mlPrediction.threshold === 'attenzione' ? '⚠ Attenzione' :
                   '→ Neutro'}
                </div>

                {/* Progress bar */}
                <div className="mt-4 w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      mlPrediction.threshold === 'in_crescita' ? 'bg-green-500' :
                      mlPrediction.threshold === 'attenzione' ? 'bg-red-500' :
                      'bg-yellow-500'
                    }`}
                    style={{ width: `${mlPrediction.expected_performance}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Overload Risk */}
            <div>
              <div className="bg-white rounded-lg p-4">
                <div className="text-sm font-medium text-gray-600 mb-2">Rischio Sovraccarico</div>
                <div className="flex items-baseline gap-3 mb-3">
                  <div className={`text-4xl font-bold ${
                    mlPrediction.overload_risk.level === 'low' ? 'text-green-600' :
                    mlPrediction.overload_risk.level === 'medium' ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {(mlPrediction.overload_risk.probability * 100).toFixed(0)}%
                  </div>
                </div>

                {/* Risk level badge */}
                <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold
                  ${mlPrediction.overload_risk.level === 'low' ? 'bg-green-100 text-green-800' :
                    mlPrediction.overload_risk.level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'}`}>
                  {mlPrediction.overload_risk.level === 'low' ? '✓ Basso' :
                   mlPrediction.overload_risk.level === 'medium' ? '⚠ Medio' :
                   '⛔ Alto'}
                </div>

                {/* Risk bar */}
                <div className="mt-4 w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      mlPrediction.overload_risk.level === 'low' ? 'bg-green-500' :
                      mlPrediction.overload_risk.level === 'medium' ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${mlPrediction.overload_risk.probability * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Explanation */}
          <div className="mt-4 bg-white rounded-lg p-4">
            <div className="text-sm font-medium text-gray-600 mb-2">📊 Spiegazione</div>
            <p className="text-gray-800">{mlPrediction.explanation.natural_language}</p>
          </div>
        </div>
      )}

      {/* Performance Trend Chart (Simple ASCII/Text visualization) */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">📈 Trend Performance (Ultimi 20 Allenamenti)</h2>

        {/* Simple table visualization */}
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Data</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Performance</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Progress Rolling</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Distanza (km)</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Pass Acc.%</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Sprint {'>'}25</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">RPE</th>
              </tr>
            </thead>
            <tbody>
              {trendData.map((row, i) => (
                <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-4 py-2 text-sm">{row.session_date}</td>
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{row.performance_index.toFixed(1)}</span>
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${row.performance_index}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-sm">
                    {row.progress_index_rolling ? row.progress_index_rolling.toFixed(1) : '-'}
                  </td>
                  <td className="px-4 py-2 text-sm">
                    {row.distance_km ? row.distance_km.toFixed(1) : '-'}
                  </td>
                  <td className="px-4 py-2 text-sm">
                    {row.pass_accuracy_pct ? row.pass_accuracy_pct.toFixed(1) : '-'}
                  </td>
                  <td className="px-4 py-2 text-sm">
                    {row.sprints_over_25kmh || '-'}
                  </td>
                  <td className="px-4 py-2 text-sm">
                    <span className={`font-semibold ${
                      row.rpe && row.rpe >= 8 ? 'text-red-600' :
                      row.rpe && row.rpe >= 6 ? 'text-yellow-600' :
                      'text-green-600'
                    }`}>
                      {row.rpe ? row.rpe.toFixed(1) : '-'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Key Metrics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Metriche Fisiche Recenti</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Distanza Media</span>
              <span className="font-semibold">
                {trendData.slice(0, 5).reduce((a, b) => a + (b.distance_km || 0), 0) / Math.min(5, trendData.length) || 0} km
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Sprint Media</span>
              <span className="font-semibold">
                {Math.round(trendData.slice(0, 5).reduce((a, b) => a + (b.sprints_over_25kmh || 0), 0) / Math.min(5, trendData.length) || 0)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">RPE Medio</span>
              <span className="font-semibold">
                {(trendData.slice(0, 5).reduce((a, b) => a + (b.rpe || 0), 0) / Math.min(5, trendData.length) || 0).toFixed(1)}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Metriche Tecniche Recenti</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Pass Accuracy Media</span>
              <span className="font-semibold">
                {(trendData.slice(0, 5).reduce((a, b) => a + (b.pass_accuracy_pct || 0), 0) / Math.min(5, trendData.length) || 0).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Valutazione Allenatore</span>
              <span className="font-semibold">
                {(trendData.slice(0, 5).reduce((a, b) => a + (b.coach_rating || 0), 0) / Math.min(5, trendData.length) || 0).toFixed(1)} /10
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Azioni Raccomandate</h3>
          <div className="space-y-2">
            {mlPrediction && mlPrediction.overload_risk.level === 'high' && (
              <div className="text-sm bg-red-50 text-red-800 p-2 rounded">
                ⚠️ Ridurre carico allenamento
              </div>
            )}
            {mlPrediction && mlPrediction.threshold === 'in_crescita' && (
              <div className="text-sm bg-green-50 text-green-800 p-2 rounded">
                ✓ Momento positivo - mantenere programma
              </div>
            )}
            {/* Baseline Z-score indicator temporaneamente rimosso - proprietà non disponibile */}
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="mt-8 flex gap-4">
        <button
          onClick={() => router.push(`/sessions/new`)}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + Nuova Sessione
        </button>
        <button
          onClick={loadDashboardData}
          className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
        >
          🔄 Aggiorna Dati
        </button>
      </div>
    </div>
  )
}
