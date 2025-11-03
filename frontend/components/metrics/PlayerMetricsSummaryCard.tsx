'use client'

import { useEffect, useState } from 'react'
import { getPlayerMetricsLatest } from '@/lib/api/metrics'
import type { PlayerMetricsLatest } from '@/types/metrics'

interface PlayerMetricsSummaryCardProps {
  playerId: string
}

export default function PlayerMetricsSummaryCard({ playerId }: PlayerMetricsSummaryCardProps) {
  const [data, setData] = useState<PlayerMetricsLatest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [playerId])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await getPlayerMetricsLatest(playerId)
      setData(result)
    } catch (err) {
      console.error('Error fetching metrics:', err)
      setError('Nessun dato disponibile')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8 text-gray-500">{error}</div>
      </div>
    )
  }

  const getACWRBadge = (acwr: number | null) => {
    if (acwr === null) return { color: 'gray', label: 'N/A' }
    if (acwr < 0.8) return { color: 'blue', label: 'Basso' }
    if (acwr <= 1.3) return { color: 'green', label: 'Ottimale' }
    if (acwr <= 1.5) return { color: 'yellow', label: 'Moderato' }
    return { color: 'red', label: 'Sovraccarico' }
  }

  const acwrBadge = getACWRBadge(data.acwr)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-800">Metriche Attuali</h3>
        <span className="text-sm text-gray-500">
          {new Date(data.date).toLocaleDateString('it-IT')}
        </span>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* ACWR */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-2">ACWR</div>
          <div className="text-2xl font-bold text-gray-800">
            {data.acwr !== null ? data.acwr.toFixed(2) : 'N/A'}
          </div>
          <span className={`inline-block mt-2 px-2 py-1 rounded text-xs font-medium bg-${acwrBadge.color}-100 text-${acwrBadge.color}-800`}>
            {acwrBadge.label}
          </span>
        </div>

        {/* Monotony */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-2">Monotonia</div>
          <div className="text-2xl font-bold text-gray-800">
            {data.monotony !== null ? data.monotony.toFixed(2) : 'N/A'}
          </div>
          <span className="text-xs text-gray-500 mt-2">variabilità carico</span>
        </div>

        {/* Strain */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-2">Strain</div>
          <div className="text-2xl font-bold text-gray-800">
            {data.strain !== null ? Math.round(data.strain) : 'N/A'}
          </div>
          <span className="text-xs text-gray-500 mt-2">unità di carico</span>
        </div>

        {/* Readiness */}
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-2">Readiness</div>
          <div className="text-2xl font-bold text-blue-600">
            {data.readiness !== null ? Math.round(data.readiness) : 'N/A'}
          </div>
          <span className="text-xs text-gray-500 mt-2">
            {data.readiness !== null && '/100'}
          </span>
        </div>
      </div>

      {/* Info tooltip */}
      <div className="mt-4 p-3 bg-blue-50 rounded text-xs text-blue-800">
        <strong>ACWR ottimale:</strong> 0.8-1.3 |
        <strong className="ml-2">Monotonia bassa:</strong> &lt;2.0 |
        <strong className="ml-2">Readiness:</strong> 0-100 (più alto = meglio)
      </div>
    </div>
  )
}
