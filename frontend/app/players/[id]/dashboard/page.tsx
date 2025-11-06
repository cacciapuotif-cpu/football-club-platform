'use client'

import { useEffect, useState, useMemo } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import * as Tabs from '@radix-ui/react-tabs'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import {
  getPlayerOverview,
  getPlayerProgress,
  getPlayerTrainingLoad,
  getPlayerMatchSummary,
  getPlayerReadiness,
  getPlayerAlerts,
  type PlayerOverview,
  type ProgressResponse,
  type TrainingLoadResponse,
  type MatchSummaryResponse,
  type ReadinessResponse,
  type AlertsResponse,
} from '@/lib/api/player-progress'

interface Player {
  id: string
  first_name: string
  last_name: string
  jersey_number: number | null
  role_primary: string
}

const WELLNESS_METRICS = [
  { key: 'sleep_hours', label: 'Ore Sonno', color: '#8b5cf6' },
  { key: 'sleep_quality', label: 'Qualità Sonno', color: '#6366f1' },
  { key: 'fatigue', label: 'Fatica', color: '#ef4444' },
  { key: 'soreness', label: 'Indolenzimento', color: '#f59e0b' },
  { key: 'stress', label: 'Stress', color: '#ec4899' },
  { key: 'mood', label: 'Umore', color: '#10b981' },
  { key: 'motivation', label: 'Motivazione', color: '#3b82f6' },
  { key: 'resting_hr_bpm', label: 'FC Riposo', color: '#06b6d4' },
  { key: 'hrv_ms', label: 'HRV', color: '#14b8a6' },
]

const TRAINING_METRICS = [
  { key: 'rpe_post', label: 'RPE', color: '#3b82f6' },
  { key: 'total_distance', label: 'Distanza', color: '#10b981' },
  { key: 'hsr', label: 'HSR', color: '#f59e0b' },
  { key: 'sprint_count', label: 'Sprint', color: '#ef4444' },
  { key: 'avg_hr', label: 'FC Media', color: '#ec4899' },
]

const MATCH_METRICS = [
  { key: 'pass_accuracy', label: 'Precisione Passaggi', color: '#3b82f6' },
  { key: 'passes_completed', label: 'Passaggi Completati', color: '#10b981' },
  { key: 'duels_won', label: 'Duel Vinti', color: '#f59e0b' },
  { key: 'touches', label: 'Tocchi', color: '#8b5cf6' },
  { key: 'shots_on_target', label: 'Tiri in Porta', color: '#ef4444' },
]

export default function PlayerDashboard() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const playerId = params.id as string

  // URL state for filters
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'overview')
  const [dateFrom, setDateFrom] = useState(searchParams.get('date_from') || getDefaultDateFrom())
  const [dateTo, setDateTo] = useState(searchParams.get('date_to') || getDefaultDateTo())
  const [grouping, setGrouping] = useState<'day' | 'week' | 'month'>(
    (searchParams.get('grouping') as 'day' | 'week' | 'month') || 'week'
  )

  // Selected metrics per tab
  const [selectedWellnessMetrics, setSelectedWellnessMetrics] = useState<string[]>(['sleep_quality', 'fatigue', 'mood'])
  const [selectedTrainingMetrics, setSelectedTrainingMetrics] = useState<string[]>(['rpe_post', 'total_distance'])
  const [selectedMatchMetrics, setSelectedMatchMetrics] = useState<string[]>(['pass_accuracy', 'duels_won'])

  // Data state
  const [player, setPlayer] = useState<Player | null>(null)
  const [overview, setOverview] = useState<PlayerOverview | null>(null)
  const [wellnessProgress, setWellnessProgress] = useState<ProgressResponse | null>(null)
  const [trainingLoad, setTrainingLoad] = useState<TrainingLoadResponse | null>(null)
  const [matchSummary, setMatchSummary] = useState<MatchSummaryResponse | null>(null)
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null)
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function getDefaultDateFrom(): string {
    const date = new Date()
    date.setDate(date.getDate() - 90)
    return date.toISOString().split('T')[0]
  }

  function getDefaultDateTo(): string {
    return new Date().toISOString().split('T')[0]
  }

  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams()
    params.set('tab', activeTab)
    params.set('date_from', dateFrom)
    params.set('date_to', dateTo)
    params.set('grouping', grouping)
    router.replace(`/players/${playerId}/dashboard?${params.toString()}`, { scroll: false })
  }, [activeTab, dateFrom, dateTo, grouping, playerId, router])

  useEffect(() => {
    if (playerId) {
      fetchAllData()
    }
  }, [playerId, dateFrom, dateTo, grouping, activeTab])

  const fetchAllData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch player info
      const token = localStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      
      const playerRes = await fetch(`http://localhost:8000/api/v1/players/${playerId}`, { headers })
      if (playerRes.ok) {
        const playerData = await playerRes.json()
        setPlayer(playerData)
      }

      // Fetch overview (always)
      const overviewData = await getPlayerOverview(playerId, '28d')
      setOverview(overviewData)

      // Fetch readiness, alerts, and training load (for Overview tab)
      if (activeTab === 'overview') {
        const [readinessData, alertsData, loadData] = await Promise.all([
          getPlayerReadiness(playerId, { date_from: dateFrom, date_to: dateTo }),
          getPlayerAlerts(playerId, { date_from: dateFrom, date_to: dateTo }),
          getPlayerTrainingLoad(playerId, { window_short: 7, window_long: 28 }),
        ])
        setReadiness(readinessData)
        setAlerts(alertsData)
        setTrainingLoad(loadData)
      }

      // Fetch wellness progress (for Wellness tab)
      if (activeTab === 'wellness') {
        const progressData = await getPlayerProgress(playerId, {
          date_from: dateFrom,
          date_to: dateTo,
          families: 'wellness',
          metrics: selectedWellnessMetrics.join(','),
          grouping,
        })
        setWellnessProgress(progressData)
      }

      // Fetch training load (for Allenamento tab)
      if (activeTab === 'allenamento') {
        const [loadData, trainingProgress] = await Promise.all([
          getPlayerTrainingLoad(playerId, { window_short: 7, window_long: 28 }),
          getPlayerProgress(playerId, {
            date_from: dateFrom,
            date_to: dateTo,
            families: 'training',
            metrics: selectedTrainingMetrics.join(','),
            grouping,
          }),
        ])
        setTrainingLoad(loadData)
        setWellnessProgress(trainingProgress)
      } else {
        // Reset training load when not on allenamento tab
        setTrainingLoad(null)
      }

      // Fetch match summary (for Partite tab)
      if (activeTab === 'partite') {
        const [matchData, matchProgress] = await Promise.all([
          getPlayerMatchSummary(playerId, { date_from: dateFrom, date_to: dateTo }),
          getPlayerProgress(playerId, {
            date_from: dateFrom,
            date_to: dateTo,
            families: 'match',
            metrics: selectedMatchMetrics.join(','),
            grouping,
          }),
        ])
        setMatchSummary(matchData)
        setWellnessProgress(matchProgress)
      } else {
        setMatchSummary(null)
      }

      // Fetch tactical data (for Tattico tab)
      if (activeTab === 'tattico') {
        const tacticalProgress = await getPlayerProgress(playerId, {
          date_from: dateFrom,
          date_to: dateTo,
          families: 'tactical',
          grouping,
        })
        setWellnessProgress(tacticalProgress)
      }
      
      // Reset data when switching tabs
      if (activeTab !== 'wellness' && activeTab !== 'allenamento' && activeTab !== 'partite' && activeTab !== 'tattico') {
        setWellnessProgress(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore nel caricamento dei dati')
      console.error('Dashboard fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const exportToCSV = (data: any[], filename: string) => {
    if (!data || data.length === 0) return

    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => JSON.stringify(row[header] || '')).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
  }

  const handleExportCSV = () => {
    if (activeTab === 'wellness' && wellnessProgress) {
      exportToCSV(wellnessProgress.series, `wellness_${playerId}_${dateFrom}_${dateTo}.csv`)
    } else if (activeTab === 'allenamento' && trainingLoad) {
      exportToCSV(trainingLoad.series, `training_load_${playerId}_${dateFrom}_${dateTo}.csv`)
    } else if (activeTab === 'partite' && matchSummary) {
      exportToCSV(matchSummary.matches, `matches_${playerId}_${dateFrom}_${dateTo}.csv`)
    }
  }

  if (loading && !overview) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  if (error && !overview) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <Link href="/players" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
          ← Torna ai giocatori
        </Link>
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">
              {player ? `${player.first_name} ${player.last_name}` : 'Dashboard'}
              {player?.jersey_number && (
                <span className="text-blue-600"> #{player.jersey_number}</span>
              )}
            </h1>
            <p className="text-gray-600">
              {player?.role_primary && `${player.role_primary} • `}Dashboard Completa
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Da</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">A</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Raggruppamento</label>
            <select
              value={grouping}
              onChange={(e) => setGrouping(e.target.value as 'day' | 'week' | 'month')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="day">Giornaliero</option>
              <option value="week">Settimanale</option>
              <option value="month">Mensile</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleExportCSV}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              📥 Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="w-full">
        <Tabs.List className="flex border-b border-gray-200 mb-6">
          <Tabs.Trigger
            value="overview"
            className="px-6 py-3 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:text-blue-600"
          >
            Overview
          </Tabs.Trigger>
          <Tabs.Trigger
            value="wellness"
            className="px-6 py-3 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:text-blue-600"
          >
            Wellness
          </Tabs.Trigger>
          <Tabs.Trigger
            value="allenamento"
            className="px-6 py-3 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:text-blue-600"
          >
            Allenamento
          </Tabs.Trigger>
          <Tabs.Trigger
            value="partite"
            className="px-6 py-3 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:text-blue-600"
          >
            Partite
          </Tabs.Trigger>
          <Tabs.Trigger
            value="tattico"
            className="px-6 py-3 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:text-blue-600"
          >
            Tattico
          </Tabs.Trigger>
        </Tabs.List>

        {/* Overview Tab */}
        <Tabs.Content value="overview" className="mt-6">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
                {/* Readiness Latest */}
                <div className="bg-white rounded-lg shadow p-4">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Readiness</h3>
                  <p className="text-2xl font-bold text-gray-800">
                    {readiness?.latest_value?.toFixed(1) || '-'}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    Media 7d: {readiness?.avg_7d?.toFixed(1) || '-'}
                  </p>
                </div>

                {/* ACWR Latest */}
                <div className="bg-white rounded-lg shadow p-4">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">ACWR</h3>
                  <p className="text-2xl font-bold text-gray-800">
                    {trainingLoad?.acwr_latest !== null && trainingLoad?.acwr_latest !== undefined 
                      ? trainingLoad.acwr_latest.toFixed(2) 
                      : '-'}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">Ultimo valore</p>
                </div>

                {/* Carico 7d */}
                <div className="bg-white rounded-lg shadow p-4">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Carico 7d</h3>
                  <p className="text-2xl font-bold text-gray-800">
                    {trainingLoad?.series && trainingLoad.series.length > 0
                      ? trainingLoad.series.slice(-7).reduce((sum, p) => sum + (p.srpe || 0), 0).toFixed(0)
                      : '-'}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">sRPE totale</p>
                </div>

                {/* Monotony Current Week */}
                <div className="bg-white rounded-lg shadow p-4">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Monotony</h3>
                  <p className="text-2xl font-bold text-gray-800">
                    {trainingLoad?.monotony_weekly && trainingLoad.monotony_weekly.length > 0
                      ? (trainingLoad.monotony_weekly[trainingLoad.monotony_weekly.length - 1]?.value?.toFixed(2) || '-')
                      : '-'}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">Settimana corrente</p>
                </div>

                {/* Strain Current Week */}
                <div className="bg-white rounded-lg shadow p-4">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Strain</h3>
                  <p className="text-2xl font-bold text-gray-800">
                    {trainingLoad?.strain_weekly && trainingLoad.strain_weekly.length > 0
                      ? (trainingLoad.strain_weekly[trainingLoad.strain_weekly.length - 1]?.value?.toFixed(0) || '-')
                      : '-'}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">Settimana corrente</p>
                </div>
              </div>

              {/* Alerts Banner */}
              {alerts && alerts.alerts.length > 0 && (
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <span className="text-yellow-400 text-xl">⚠️</span>
                    </div>
                    <div className="ml-3 flex-1">
                      <h3 className="text-sm font-medium text-yellow-800 mb-2">
                        Alert Recenti (ultimi 7 giorni)
                      </h3>
                      <div className="space-y-1">
                        {alerts.alerts.slice(-5).map((alert, idx) => (
                          <div key={idx} className="text-sm text-yellow-700">
                            <span className="font-medium">{alert.type}:</span> {alert.metric} - {alert.threshold} 
                            <span className="text-xs ml-2">({new Date(alert.date).toLocaleDateString('it-IT')})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Overview Charts */}
              {readiness && readiness.series.length > 0 && (
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Readiness Index</h2>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={readiness.series}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tickFormatter={(v) => new Date(v).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' })} />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Legend />
                      <ReferenceLine y={50} stroke="#9ca3af" strokeDasharray="3 3" label="Baseline" />
                      <Line type="monotone" dataKey="readiness" stroke="#3b82f6" strokeWidth={2} name="Readiness" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Family Completeness */}
              {overview && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Completezza Dati</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {overview.family_completeness.map((family) => (
                      <div key={family.family} className="border rounded-lg p-4">
                        <h3 className="text-sm font-medium text-gray-700 mb-2 capitalize">{family.family}</h3>
                        <div className="text-2xl font-bold text-gray-800">{family.completeness_pct.toFixed(1)}%</div>
                        <div className="text-xs text-gray-600 mt-1">
                          {family.days_with_data} / {family.total_days} giorni
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </Tabs.Content>

        {/* Wellness Tab */}
        <Tabs.Content value="wellness" className="mt-6">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {/* Metric Selection */}
              <div className="bg-white rounded-lg shadow p-4 mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Metriche da Visualizzare</h3>
                <div className="flex flex-wrap gap-2">
                  {WELLNESS_METRICS.map((metric) => (
                    <label key={metric.key} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedWellnessMetrics.includes(metric.key)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedWellnessMetrics([...selectedWellnessMetrics, metric.key])
                          } else {
                            setSelectedWellnessMetrics(selectedWellnessMetrics.filter(m => m !== metric.key))
                          }
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{metric.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Wellness Chart */}
              {wellnessProgress && wellnessProgress.series.length > 0 ? (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Trend Wellness</h2>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={wellnessProgress.series}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="bucket_start" 
                        tickFormatter={(v) => new Date(v).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' })} 
                      />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      {selectedWellnessMetrics.map((metricKey) => {
                        const metric = WELLNESS_METRICS.find(m => m.key === metricKey)
                        if (!metric) return null
                        return (
                          <Line
                            key={metricKey}
                            type="monotone"
                            dataKey={metricKey}
                            stroke={metric.color}
                            strokeWidth={2}
                            name={metric.label}
                            connectNulls
                          />
                        )
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow p-12 text-center">
                  <p className="text-gray-500">Nessun dato disponibile per il periodo selezionato</p>
                </div>
              )}
            </>
          )}
        </Tabs.Content>

        {/* Allenamento Tab */}
        <Tabs.Content value="allenamento" className="mt-6">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {/* Metric Selection */}
              <div className="bg-white rounded-lg shadow p-4 mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Metriche da Visualizzare</h3>
                <div className="flex flex-wrap gap-2">
                  {TRAINING_METRICS.map((metric) => (
                    <label key={metric.key} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedTrainingMetrics.includes(metric.key)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTrainingMetrics([...selectedTrainingMetrics, metric.key])
                          } else {
                            setSelectedTrainingMetrics(selectedTrainingMetrics.filter(m => m !== metric.key))
                          }
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{metric.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* ACWR Chart */}
              {trainingLoad && trainingLoad.acwr_series.length > 0 && (
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">ACWR (Acute:Chronic Workload Ratio)</h2>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={trainingLoad.acwr_series}>
                      <defs>
                        <linearGradient id="colorAcwr" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tickFormatter={(v) => new Date(v).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' })} />
                      <YAxis domain={[0, 2]} />
                      <Tooltip />
                      <Legend />
                      <ReferenceLine y={0.8} stroke="green" strokeDasharray="3 3" label="Min (0.8)" />
                      <ReferenceLine y={1.5} stroke="red" strokeDasharray="3 3" label="Max (1.5)" />
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke="#3b82f6"
                        fillOpacity={1}
                        fill="url(#colorAcwr)"
                        name="ACWR"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Monotony & Strain */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {trainingLoad && trainingLoad.monotony_weekly.length > 0 && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-bold text-gray-800 mb-4">Monotony Settimanale</h2>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={trainingLoad.monotony_weekly}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="week_start" tickFormatter={(v) => new Date(v).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' })} />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="value" fill="#f59e0b" name="Monotony" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {trainingLoad && trainingLoad.strain_weekly.length > 0 && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-bold text-gray-800 mb-4">Strain Settimanale</h2>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={trainingLoad.strain_weekly}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="week_start" tickFormatter={(v) => new Date(v).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' })} />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="value" fill="#ef4444" name="Strain" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Training Metrics Chart */}
              {wellnessProgress && wellnessProgress.series.length > 0 ? (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Metriche Allenamento</h2>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={wellnessProgress.series}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="bucket_start" 
                        tickFormatter={(v) => new Date(v).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' })} 
                      />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      {selectedTrainingMetrics.map((metricKey) => {
                        const metric = TRAINING_METRICS.find(m => m.key === metricKey)
                        if (!metric) return null
                        return (
                          <Line
                            key={metricKey}
                            type="monotone"
                            dataKey={metricKey}
                            stroke={metric.color}
                            strokeWidth={2}
                            name={metric.label}
                            connectNulls
                          />
                        )
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow p-12 text-center">
                  <p className="text-gray-500">Nessun dato disponibile per il periodo selezionato</p>
                </div>
              )}
            </>
          )}
        </Tabs.Content>

        {/* Partite Tab */}
        <Tabs.Content value="partite" className="mt-6">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {/* Aggregates */}
              {matchSummary && matchSummary.aggregates && Object.keys(matchSummary.aggregates).length > 0 && (
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Aggregati Periodo</h2>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {matchSummary.aggregates.total_matches !== undefined && (
                      <div>
                        <p className="text-sm text-gray-500">Partite</p>
                        <p className="text-2xl font-bold text-gray-800">{matchSummary.aggregates.total_matches}</p>
                      </div>
                    )}
                    {matchSummary.aggregates.avg_minutes !== undefined && (
                      <div>
                        <p className="text-sm text-gray-500">Minuti Medi</p>
                        <p className="text-2xl font-bold text-gray-800">{matchSummary.aggregates.avg_minutes.toFixed(1)}</p>
                      </div>
                    )}
                    {matchSummary.aggregates.avg_pass_accuracy !== undefined && (
                      <div>
                        <p className="text-sm text-gray-500">Precisione Passaggi</p>
                        <p className="text-2xl font-bold text-gray-800">{matchSummary.aggregates.avg_pass_accuracy.toFixed(1)}%</p>
                      </div>
                    )}
                    {matchSummary.aggregates.total_passes !== undefined && (
                      <div>
                        <p className="text-sm text-gray-500">Passaggi Totali</p>
                        <p className="text-2xl font-bold text-gray-800">{matchSummary.aggregates.total_passes}</p>
                      </div>
                    )}
                    {matchSummary.aggregates.total_duels_won !== undefined && (
                      <div>
                        <p className="text-sm text-gray-500">Duel Vinti</p>
                        <p className="text-2xl font-bold text-gray-800">{matchSummary.aggregates.total_duels_won}</p>
                      </div>
                    )}
                    {matchSummary.aggregates.total_touches !== undefined && (
                      <div>
                        <p className="text-sm text-gray-500">Tocchi Totali</p>
                        <p className="text-2xl font-bold text-gray-800">{matchSummary.aggregates.total_touches}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Match Metrics Chart */}
              {wellnessProgress && wellnessProgress.series.length > 0 ? (
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Trend Metriche Partite</h2>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={wellnessProgress.series}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="bucket_start" 
                        tickFormatter={(v) => new Date(v).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' })} 
                      />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      {selectedMatchMetrics.map((metricKey) => {
                        const metric = MATCH_METRICS.find(m => m.key === metricKey)
                        if (!metric) return null
                        return (
                          <Line
                            key={metricKey}
                            type="monotone"
                            dataKey={metricKey}
                            stroke={metric.color}
                            strokeWidth={2}
                            name={metric.label}
                            connectNulls
                          />
                        )
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow p-12 text-center">
                  <p className="text-gray-500">Nessun dato disponibile per il periodo selezionato</p>
                </div>
              )}

              {/* Matches Table */}
              {matchSummary && matchSummary.matches.length > 0 && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Dettaglio Partite</h2>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avversario</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Minuti</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Passaggi</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duel</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tocchi</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {matchSummary.matches.map((match) => (
                          <tr key={match.match_id}>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {new Date(match.match_date).toLocaleDateString('it-IT')}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {match.is_home ? '🏠' : '✈️'} {match.opponent}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">{match.minutes_played}</td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              {match.passes_completed || '-'} ({match.pass_accuracy?.toFixed(0) || '-'}%)
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">{match.duels_won || '-'}</td>
                            <td className="px-4 py-3 text-sm text-gray-500">{match.touches || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </Tabs.Content>

        {/* Tattico Tab */}
        <Tabs.Content value="tattico" className="mt-6">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {wellnessProgress && wellnessProgress.series.length > 0 ? (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Metriche Tattiche</h2>
                  <p className="text-sm text-gray-600 mb-4">
                    Visualizzazione delle metriche tattiche (pressures, recoveries, progressive passes, etc.)
                  </p>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={wellnessProgress.series}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="bucket_start" 
                        tickFormatter={(v) => new Date(v).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' })} 
                      />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="pressures" stroke="#3b82f6" strokeWidth={2} name="Pressures" connectNulls />
                      <Line type="monotone" dataKey="recoveries_def_third" stroke="#10b981" strokeWidth={2} name="Recoveries Def" connectNulls />
                      <Line type="monotone" dataKey="progressive_passes" stroke="#f59e0b" strokeWidth={2} name="Progressive Passes" connectNulls />
                      <Line type="monotone" dataKey="xthreat_contrib" stroke="#ef4444" strokeWidth={2} name="xThreat" connectNulls />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow p-12 text-center">
                  <p className="text-gray-500">Nessun dato tattico disponibile per il periodo selezionato</p>
                  <p className="text-sm text-gray-400 mt-2">I dati tattici vengono popolati durante le partite</p>
                </div>
              )}
            </>
          )}
        </Tabs.Content>
      </Tabs.Root>
    </div>
  )
}
