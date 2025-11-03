'use client'

import { useState, useEffect } from 'react'
import WellnessTable from '@/components/wellness/WellnessTable'
import WellnessPlayerDrawer from '@/components/wellness/WellnessPlayerDrawer'
import { getWellnessSummary, getPlayerWellnessEntries } from '@/lib/api/wellness'
import type { WellnessSummary, WellnessEntry } from '@/types/wellness'

export default function WellnessPage() {
  // State for table data
  const [data, setData] = useState<WellnessSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // State for filters
  const [fromDate, setFromDate] = useState<string>('')
  const [toDate, setToDate] = useState<string>('')
  const [roleFilter, setRoleFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [currentSort, setCurrentSort] = useState<string>('cognome_asc')

  // State for drawer
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedPlayer, setSelectedPlayer] = useState<WellnessSummary | null>(null)
  const [playerEntries, setPlayerEntries] = useState<WellnessEntry[]>([])
  const [loadingEntries, setLoadingEntries] = useState(false)

  // Fetch wellness summary data
  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      const params: any = {
        sort: currentSort,
        page: 1,
        page_size: 100,
      }

      if (fromDate) params.from = fromDate
      if (toDate) params.to = toDate
      if (roleFilter) params.role = roleFilter
      if (searchQuery) params.search = searchQuery

      const result = await getWellnessSummary(params)
      setData(result)
    } catch (err) {
      console.error('Error fetching wellness summary:', err)
      setError(err instanceof Error ? err.message : 'Errore nel caricamento dei dati')
    } finally {
      setLoading(false)
    }
  }

  // Fetch data on mount and when filters change
  useEffect(() => {
    fetchData()
  }, [fromDate, toDate, roleFilter, searchQuery, currentSort])

  // Handle row click - open drawer
  const handleRowClick = async (playerId: string) => {
    const player = data.find((p) => p.player_id === playerId)
    if (!player) return

    setSelectedPlayer(player)
    setDrawerOpen(true)
    setLoadingEntries(true)

    try {
      const params: any = {}
      if (fromDate) params.from = fromDate
      if (toDate) params.to = toDate

      const entries = await getPlayerWellnessEntries(playerId, params)
      setPlayerEntries(entries)
    } catch (err) {
      console.error('Error fetching player entries:', err)
      setPlayerEntries([])
    } finally {
      setLoadingEntries(false)
    }
  }

  // Handle drawer close
  const handleDrawerClose = () => {
    setDrawerOpen(false)
    setSelectedPlayer(null)
    setPlayerEntries([])
  }

  // Reset filters
  const handleResetFilters = () => {
    setFromDate('')
    setToDate('')
    setRoleFilter('')
    setSearchQuery('')
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Sessioni Wellness</h1>
        <p className="text-gray-600">Monitora lo stato di benessere dei giocatori</p>
      </div>

      {/* Error message */}
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

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Date from */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data inizio
            </label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Date to */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data fine
            </label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Role filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ruolo
            </label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tutti i ruoli</option>
              <option value="GK">Portiere (GK)</option>
              <option value="DF">Difensore (DF)</option>
              <option value="MF">Centrocampista (MF)</option>
              <option value="FW">Attaccante (FW)</option>
            </select>
          </div>

          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cerca giocatore
            </label>
            <input
              type="text"
              placeholder="Nome o cognome..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Reset button */}
        {(fromDate || toDate || roleFilter || searchQuery) && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleResetFilters}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 underline"
            >
              Azzera filtri
            </button>
          </div>
        )}
      </div>

      {/* Stats summary */}
      {!loading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <svg
                className="h-5 w-5 text-blue-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="text-sm text-blue-800">
                <strong>{data.length}</strong> giocator{data.length === 1 ? 'e' : 'i'} trovat{data.length === 1 ? 'o' : 'i'}
                {(fromDate || toDate) && ' nel periodo selezionato'}
              </span>
            </div>
            <span className="text-xs text-blue-600">
              Clicca su un giocatore per vedere i dettagli
            </span>
          </div>
        </div>
      )}

      {/* Wellness Table */}
      <WellnessTable
        data={data}
        loading={loading}
        onRowClick={handleRowClick}
        onSort={setCurrentSort}
        currentSort={currentSort}
      />

      {/* Player Drawer */}
      {selectedPlayer && (
        <WellnessPlayerDrawer
          isOpen={drawerOpen}
          onClose={handleDrawerClose}
          playerName={selectedPlayer.nome}
          playerSurname={selectedPlayer.cognome}
          playerId={selectedPlayer.player_id}
          entries={playerEntries}
          loading={loadingEntries}
        />
      )}
    </div>
  )
}
