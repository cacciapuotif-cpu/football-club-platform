'use client'

import Link from 'next/link'

export default function MLPredictivePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-4">ML Predittivo</h1>
        <p className="text-gray-600 text-lg mb-6">Funzionalità in lavorazione</p>
        <p className="text-gray-500">
          Questa sezione sarà presto disponibile per analisi predittive avanzate.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block text-blue-600 hover:text-blue-800"
        >
          ← Torna alla Home
        </Link>
      </div>
    </div>
  )
}

