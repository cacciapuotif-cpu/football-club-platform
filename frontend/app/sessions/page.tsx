'use client'

import Link from 'next/link'

export default function SessionsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-blue-50 border-l-4 border-blue-400 p-6 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <span className="text-blue-400 text-xl">ℹ️</span>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800 mb-2">
              Area Sessioni di Allenamento
            </h3>
            <p className="text-sm text-blue-700 mb-4">
              Le sessioni di allenamento sono ora gestite nell'area <strong>Dati Wellness</strong> per ogni giocatore.
              Naviga su un giocatore e clicca su "Vai ai dati" per visualizzare e gestire tutte le metriche, incluse le sessioni di allenamento.
            </p>
            <div className="mt-4">
              <Link
                href="/players"
                className="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Vai ai Giocatori →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
