'use client'

import { use } from 'react'
import Link from 'next/link'
import PlayerWeeklyLoadChart from '@/components/training/PlayerWeeklyLoadChart'
import RpeQuickAdd from '@/components/training/RpeQuickAdd'

export default function PlayerLoadPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)

  const handleRpeSaved = () => {
    // Force chart to reload by remounting it
    // This is a simple approach - you could also use a key prop
    window.location.reload()
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header with back link */}
      <div className="mb-6">
        <Link
          href={`/players/${id}`}
          className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
        >
          <svg
            className="w-5 h-5 mr-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          Torna al profilo
        </Link>
        <h1 className="text-3xl font-bold text-gray-800">Carico allenamento</h1>
        <p className="text-gray-600 mt-2">Monitoraggio RPE e carico settimanale</p>
      </div>

      {/* RPE Quick Add Form */}
      <div className="mb-8">
        <RpeQuickAdd playerId={id} onSuccess={handleRpeSaved} />
      </div>

      {/* Weekly Load Chart */}
      <div className="mb-8">
        <PlayerWeeklyLoadChart playerId={id} weeks={8} />
      </div>

      {/* Info box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">💡 Cos'è l'RPE?</h3>
        <p className="text-sm text-blue-800">
          <strong>RPE (Rate of Perceived Exertion)</strong> è una scala da 0 a 10 che indica l'intensità percepita dell'allenamento dal giocatore.
        </p>
        <ul className="mt-2 text-sm text-blue-800 space-y-1 ml-4">
          <li>• <strong>0-2:</strong> Molto leggero</li>
          <li>• <strong>3-4:</strong> Leggero</li>
          <li>• <strong>5-6:</strong> Moderato</li>
          <li>• <strong>7-8:</strong> Intenso</li>
          <li>• <strong>9-10:</strong> Massimo sforzo</li>
        </ul>
        <p className="mt-3 text-sm text-blue-800">
          <strong>Carico sessione</strong> = RPE × Durata (minuti)
        </p>
        <p className="text-sm text-blue-800">
          <strong>Carico settimanale</strong> = Somma dei carichi di tutte le sessioni della settimana
        </p>
      </div>
    </div>
  )
}
