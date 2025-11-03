'use client'

import { useEffect, useRef } from 'react'
import type { WellnessEntry } from '@/types/wellness'

interface WellnessPlayerDrawerProps {
  isOpen: boolean
  onClose: () => void
  playerName: string
  playerSurname: string
  playerId: string
  entries: WellnessEntry[]
  loading: boolean
}

export default function WellnessPlayerDrawer({
  isOpen,
  onClose,
  playerName,
  playerSurname,
  playerId,
  entries,
  loading,
}: WellnessPlayerDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  // Focus trap
  useEffect(() => {
    if (isOpen && closeButtonRef.current) {
      closeButtonRef.current.focus()
    }
  }, [isOpen])

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  const exportToCSV = () => {
    if (entries.length === 0) return

    const headers = [
      'Data',
      'Sonno (h)',
      'Qualità Sonno',
      'Fatica',
      'Stress',
      'Umore',
      'DOMS',
      'Peso (kg)',
      'Note',
    ]

    const csvContent = [
      headers.join(','),
      ...entries.map((entry) =>
        [
          entry.date,
          entry.sleep_h ?? '',
          entry.sleep_quality ?? '',
          entry.fatigue ?? '',
          entry.stress ?? '',
          entry.mood ?? '',
          entry.doms ?? '',
          entry.weight_kg ?? '',
          entry.notes ? `"${entry.notes.replace(/"/g, '""')}"` : '',
        ].join(',')
      ),
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `wellness_${playerSurname}_${playerName}_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const openPlayerProfile = () => {
    window.location.href = `/players/${playerId}`
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      ></div>

      {/* Drawer */}
      <div
        ref={drawerRef}
        className="fixed inset-y-0 right-0 max-w-2xl w-full bg-white shadow-xl z-50 transform transition-transform"
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 z-10">
          <div className="flex items-center justify-between">
            <h2 id="drawer-title" className="text-xl font-bold text-gray-900">
              Sessioni Wellness — {playerSurname} {playerName}
            </h2>
            <button
              ref={closeButtonRef}
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Chiudi drawer"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Action buttons */}
          <div className="flex space-x-3 mt-4">
            <button
              onClick={exportToCSV}
              disabled={entries.length === 0}
              className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              <span className="flex items-center justify-center space-x-2">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <span>Esporta CSV</span>
              </span>
            </button>
            <button
              onClick={openPlayerProfile}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <span className="flex items-center justify-center space-x-2">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
                <span>Profilo Giocatore</span>
              </span>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto h-[calc(100vh-180px)] px-6 py-4">
          {loading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse bg-gray-100 h-40 rounded-lg"></div>
              ))}
            </div>
          ) : entries.length === 0 ? (
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
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="mt-4 text-gray-500">Nessuna sessione wellness registrata</p>
            </div>
          ) : (
            <div className="space-y-4">
              {entries.map((entry, index) => (
                <div
                  key={index}
                  className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-blue-300 transition-colors"
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {formatDate(entry.date)}
                    </h3>
                    {entry.weight_kg && (
                      <span className="text-sm text-gray-600 bg-white px-2 py-1 rounded">
                        {entry.weight_kg} kg
                      </span>
                    )}
                  </div>

                  {/* Sleep */}
                  <div className="grid grid-cols-2 gap-4 mb-3">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Sonno</p>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">😴</span>
                        <span className="text-sm font-medium">
                          {entry.sleep_h !== null ? `${entry.sleep_h}h` : 'N/D'}
                        </span>
                        {entry.sleep_quality && (
                          <div className="flex">
                            {renderStars(entry.sleep_quality)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Ratings Grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <RatingItem
                      label="Fatica"
                      value={entry.fatigue}
                      icon="💪"
                      color="blue"
                    />
                    <RatingItem
                      label="Stress"
                      value={entry.stress}
                      icon="😰"
                      color="yellow"
                    />
                    <RatingItem
                      label="Umore"
                      value={entry.mood}
                      icon="😊"
                      color="green"
                    />
                    <RatingItem
                      label="DOMS"
                      value={entry.doms}
                      icon="🔥"
                      color="red"
                    />
                  </div>

                  {/* Notes */}
                  {entry.notes && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs text-gray-500 mb-1">Note</p>
                      <p className="text-sm text-gray-700 italic">"{entry.notes}"</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}

// Helper components

function RatingItem({
  label,
  value,
  icon,
  color,
}: {
  label: string
  value: number | null
  icon: string
  color: 'blue' | 'yellow' | 'green' | 'red'
}) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    green: 'bg-green-100 text-green-800',
    red: 'bg-red-100 text-red-800',
  }

  return (
    <div className="bg-white rounded p-2">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <div className="flex items-center justify-between">
        <span className="text-xl">{icon}</span>
        {value !== null ? (
          <span className={`text-xs font-semibold px-2 py-1 rounded ${colorClasses[color]}`}>
            {value}/5
          </span>
        ) : (
          <span className="text-xs text-gray-400">N/D</span>
        )}
      </div>
    </div>
  )
}

function renderStars(quality: number) {
  return [...Array(5)].map((_, i) => (
    <span key={i} className="text-yellow-400 text-xs">
      {i < quality ? '★' : '☆'}
    </span>
  ))
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('it-IT', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  }).format(date)
}
