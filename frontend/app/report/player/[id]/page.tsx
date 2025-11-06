'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface ReportPoint {
  bucket_start: string
  value: number | null
}

interface ReportKPI {
  metric: string
  min_value: number | null
  max_value: number | null
  avg_value: number | null
  trend_pct: number | null
}

interface ReportResponse {
  player_id: string
  metric: string
  date_from: string
  date_to: string
  grouping: string
  series: ReportPoint[]
  kpi: ReportKPI
}

const AVAILABLE_METRICS = [
  { key: 'sleep_hours', label: 'Ore Sonno' },
  { key: 'sleep_quality', label: 'Qualità Sonno' },
  { key: 'fatigue', label: 'Fatica' },
  { key: 'stress', label: 'Stress' },
  { key: 'mood', label: 'Umore' },
  { key: 'doms', label: 'DOMS' },
  { key: 'resting_hr_bpm', label: 'FC Riposo' },
  { key: 'hrv_ms', label: 'HRV' },
  { key: 'rpe_post', label: 'RPE' },
  { key: 'total_distance', label: 'Distanza' },
  { key: 'hsr', label: 'HSR' },
  { key: 'sprint_count', label: 'Sprint' },
  { key: 'body_weight_kg', label: 'Peso' },
]

export default function PlayerReportPage() {
  const params = useParams()
  const playerId = params.id as string

  const [report, setReport] = useState<ReportResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedMetric, setSelectedMetric] = useState('sleep_quality')
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() - 90)
    return d.toISOString().split('T')[0]
  })
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().split('T')[0])
  const [grouping, setGrouping] = useState<'day' | 'week' | 'month'>('week')

  useEffect(() => {
    fetchReport()
  }, [playerId, selectedMetric, dateFrom, dateTo, grouping])

  const fetchReport = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const url = new URL(`http://localhost:8000/api/v1/players/${playerId}/report`)
      url.searchParams.set('metric', selectedMetric)
      url.searchParams.set('date_from', dateFrom)
      url.searchParams.set('date_to', dateTo)
      url.searchParams.set('grouping', grouping)

      const response = await fetch(url.toString(), { headers })
      if (!response.ok) throw new Error('Errore nel caricamento del report')
      const result = await response.json()
      setReport(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  const handleExportCSV = () => {
    if (!report || report.series.length === 0) return

    const csvContent = [
      'Data,Valore',
      ...report.series.map(p => `${p.bucket_start},${p.value ?? ''}`)
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `report_${playerId}_${selectedMetric}_${dateFrom}_${dateTo}.csv`
    link.click()
  }

  const chartData = report?.series.map(p => ({
    date: new Date(p.bucket_start).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' }),
    value: p.value,
  })) || []

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-6">
        <Link href="/players" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
          ← Torna ai giocatori
        </Link>
        <h1 className="text-3xl font-bold text-gray-800">Report Analisi Metrica</h1>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Metrica</label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              {AVAILABLE_METRICS.map(m => (
                <option key={m.key} value={m.key}>{m.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Da</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">A</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Raggruppamento</label>
            <select
              value={grouping}
              onChange={(e) => setGrouping(e.target.value as 'day' | 'week' | 'month')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="day">Giornaliero</option>
              <option value="week">Settimanale</option>
              <option value="month">Mensile</option>
            </select>
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={handleExportCSV}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            📥 Export CSV
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      ) : report ? (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Minimo</h3>
              <p className="text-2xl font-bold text-gray-800">
                {report.kpi.min_value?.toFixed(2) ?? '-'}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Massimo</h3>
              <p className="text-2xl font-bold text-gray-800">
                {report.kpi.max_value?.toFixed(2) ?? '-'}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Media</h3>
              <p className="text-2xl font-bold text-gray-800">
                {report.kpi.avg_value?.toFixed(2) ?? '-'}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Trend</h3>
              <p className={`text-2xl font-bold ${report.kpi.trend_pct && report.kpi.trend_pct > 0 ? 'text-green-600' : report.kpi.trend_pct && report.kpi.trend_pct < 0 ? 'text-red-600' : 'text-gray-800'}`}>
                {report.kpi.trend_pct !== null ? `${report.kpi.trend_pct > 0 ? '+' : ''}${report.kpi.trend_pct.toFixed(1)}%` : '-'}
              </p>
            </div>
          </div>

          {/* Chart */}
          {chartData.length > 0 ? (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">
                {AVAILABLE_METRICS.find(m => m.key === selectedMetric)?.label || selectedMetric}
              </h2>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} name="Valore" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <p className="text-gray-500">Nessun dato disponibile per la metrica selezionata</p>
            </div>
          )}
        </>
      ) : null}
    </div>
  )
}

