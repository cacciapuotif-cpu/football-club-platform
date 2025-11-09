'use client'

import Link from 'next/link'
import type { HeatmapCell } from '@/types/wellness'

type Props = {
  cells: HeatmapCell[]
  loading?: boolean
  emptyMessage?: string
}

const severityColor: Record<string, string> = {
  low: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  medium: 'bg-amber-100 text-amber-700 border-amber-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  critical: 'bg-red-100 text-red-700 border-red-200',
}

export function HeatmapGrid({ cells, loading = false, emptyMessage = 'Nessun atleta disponibile.' }: Props) {
  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="animate-pulse rounded-lg border border-gray-200 bg-white p-4">
            <div className="h-4 w-1/2 rounded bg-gray-200" />
            <div className="mt-3 h-8 rounded bg-gray-100" />
            <div className="mt-4 flex gap-2">
              <div className="h-6 w-16 rounded bg-gray-100" />
              <div className="h-6 w-12 rounded bg-gray-100" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (!cells.length) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-gray-500">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {cells.map((cell) => {
        const severityClass =
          (cell.risk_severity && severityColor[cell.risk_severity]) || 'bg-blue-50 text-blue-800 border-blue-100'
        return (
          <div
            key={cell.athlete_id}
            className={`flex flex-col rounded-lg border ${severityClass} p-4 shadow-sm transition hover:-translate-y-1`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-semibold">
                  {cell.full_name ?? `Athlete ${cell.athlete_id.slice(0, 6)}`}
                </p>
                {cell.role && <p className="text-xs uppercase text-gray-500">{cell.role}</p>}
              </div>
              <span className="text-xs font-semibold uppercase">{cell.risk_severity ?? 'n/a'}</span>
            </div>

            <div className="mt-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Readiness</p>
                <p className="text-xl font-bold text-gray-900">
                  {cell.readiness_score !== undefined && cell.readiness_score !== null
                    ? Math.round(cell.readiness_score)
                    : '—'}
                </p>
              </div>
              <div className="text-right text-xs text-gray-600">
                <p>
                  Δ{' '}
                  {cell.readiness_delta !== undefined && cell.readiness_delta !== null
                    ? cell.readiness_delta > 0
                      ? `+${cell.readiness_delta.toFixed(1)}`
                      : cell.readiness_delta.toFixed(1)
                    : '—'}
                </p>
                <p>⚠️ {cell.alerts_count}</p>
              </div>
            </div>

            <div className="mt-4 border-t border-white/40 pt-3">
              <Link
                href={`/athletes/${cell.athlete_id}`}
                className="text-xs font-semibold text-blue-700 hover:text-blue-900"
              >
                Apri Athlete 360 →
              </Link>
            </div>
          </div>
        )
      })}
    </div>
  )
}

