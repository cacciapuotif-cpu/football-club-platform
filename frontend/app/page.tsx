'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-blue-600 to-yellow-500">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm flex flex-col">
        <h1 className="text-6xl font-bold text-white mb-4 text-center">
          Football Club Platform
        </h1>
        <p className="text-2xl text-white/90 mb-4 text-center">
          Gestionale per Società di Calcio
        </p>
        <p className="text-lg text-white/80 mb-12 text-center max-w-2xl">
          Gestionale innovativo per società di calcio dilettantistiche.
          Monitoraggio atleti, analisi video, ML predittivo, piani personalizzati.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
            <h3 className="text-xl font-semibold text-white mb-2">⚽ Dashboard</h3>
            <p className="text-white/80">
              Monitoraggio carichi, KPI tecnici, rischio overload
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
            <h3 className="text-xl font-semibold text-white mb-2">🤖 ML Predittivo</h3>
            <p className="text-white/80">
              Performance attesa, explainability, drift monitoring
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
            <h3 className="text-xl font-semibold text-white mb-2">📊 Report PDF</h3>
            <p className="text-white/80">
              Report atleta, squadra, staff weekly automatici
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
            <h3 className="text-xl font-semibold text-white mb-2">📹 Video Analysis</h3>
            <p className="text-white/80">
              Tracking, heatmap, eventi, clip generator
            </p>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-4 items-center">
          <h2 className="text-2xl font-bold text-white mb-4">🎯 Accesso Rapido</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl">
            <Link
              href="/players/new"
              className="bg-green-500 text-white px-6 py-4 rounded-lg font-semibold hover:bg-green-600 transition-colors text-center shadow-lg"
            >
              ➕ Nuovo Giocatore
            </Link>

            <Link
              href="/sessions/new"
              className="bg-orange-500 text-white px-6 py-4 rounded-lg font-semibold hover:bg-orange-600 transition-colors text-center shadow-lg"
            >
              🏃 Nuova Sessione
            </Link>

            <Link
              href="/wellness/new"
              className="bg-purple-500 text-white px-6 py-4 rounded-lg font-semibold hover:bg-purple-600 transition-colors text-center shadow-lg"
            >
              💪 Dati Wellness
            </Link>
          </div>

          <div className="mt-8">
            <Link
              href="/players"
              className="bg-blue-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-600 transition-colors shadow-lg"
            >
              📋 Vedi Lista Giocatori
            </Link>
          </div>

          <div className="mt-4">
            <a
              href="http://localhost:8101/docs"
              target="_blank"
              className="bg-white text-blue-600 px-6 py-2 rounded-lg font-medium hover:bg-blue-50 transition-colors text-sm"
            >
              📚 API Documentation →
            </a>
          </div>
        </div>
      </div>
    </main>
  );
}
