/**
 * Football Club Platform - k6 Smoke Test
 *
 * Validates DEMO_10x10 requirements:
 * - Health endpoints functional
 * - 10 players present
 * - Each player has ≥10 training sessions
 * - Each player has 7-day predictions
 * - Each player has ≥1 prescription
 *
 * SLO/Thresholds:
 * - Error rate < 1%
 * - P95 latency < 500ms
 * - Checks pass rate > 99%
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';

// ============================================================================
// Configuration
// ============================================================================

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS || 5),
      duration: __ENV.DURATION || '30s',
      tags: { scenario: 'smoke' },
    },
  },
  thresholds: {
    // SLO: Error rate < 1%
    http_req_failed: ['rate<0.01'],

    // SLO: P95 < 500ms
    'http_req_duration{scenario:smoke}': ['p(95)<500'],

    // SLO: Checks pass > 99%
    checks: ['rate>0.99'],
  },
};

// Environment variables with fallbacks
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000/api/v1';
const HEALTH_URL = __ENV.HEALTH_URL || 'http://localhost:8000/healthz';
const READY_URL = __ENV.READY_URL || 'http://localhost:8000/readyz';

// ============================================================================
// Test Execution
// ============================================================================

export default function () {
  // -------------------------------------------------------------------------
  // 1. Health Checks
  // -------------------------------------------------------------------------
  group('health', () => {
    const healthz = http.get(HEALTH_URL);
    check(healthz, {
      'healthz returns 200': (r) => r.status === 200,
      'healthz has status ok': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.status === 'ok';
        } catch {
          return false;
        }
      },
    });

    const readyz = http.get(READY_URL);
    check(readyz, {
      'readyz returns 200': (r) => r.status === 200,
      'readyz has status ready': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.status === 'ready';
        } catch {
          return false;
        }
      },
    });
  });

  // -------------------------------------------------------------------------
  // 2. Players Endpoint
  // -------------------------------------------------------------------------
  group('players', () => {
    const playersRes = http.get(`${BASE_URL}/players`);

    const playersChecks = check(playersRes, {
      'GET /players returns 200': (r) => r.status === 200,
      'players list is not empty': (r) => {
        try {
          const players = JSON.parse(r.body);
          return Array.isArray(players) && players.length > 0;
        } catch {
          return false;
        }
      },
      'players list has 10 players (DEMO_10x10)': (r) => {
        try {
          const players = JSON.parse(r.body);
          return players.length === 10;
        } catch {
          return false;
        }
      },
    });

    if (!playersChecks) {
      return; // Skip further tests if players endpoint fails
    }

    // Parse players for session checks
    let players = [];
    try {
      players = JSON.parse(playersRes.body);
    } catch (e) {
      console.error('Failed to parse players response:', e);
      return;
    }

    // Test first 5 players in detail (to keep load reasonable)
    const testPlayers = players.slice(0, 5);

    testPlayers.forEach((player) => {
      const playerId = player.id;
      const playerName = `${player.first_name} ${player.last_name}`;

      // Check training sessions
      const sessionsRes = http.get(
        `${BASE_URL}/sessions?type=training&player_id=${playerId}`
      );

      check(sessionsRes, {
        [`sessions for ${playerName} returns 200`]: (r) => r.status === 200,
        [`sessions for ${playerName} ≥10 (DEMO_10x10)`]: (r) => {
          try {
            const sessions = JSON.parse(r.body);
            const count = Array.isArray(sessions) ? sessions.length : 0;
            return count >= 10;
          } catch {
            return false;
          }
        },
      });

      // Check predictions (7-day horizon)
      const predictionsRes = http.get(
        `${BASE_URL}/predictions/${playerId}?horizon=7`
      );

      check(predictionsRes, {
        [`predictions for ${playerName} returns 200`]: (r) => r.status === 200,
        [`predictions for ${playerName} exists`]: (r) => {
          try {
            const pred = JSON.parse(r.body);
            return pred !== null && Object.keys(pred).length > 0;
          } catch {
            return false;
          }
        },
      });

      // Check prescriptions
      const prescriptionsRes = http.get(
        `${BASE_URL}/prescriptions/${playerId}`
      );

      check(prescriptionsRes, {
        [`prescriptions for ${playerName} returns 200`]: (r) => r.status === 200,
        [`prescriptions for ${playerName} ≥1 (DEMO_10x10)`]: (r) => {
          try {
            const presc = JSON.parse(r.body);
            const count = Array.isArray(presc) ? presc.length : (presc ? 1 : 0);
            return count >= 1;
          } catch {
            return false;
          }
        },
      });
    });
  });

  // Small delay between iterations to avoid hammering the API
  sleep(0.5);
}

// ============================================================================
// Lifecycle Hooks
// ============================================================================

export function handleSummary(data) {
  console.log('\n========================================');
  console.log('k6 SMOKE TEST SUMMARY');
  console.log('========================================');
  console.log(`Total Requests: ${data.metrics.http_reqs.values.count}`);
  console.log(`Failed Requests: ${data.metrics.http_req_failed.values.rate * 100}%`);
  console.log(`P95 Duration: ${data.metrics.http_req_duration.values['p(95)']}ms`);
  console.log(`Checks Passed: ${data.metrics.checks.values.rate * 100}%`);
  console.log('========================================\n');

  return {
    'stdout': '', // Suppress default summary (we printed our own above)
  };
}
