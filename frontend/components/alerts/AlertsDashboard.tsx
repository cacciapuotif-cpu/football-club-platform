'use client';

/**
 * AlertsDashboard - Staff view of all today's alerts with filtering and sorting.
 */

import { useEffect, useState } from 'react';
import { getTodayAlerts, resolveAlert } from '@/lib/api/alerts';
import type { TodayAlert } from '@/types/alerts';
import { AlertCircle, AlertTriangle, Info, Filter } from 'lucide-react';
import Link from 'next/link';

type FilterLevel = 'all' | 'critical' | 'warning' | 'info';

export default function AlertsDashboard() {
  const [alerts, setAlerts] = useState<TodayAlert[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<TodayAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterLevel>('all');
  const [showResolved, setShowResolved] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, [showResolved]);

  useEffect(() => {
    // Apply filter
    if (filter === 'all') {
      setFilteredAlerts(alerts);
    } else {
      setFilteredAlerts(alerts.filter(a => a.level === filter));
    }
  }, [filter, alerts]);

  async function fetchAlerts() {
    try {
      setLoading(true);
      setError(null);
      const data = await getTodayAlerts(showResolved);
      setAlerts(data.alerts);
    } catch (err) {
      setError('Errore nel caricamento degli alert');
      console.error('Error fetching today alerts:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleResolve(alertId: string) {
    try {
      await resolveAlert(alertId);
      // Refresh alerts
      await fetchAlerts();
    } catch (err) {
      console.error('Error resolving alert:', err);
      alert('Errore nella risoluzione dell\'alert');
    }
  }

  const stats = {
    total: alerts.length,
    critical: alerts.filter(a => a.level === 'critical' && !a.resolved).length,
    warning: alerts.filter(a => a.level === 'warning' && !a.resolved).length,
    info: alerts.filter(a => a.level === 'info' && !a.resolved).length,
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-24 bg-gray-200 rounded"></div>
        <div className="h-32 bg-gray-200 rounded"></div>
        <div className="h-32 bg-gray-200 rounded"></div>
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

  return (
    <div className="space-y-6">
      {/* Stats Summary */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Totale Alert"
          value={stats.total}
          color="bg-gray-100 text-gray-800"
          active={filter === 'all'}
          onClick={() => setFilter('all')}
        />
        <StatCard
          label="Critici"
          value={stats.critical}
          color="bg-red-100 text-red-800"
          active={filter === 'critical'}
          onClick={() => setFilter('critical')}
        />
        <StatCard
          label="Attenzione"
          value={stats.warning}
          color="bg-yellow-100 text-yellow-800"
          active={filter === 'warning'}
          onClick={() => setFilter('warning')}
        />
        <StatCard
          label="Info"
          value={stats.info}
          color="bg-blue-100 text-blue-800"
          active={filter === 'info'}
          onClick={() => setFilter('info')}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Filter className="w-5 h-5 text-gray-500" />
          <span className="text-sm text-gray-600">
            Mostrando {filteredAlerts.length} di {alerts.length} alert
          </span>
        </div>
        <label className="flex items-center space-x-2 text-sm">
          <input
            type="checkbox"
            checked={showResolved}
            onChange={(e) => setShowResolved(e.target.checked)}
            className="rounded"
          />
          <span>Mostra risolti</span>
        </label>
      </div>

      {/* Alerts List */}
      {filteredAlerts.length === 0 ? (
        <div className="p-8 bg-green-50 border border-green-200 rounded-lg text-center">
          <p className="text-green-800 font-medium">Nessun alert da mostrare</p>
          <p className="text-green-600 text-sm mt-1">
            {filter !== 'all' ? 'Prova a cambiare il filtro' : 'Tutti i giocatori sono in ottimo stato!'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map(alert => (
            <StaffAlertCard
              key={alert.id}
              alert={alert}
              onResolve={handleResolve}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
  active,
  onClick,
}: {
  label: string;
  value: number;
  color: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`p-4 rounded-lg transition cursor-pointer ${color} ${
        active ? 'ring-2 ring-blue-500' : 'hover:opacity-80'
      }`}
    >
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-sm mt-1">{label}</div>
    </button>
  );
}

function StaffAlertCard({
  alert,
  onResolve,
}: {
  alert: TodayAlert;
  onResolve: (id: string) => void;
}) {
  const { level, message, resolved, player_name, jersey_number, role, player_id } = alert;

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
            <div className="flex items-center space-x-2 mb-2">
              <Link
                href={`/players/${player_id}`}
                className="font-semibold text-blue-600 hover:underline"
              >
                {player_name}
              </Link>
              {jersey_number && (
                <span className="px-2 py-0.5 rounded bg-gray-200 text-xs font-mono">
                  #{jersey_number}
                </span>
              )}
              <span className="text-sm text-gray-500">{role}</span>
              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${config.badgeColor}`}>
                {config.badge}
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
