'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

interface MetricsRow {
  date: string
  sleep_hours?: number | null
  sleep_quality?: number | null
  fatigue?: number | null
  stress?: number | null
  mood?: number | null
  doms?: number | null
  resting_hr_bpm?: number | null
  hrv_ms?: number | null
  rpe_post?: number | null
  total_distance?: number | null
  hsr?: number | null
  sprint_count?: number | null
  body_weight_kg?: number | null
  [key: string]: string | number | null | undefined
}

interface MetricsResponse {
  player_id: string
  date_from: string
  date_to: string
  rows: MetricsRow[]
}

export default function PlayerDataPage() {
  const params = useParams()
  const router = useRouter()
  const playerId = params.id as string

  const [data, setData] = useState<MetricsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() - 90)
    return d.toISOString().split('T')[0]
  })
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().split('T')[0])
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([])
  const [editingRow, setEditingRow] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [playerId, dateFrom, dateTo])

  const fetchData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const metricsParam = selectedMetrics.length > 0 ? selectedMetrics.join(',') : undefined
      const url = new URL(`http://localhost:8000/api/v1/players/${playerId}/metrics`)
      url.searchParams.set('date_from', dateFrom)
      url.searchParams.set('date_to', dateTo)
      url.searchParams.set('grouping', 'day')
      if (metricsParam) {
        url.searchParams.set('metrics', metricsParam)
      }

      const response = await fetch(url.toString(), { headers })
      if (!response.ok) throw new Error('Errore nel caricamento dei dati')
      const result = await response.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  const handleExportCSV = () => {
    if (!data || data.rows.length === 0) return

    const headers = ['Data', ...Object.keys(data.rows[0]).filter(k => k !== 'date')]
    const csvContent = [
      headers.join(','),
      ...data.rows.map(row => {
        const values = [row.date, ...headers.slice(1).map(h => row[h] ?? '')]
        return values.map(v => JSON.stringify(v)).join(',')
      })
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `dati_${playerId}_${dateFrom}_${dateTo}.csv`
    link.click()
  }

  const availableMetrics = [
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

  // Get all available columns from data
  const allColumns = data && data.rows.length > 0
    ? Object.keys(data.rows[0]).filter(k => k !== 'date')
    : availableMetrics.map(m => m.key)

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  if (error) {
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
      <div className="mb-6">
        <Link href="/players" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
          ← Torna ai giocatori
        </Link>
        <h1 className="text-3xl font-bold text-gray-800">Dati Wellness/Performance</h1>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
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
          <div className="flex items-end">
            <button
              onClick={fetchData}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Aggiorna
            </button>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleExportCSV}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              📥 Export CSV
            </button>
          </div>
        </div>

        {/* Metric Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Metriche da Visualizzare</label>
          <div className="flex flex-wrap gap-2">
            {availableMetrics.map((metric) => (
              <label key={metric.key} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedMetrics.includes(metric.key)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedMetrics([...selectedMetrics, metric.key])
                    } else {
                      setSelectedMetrics(selectedMetrics.filter(m => m !== metric.key))
                    }
                  }}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{metric.label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      {data && data.rows.length > 0 ? (
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data</th>
                {allColumns.map((col) => {
                  const metric = availableMetrics.find(m => m.key === col)
                  return (
                    <th key={col} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      {metric?.label || col}
                    </th>
                  )
                })}
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Azioni</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.rows.map((row) => (
                <tr key={row.date} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {new Date(row.date).toLocaleDateString('it-IT')}
                  </td>
                  {allColumns.map((col) => (
                    <td key={col} className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {row[col] !== null && row[col] !== undefined ? String(row[col]) : '-'}
                    </td>
                  ))}
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    <button
                      onClick={() => setEditingRow(row.date)}
                      className="text-blue-600 hover:text-blue-900 mr-2"
                    >
                      Modifica
                    </button>
                    <button
                      onClick={() => {
                        // Duplicate logic here
                        alert('Funzionalità duplica in sviluppo')
                      }}
                      className="text-green-600 hover:text-green-900"
                    >
                      Duplica
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500">Nessun dato disponibile per il periodo selezionato</p>
        </div>
      )}
    </div>
  )
}

