'use client'

import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { getPlayerWeeklyLoad } from '@/lib/api/training'
import type { WeeklyLoadResponse } from '@/types/training'

interface PlayerWeeklyLoadChartProps {
  playerId: string
  weeks?: number
}

export default function PlayerWeeklyLoadChart({ playerId, weeks = 8 }: PlayerWeeklyLoadChartProps) {
  const [data, setData] = useState<WeeklyLoadResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [playerId, weeks])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await getPlayerWeeklyLoad(playerId, weeks)
      setData(result)
    } catch (err) {
      console.error('Error fetching weekly load:', err)
      setError(err instanceof Error ? err.message : 'Errore nel caricamento dei dati')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-100 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      </div>
    )
  }

  if (!data || data.weeks.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Carico allenamento — Ultime {weeks} settimane
        </h3>
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
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
          <p className="mt-4 text-gray-500">Nessun RPE registrato nelle ultime settimane</p>
        </div>
      </div>
    )
  }

  // Format chart data
  const chartData = data.weeks.map(week => ({
    week: formatWeekLabel(week.week_start),
    carico: Number(week.weekly_load),
  }))

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-800">
          Carico allenamento — Ultime {weeks} settimane
        </h3>
        <div className="bg-blue-50 px-4 py-2 rounded">
          <span className="text-sm text-gray-600">Settimana corrente: </span>
          <span className="text-lg font-bold text-blue-600">
            {Math.round(Number(data.total_current_week))}
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="week"
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
          />
          <YAxis
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
            label={{ value: 'Carico (a.u.)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '8px 12px'
            }}
            formatter={(value: number) => [Math.round(value), 'Carico']}
          />
          <Bar
            dataKey="carico"
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 text-xs text-gray-500 text-center">
        Carico settimanale = Σ (RPE × durata sessione in minuti)
      </div>
    </div>
  )
}

function formatWeekLabel(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('it-IT', {
    day: '2-digit',
    month: 'short',
  }).format(date)
}
