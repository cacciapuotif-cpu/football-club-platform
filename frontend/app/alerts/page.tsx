'use client';

/**
 * Alerts Dashboard Page - Staff view of all today's alerts.
 */

import AlertsDashboard from '@/components/alerts/AlertsDashboard';

export default function AlertsPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">Alert e Notifiche</h1>
        <p className="text-gray-600">
          Monitora gli alert di oggi per tutti i giocatori. Gli alert vengono generati automaticamente in base ai parametri di carico e recupero.
        </p>
      </div>

      <AlertsDashboard />
    </div>
  );
}
