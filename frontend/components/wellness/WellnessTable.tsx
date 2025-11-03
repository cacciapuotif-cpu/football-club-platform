'use client'

import { useState } from 'react'
import type { WellnessSummary } from '@/types/wellness'

interface WellnessTableProps {
  data: WellnessSummary[]
  loading: boolean
  onRowClick: (playerId: string) => void
  onSort: (sort: string) => void
  currentSort: string
}

export default function WellnessTable({
  data,
  loading,
  onRowClick,
  onSort,
  currentSort,
}: WellnessTableProps) {
  const getSortIcon = (column: string) => {
    if (currentSort === `${column}_asc`) return '↑'
    if (currentSort === `${column}_desc`) return '↓'
    return '↕'
  }

  const toggleSort = (column: string) => {
    const currentDirection = currentSort.includes('_asc') ? 'asc' : 'desc'
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc'

    if (currentSort.startsWith(column)) {
      onSort(`${column}_${newDirection}`)
    } else {
      onSort(`${column}_asc`)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="animate-pulse">
          <div className="h-12 bg-gray-200"></div>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-100 border-t border-gray-200"></div>
          ))}
        </div>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <div className="text-gray-400 text-lg">
          <svg
            className="mx-auto h-12 w-12 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p>Nessuna sessione wellness trovata nel periodo selezionato</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => toggleSort('cognome')}
            >
              <div className="flex items-center space-x-1">
                <span>Cognome</span>
                <span className="text-gray-400">{getSortIcon('cognome')}</span>
              </div>
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Nome
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Ruolo
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => toggleSort('sessions')}
            >
              <div className="flex items-center space-x-1">
                <span># Sessioni</span>
                <span className="text-gray-400">{getSortIcon('sessions')}</span>
              </div>
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => toggleSort('last_entry')}
            >
              <div className="flex items-center space-x-1">
                <span>Ultima Entry</span>
                <span className="text-gray-400">{getSortIcon('last_entry')}</span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((player) => (
            <tr
              key={player.player_id}
              onClick={() => onRowClick(player.player_id)}
              className="hover:bg-blue-50 cursor-pointer transition-colors"
              tabIndex={0}
              role="button"
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onRowClick(player.player_id)
                }
              }}
            >
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {player.cognome}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {player.nome}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <span
                  className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(
                    player.ruolo
                  )}`}
                >
                  {player.ruolo}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <span className="font-semibold">{player.wellness_sessions_count}</span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {player.last_entry_date
                  ? formatDate(player.last_entry_date)
                  : <span className="text-gray-400 italic">Mai</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function getRoleBadgeColor(role: string): string {
  switch (role) {
    case 'GK':
      return 'bg-yellow-100 text-yellow-800'
    case 'DF':
      return 'bg-blue-100 text-blue-800'
    case 'MF':
      return 'bg-green-100 text-green-800'
    case 'FW':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}
