'use client'

import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { API_URL } from '@/lib/api'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
  ComposedChart,
  Bar,
} from 'recharts'

// Metriche organizzate per categoria
const WELLNESS_METRICS = {
  core: ['sleep_quality', 'fatigue', 'soreness', 'stress', 'mood'],
  extended: ['sleep_hours', 'motivation', 'hydration', 'rpe_morning'],
  physical: ['body_weight_kg', 'resting_hr_bpm', 'hrv_ms'],
}

const TRAINING_METRICS = {
  load: ['rpe_post', 'player_load', 'total_distance'],
  intensity: ['hsr', 'sprint_count', 'top_speed'],
  movement: ['accel_count', 'decel_count'],
  heart: ['avg_hr', 'max_hr'],
}

const MATCH_METRICS = {
  passing: ['pass_accuracy', 'pass_completed'],
  duels: ['duels_won', 'touches'],
  actions: ['dribbles_success', 'interceptions', 'tackles', 'shots_on_target'],
}

type Bucket = 'daily' | 'weekly' | 'monthly'
type Section = 'wellness' | 'training' | 'match' | 'overview'

interface ProgressPoint {
  bucket_start: string
  [key: string]: number | string | Record<string, number> | null | undefined
}

interface TrainingLoadPoint {
  date: string
  srpe: number
  acute?: number
  chronic?: number
  acwr?: number
}

interface OverviewData {
  window_days: number
  wellness_days_with_data: number
  wellness_completeness_pct: number
  last_values: Record<string, number | null>
  training_sessions: number
  present_count: number
  avg_srpe_last_7d: number | null
  avg_srpe_last_28d: number | null
}

const COLORS = {
  sleep_quality: '#4f46e5',
  sleep_hours: '#6366f1',
  stress: '#f59e0b',
  fatigue: '#dc2626',
  soreness: '#16a34a',
  mood: '#0ea5e9',
  motivation: '#8b5cf6',
  hydration: '#06b6d4',
  rpe_morning: '#ef4444',
  body_weight_kg: '#84cc16',
  resting_hr_bpm: '#f97316',
  hrv_ms: '#14b8a6',
  rpe_post: '#3b82f6',
  hsr: '#ec4899',
  sprint_count: '#f43f5e',
  total_distance: '#10b981',
  accel_count: '#6366f1',
  decel_count: '#a855f7',
  top_speed: '#f59e0b',
  avg_hr: '#ef4444',
  max_hr: '#dc2626',
  player_load: '#8b5cf6',
  pass_accuracy: '#10b981',
  pass_completed: '#3b82f6',
  duels_won: '#f59e0b',
  touches: '#6366f1',
  dribbles_success: '#ec4899',
  interceptions: '#14b8a6',
  tackles: '#f97316',
  shots_on_target: '#ef4444',
}

export default function WellnessTrendPage() {
  const params = useParams()
  const playerId = params.id as string

  const [bucket, setBucket] = useState<Bucket>('weekly')
  const [dateFrom, setDateFrom] = useState<string>(
    new Date(Date.now() - 90 * 86400000).toISOString().slice(0, 10)
  )
  const [dateTo, setDateTo] = useState<string>(new Date().toISOString().slice(0, 10))
  const [period, setPeriod] = useState<'7d' | '28d' | '30d' | '90d'>('28d')
  const [activeSection, setActiveSection] = useState<Section>('overview')

  // Wellness selections
  const [wellnessCore, setWellnessCore] = useState<string[]>(WELLNESS_METRICS.core)
  const [wellnessExtended, setWellnessExtended] = useState<string[]>([])
  const [wellnessPhysical, setWellnessPhysical] = useState<string[]>([])

  // Training selections
  const [trainingLoad, setTrainingLoad] = useState<string[]>(TRAINING_METRICS.load)
  const [trainingIntensity, setTrainingIntensity] = useState<string[]>([])
  const [trainingMovement, setTrainingMovement] = useState<string[]>([])
  const [trainingHeart, setTrainingHeart] = useState<string[]>([])

  // Match selections
  const [matchPassing, setMatchPassing] = useState<string[]>(MATCH_METRICS.passing)
  const [matchDuels, setMatchDuels] = useState<string[]>([])
  const [matchActions, setMatchActions] = useState<string[]>([])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [wellnessData, setWellnessData] = useState<ProgressPoint[]>([])
  const [trainingData, setTrainingData] = useState<ProgressPoint[]>([])
  const [matchData, setMatchData] = useState<ProgressPoint[]>([])
  const [trainingLoadData, setTrainingLoadData] = useState<TrainingLoadPoint[]>([])
  const [overviewData, setOverviewData] = useState<OverviewData | null>(null)

  const wellnessMetricsQuery = useMemo(
    () => [...wellnessCore, ...wellnessExtended, ...wellnessPhysical].join(','),
    [wellnessCore, wellnessExtended, wellnessPhysical]
  )

  const trainingMetricsQuery = useMemo(
    () => [...trainingLoad, ...trainingIntensity, ...trainingMovement, ...trainingHeart].join(','),
    [trainingLoad, trainingIntensity, trainingMovement, trainingHeart]
  )

  const matchMetricsQuery = useMemo(
    () => [...matchPassing, ...matchDuels, ...matchActions].join(','),
    [matchPassing, matchDuels, matchActions]
  )

  const fetchWellness = async () => {
    try {
      const url = new URL(`${API_URL}/api/v1/players/${playerId}/progress`)
      url.searchParams.set('bucket', bucket)
      url.searchParams.set('date_from', dateFrom)
      url.searchParams.set('date_to', dateTo)
      if (wellnessMetricsQuery) url.searchParams.set('metrics', wellnessMetricsQuery)

      const res = await fetch(url.toString())
      if (!res.ok) throw new Error('Errore wellness')
      const data = await res.json()
      setWellnessData(data.series || [])
    } catch (e: any) {
      console.error('Wellness fetch error:', e)
    }
  }

  const fetchTraining = async () => {
    try {
      const url = new URL(`${API_URL}/api/v1/players/${playerId}/training-metrics`)
      url.searchParams.set('bucket', bucket)
      url.searchParams.set('date_from', dateFrom)
      url.searchParams.set('date_to', dateTo)
      if (trainingMetricsQuery) url.searchParams.set('metrics', trainingMetricsQuery)

      const res = await fetch(url.toString())
      if (!res.ok) throw new Error('Errore training')
      const data = await res.json()
      setTrainingData(data.series || [])
    } catch (e: any) {
      console.error('Training fetch error:', e)
    }
  }

  const fetchMatch = async () => {
    try {
      const url = new URL(`${API_URL}/api/v1/players/${playerId}/match-metrics`)
      url.searchParams.set('bucket', bucket)
      url.searchParams.set('date_from', dateFrom)
      url.searchParams.set('date_to', dateTo)
      if (matchMetricsQuery) url.searchParams.set('metrics', matchMetricsQuery)

      const res = await fetch(url.toString())
      if (!res.ok) throw new Error('Errore match')
      const data = await res.json()
      setMatchData(data.series || [])
    } catch (e: any) {
      console.error('Match fetch error:', e)
    }
  }

  const fetchTrainingLoad = async () => {
    try {
      const url = new URL(`${API_URL}/api/v1/players/${playerId}/training-load`)
      url.searchParams.set('acute_days', '7')
      url.searchParams.set('chronic_days', '28')

      const res = await fetch(url.toString())
      if (!res.ok) throw new Error('Errore training load')
      const data = await res.json()
      setTrainingLoadData(data.series || [])
    } catch (e: any) {
      console.error('Training load fetch error:', e)
    }
  }

  const fetchOverview = async () => {
    try {
      const url = new URL(`${API_URL}/api/v1/players/${playerId}/overview`)
      url.searchParams.set('period', period)

      const res = await fetch(url.toString())
      if (!res.ok) throw new Error('Errore overview')
      const data = await res.json()
      setOverviewData(data)
    } catch (e: any) {
      console.error('Overview fetch error:', e)
    }
  }

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([
      fetchOverview(),
      fetchTrainingLoad(),
      activeSection === 'wellness' && fetchWellness(),
      activeSection === 'training' && fetchTraining(),
      activeSection === 'match' && fetchMatch(),
    ])
      .catch(e => setError(e?.message || 'Errore nel caricamento dati'))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playerId, bucket, dateFrom, dateTo, period, activeSection, wellnessMetricsQuery, trainingMetricsQuery, matchMetricsQuery])

  const toggleMetric = (
    metric: string,
    current: string[],
    setter: (val: string[]) => void
  ) => {
    setter(current.includes(metric) ? current.filter(m => m !== metric) : [...current, metric])
  }

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr)
    if (bucket === 'daily') {
      return d.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' })
    } else if (bucket === 'weekly') {
      return `Sett ${d.toLocaleDateString('it-IT', { week: 'numeric' })}`
    } else {
      return d.toLocaleDateString('it-IT', { month: 'short' })
    }
  }

  const renderMetricButtons = (
    metrics: string[],
    selected: string[],
    setter: (val: string[]) => void,
    category: string
  ) => (
    <div className="mb-4">
      <div className="text-sm font-medium text-gray-700 mb-2 capitalize">{category}</div>
      <div className="flex flex-wrap gap-2">
        {metrics.map(m => (
          <button
            key={m}
            onClick={() => toggleMetric(m, selected, setter)}
            className={`px-3 py-1 rounded text-xs transition ${
              selected.includes(m)
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {m.replace(/_/g, ' ')}
          </button>
        ))}
      </div>
    </div>
  )

  const renderChart = (data: ProgressPoint[], metrics: string[], title: string) => {
    if (data.length === 0) {
      return (
        <div className="text-gray-500 text-center py-8">Nessun dato disponibile per {title}</div>
      )
    }

    return (
      <div className="w-full h-[450px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="bucket_start" tickFormatter={formatDate} />
            <YAxis />
            <Tooltip
              labelFormatter={v => new Date(v).toLocaleDateString('it-IT')}
              formatter={(value: any) => (value ? Number(value).toFixed(1) : 'N/A')}
            />
            <Legend />
            {metrics.map(metric => {
              const color = COLORS[metric as keyof typeof COLORS] || '#6b7280'
              return (
                <Line
                  key={metric}
                  type="monotone"
                  dataKey={metric}
                  stroke={color}
                  strokeWidth={2}
                  dot={false}
                  name={metric.replace(/_/g, ' ')}
                />
              )
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard Completa Calciatore</h1>
          <Link
            href={`/players/${playerId}`}
            prefetch={false}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Torna al giocatore
          </Link>
        </div>

        {/* Controls */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Aggregazione</label>
              <select
                value={bucket}
                onChange={e => setBucket(e.target.value as Bucket)}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option value="daily">Giornaliera</option>
                <option value="weekly">Settimanale</option>
                <option value="monthly">Mensile</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Dal</label>
              <input
                type="date"
                value={dateFrom}
                onChange={e => setDateFrom(e.target.value)}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Al</label>
              <input
                type="date"
                value={dateTo}
                onChange={e => setDateTo(e.target.value)}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Periodo Overview</label>
              <select
                value={period}
                onChange={e => setPeriod(e.target.value as '7d' | '28d' | '30d' | '90d')}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option value="7d">7 giorni</option>
                <option value="28d">28 giorni</option>
                <option value="30d">30 giorni</option>
                <option value="90d">90 giorni</option>
              </select>
            </div>
          </div>

          {/* Section Tabs */}
          <div className="flex gap-2 border-b">
            {(['overview', 'wellness', 'training', 'match'] as Section[]).map(section => (
              <button
                key={section}
                onClick={() => setActiveSection(section)}
                className={`px-4 py-2 font-medium transition ${
                  activeSection === section
                    ? 'border-b-2 border-indigo-600 text-indigo-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {section === 'overview' ? 'Overview' : section === 'wellness' ? 'Wellness' : section === 'training' ? 'Allenamento' : 'Partite'}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-600">Caricamento dati...</div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
        ) : (
          <>
            {/* Overview Section */}
            {activeSection === 'overview' && overviewData && (
              <>
                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-white p-4 rounded-lg shadow">
                    <div className="text-sm text-gray-600">Completezza Wellness</div>
                    <div className="text-2xl font-bold text-indigo-600">
                      {overviewData.wellness_completeness_pct.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {overviewData.wellness_days_with_data} giorni su {overviewData.window_days}
                    </div>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow">
                    <div className="text-sm text-gray-600">Sessioni Allenamento</div>
                    <div className="text-2xl font-bold text-green-600">{overviewData.training_sessions}</div>
                    <div className="text-xs text-gray-500 mt-1">{overviewData.present_count} presenze</div>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow">
                    <div className="text-sm text-gray-600">sRPE Media (7d)</div>
                    <div className="text-2xl font-bold text-blue-600">
                      {overviewData.avg_srpe_last_7d?.toFixed(0) || 'N/A'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">AU</div>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow">
                    <div className="text-sm text-gray-600">sRPE Media (28d)</div>
                    <div className="text-2xl font-bold text-purple-600">
                      {overviewData.avg_srpe_last_28d?.toFixed(0) || 'N/A'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">AU</div>
                  </div>
                </div>

                {/* Last Values */}
                <div className="bg-white p-6 rounded-lg shadow mb-6">
                  <h3 className="text-lg font-semibold mb-4">Ultimi Valori Wellness</h3>
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                    {Object.entries(overviewData.last_values)
                      .filter(([_, v]) => v !== null)
                      .map(([key, value]) => (
                        <div key={key} className="text-center">
                          <div className="text-sm text-gray-600 capitalize">{key.replace(/_/g, ' ')}</div>
                          <div className="text-xl font-bold text-gray-900">{value?.toFixed(1)}</div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Training Load & ACWR */}
                <div className="bg-white p-6 rounded-lg shadow">
                  <h2 className="text-xl font-semibold mb-4">Carico Allenamento & ACWR</h2>
                  {trainingLoadData.length === 0 ? (
                    <div className="text-gray-500 text-center py-8">Nessun dato disponibile</div>
                  ) : (
                    <div className="w-full h-[400px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart
                          data={trainingLoadData}
                          margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="date"
                            tickFormatter={v => new Date(v).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' })}
                          />
                          <YAxis yAxisId="left" label={{ value: 'sRPE', angle: -90, position: 'insideLeft' }} />
                          <YAxis
                            yAxisId="right"
                            orientation="right"
                            domain={[0, 2]}
                            label={{ value: 'ACWR', angle: 90, position: 'insideRight' }}
                          />
                          <Tooltip
                            labelFormatter={v => new Date(v).toLocaleDateString('it-IT')}
                            formatter={(value: any, name: string) => {
                              if (name === 'ACWR') return value ? value.toFixed(2) : 'N/A'
                              return value ? value.toFixed(0) : 'N/A'
                            }}
                          />
                          <Legend />
                          <Bar yAxisId="left" dataKey="srpe" fill="#3b82f6" name="sRPE Giornaliero" />
                          <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="acwr"
                            stroke="#dc2626"
                            strokeWidth={2}
                            dot={{ r: 4 }}
                            name="ACWR"
                          />
                          <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey={() => 1.5}
                            stroke="#ef4444"
                            strokeDasharray="5 5"
                            strokeWidth={1}
                            dot={false}
                            name="Soglia High"
                          />
                          <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey={() => 0.8}
                            stroke="#f59e0b"
                            strokeDasharray="5 5"
                            strokeWidth={1}
                            dot={false}
                            name="Soglia Low"
                          />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Wellness Section */}
            {activeSection === 'wellness' && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4">Andamento Wellness</h2>
                <div className="mb-6">
                  {renderMetricButtons(
                    WELLNESS_METRICS.core,
                    wellnessCore,
                    setWellnessCore,
                    'Core Wellness'
                  )}
                  {renderMetricButtons(
                    WELLNESS_METRICS.extended,
                    wellnessExtended,
                    setWellnessExtended,
                    'Extended Wellness'
                  )}
                  {renderMetricButtons(
                    WELLNESS_METRICS.physical,
                    wellnessPhysical,
                    setWellnessPhysical,
                    'Physical Metrics'
                  )}
                </div>
                {renderChart(
                  wellnessData,
                  [...wellnessCore, ...wellnessExtended, ...wellnessPhysical],
                  'Wellness'
                )}
              </div>
            )}

            {/* Training Section */}
            {activeSection === 'training' && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4">Metriche Allenamento</h2>
                <div className="mb-6">
                  {renderMetricButtons(
                    TRAINING_METRICS.load,
                    trainingLoad,
                    setTrainingLoad,
                    'Carico'
                  )}
                  {renderMetricButtons(
                    TRAINING_METRICS.intensity,
                    trainingIntensity,
                    setTrainingIntensity,
                    'Intensità'
                  )}
                  {renderMetricButtons(
                    TRAINING_METRICS.movement,
                    trainingMovement,
                    setTrainingMovement,
                    'Movimento'
                  )}
                  {renderMetricButtons(
                    TRAINING_METRICS.heart,
                    trainingHeart,
                    setTrainingHeart,
                    'Frequenza Cardiaca'
                  )}
                </div>
                {renderChart(
                  trainingData,
                  [...trainingLoad, ...trainingIntensity, ...trainingMovement, ...trainingHeart],
                  'Allenamento'
                )}
              </div>
            )}

            {/* Match Section */}
            {activeSection === 'match' && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4">Performance Partite</h2>
                <div className="mb-6">
                  {renderMetricButtons(
                    MATCH_METRICS.passing,
                    matchPassing,
                    setMatchPassing,
                    'Passaggi'
                  )}
                  {renderMetricButtons(
                    MATCH_METRICS.duels,
                    matchDuels,
                    setMatchDuels,
                    'Dueli'
                  )}
                  {renderMetricButtons(
                    MATCH_METRICS.actions,
                    matchActions,
                    setMatchActions,
                    'Azioni'
                  )}
                </div>
                {renderChart(
                  matchData,
                  [...matchPassing, ...matchDuels, ...matchActions],
                  'Partite'
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
