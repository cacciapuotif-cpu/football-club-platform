'use client';

/**
 * PlayerStatusBadge - Visual indicator (green/orange/red) for player status based on alerts.
 */

import { useEffect, useState } from 'react';
import { getPlayerAlerts } from '@/lib/api/alerts';
import type { PlayerAlert } from '@/types/alerts';
import { AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react';

type PlayerStatusBadgeProps = {
  playerId: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
};

export default function PlayerStatusBadge({
  playerId,
  size = 'md',
  showLabel = true,
}: PlayerStatusBadgeProps) {
  const [status, setStatus] = useState<'loading' | 'ok' | 'warning' | 'critical'>('loading');
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    fetchStatus();
  }, [playerId]);

  async function fetchStatus() {
    try {
      const data = await getPlayerAlerts(playerId, 1); // Only check today
      const unresolvedAlerts = data.alerts.filter(a => !a.resolved);

      if (unresolvedAlerts.length === 0) {
        setStatus('ok');
        setAlertCount(0);
      } else {
        const hasCritical = unresolvedAlerts.some(a => a.level === 'critical');
        const hasWarning = unresolvedAlerts.some(a => a.level === 'warning');

        if (hasCritical) {
          setStatus('critical');
        } else if (hasWarning) {
          setStatus('warning');
        } else {
          setStatus('ok');
        }

        setAlertCount(unresolvedAlerts.length);
      }
    } catch (err) {
      console.error('Error fetching player status:', err);
      setStatus('ok'); // Default to ok if error
    }
  }

  if (status === 'loading') {
    return (
      <div className="animate-pulse bg-gray-200 rounded-full h-6 w-20"></div>
    );
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-2',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  const config = {
    ok: {
      color: 'bg-green-100 text-green-800 border-green-300',
      icon: <CheckCircle className={iconSizes[size]} />,
      label: 'OK',
    },
    warning: {
      color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      icon: <AlertTriangle className={iconSizes[size]} />,
      label: 'Attenzione',
    },
    critical: {
      color: 'bg-red-100 text-red-800 border-red-300',
      icon: <AlertCircle className={iconSizes[size]} />,
      label: 'Critico',
    },
  };

  const currentConfig = config[status];

  return (
    <div
      className={`inline-flex items-center space-x-1.5 rounded-full border font-medium ${currentConfig.color} ${sizeClasses[size]}`}
      title={alertCount > 0 ? `${alertCount} alert attivi` : 'Nessun alert'}
    >
      {currentConfig.icon}
      {showLabel && (
        <span>
          {currentConfig.label}
          {alertCount > 0 && ` (${alertCount})`}
        </span>
      )}
    </div>
  );
}
