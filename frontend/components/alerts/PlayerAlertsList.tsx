'use client';

/**
 * PlayerAlertsList - Display alerts for a specific player with resolve action.
 */

import { useEffect, useState } from 'react';
import { getPlayerAlerts, resolveAlert } from '@/lib/api/alerts';
import type { PlayerAlert } from '@/types/alerts';
import { AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react';

type PlayerAlertsListProps = {
  playerId: string;
  days?: number;
};

export default function PlayerAlertsList({ playerId, days = 14 }: PlayerAlertsListProps) {
  const [alerts, setAlerts] = useState<PlayerAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAlerts();
  }, [playerId, days]);

  async function fetchAlerts() {
    try {
      setLoading(true);
      setError(null);
      const data = await getPlayerAlerts(playerId, days);
      setAlerts(data.alerts);
    } catch (err) {
      setError('Errore nel caricamento degli alert');
      console.error('Error fetching player alerts:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleResolve(alertId: string) {
    try {
      await resolveAlert(alertId);
      // Update local state
      setAlerts(prev => prev.map(a =>
        a.id === alertId ? { ...a, resolved: true } : a
      ));
    } catch (err) {
      console.error('Error resolving alert:', err);
      alert('Errore nella risoluzione dell\'alert');
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-2">
        <div className="h-20 bg-gray-200 rounded"></div>
        <div className="h-20 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
        {error}
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="p-6 bg-green-50 border border-green-200 rounded-lg text-center">
        <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-2" />
        <p className="text-green-800 font-medium">Nessun alert attivo</p>
        <p className="text-green-600 text-sm mt-1">Il giocatore è in ottimo stato</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map(alert => (
        <AlertCard
          key={alert.id}
          alert={alert}
          onResolve={handleResolve}
        />
      ))}
    </div>
  );
}

function AlertCard({ alert, onResolve }: { alert: PlayerAlert; onResolve: (id: string) => void }) {
  const { level, message, date, resolved } = alert;

  const levelConfig = {
    critical: {
      bgColor: 'bg-red-50 border-red-300',
      textColor: 'text-red-900',
      icon: <AlertCircle className="w-5 h-5 text-red-600" />,
      badge: 'Critico',
      badgeColor: 'bg-red-600 text-white',
    },
    warning: {
      bgColor: 'bg-yellow-50 border-yellow-300',
      textColor: 'text-yellow-900',
      icon: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
      badge: 'Attenzione',
      badgeColor: 'bg-yellow-600 text-white',
    },
    info: {
      bgColor: 'bg-blue-50 border-blue-300',
      textColor: 'text-blue-900',
      icon: <Info className="w-5 h-5 text-blue-600" />,
      badge: 'Info',
      badgeColor: 'bg-blue-600 text-white',
    },
  };

  const config = levelConfig[level];

  return (
    <div className={`p-4 border rounded-lg ${config.bgColor} ${resolved ? 'opacity-50' : ''}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          {config.icon}
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${config.badgeColor}`}>
                {config.badge}
              </span>
              <span className="text-sm text-gray-500">
                {new Date(date).toLocaleDateString('it-IT')}
              </span>
              {resolved && (
                <span className="px-2 py-0.5 rounded text-xs bg-gray-300 text-gray-700">
                  Risolto
                </span>
              )}
            </div>
            <p className={`text-sm ${config.textColor}`}>{message}</p>
          </div>
        </div>
        {!resolved && (
          <button
            onClick={() => onResolve(alert.id)}
            className="ml-4 px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition"
          >
            Risolvi
          </button>
        )}
      </div>
    </div>
  );
}
