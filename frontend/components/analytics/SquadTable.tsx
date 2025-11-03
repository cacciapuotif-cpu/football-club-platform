"use client";

import React, { useEffect, useState } from "react";

type SquadRow = {
  player_id: string;
  name?: string;
  role?: string;
  avg_xg: number;
  avg_key_passes: number;
  avg_duels_won: number;
};

interface SquadTableProps {
  apiUrl?: string;
}

export default function SquadTable({
  apiUrl = "http://localhost:8000",
}: SquadTableProps) {
  const [rows, setRows] = useState<SquadRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);

        // Fetch players list
        const playersResponse = await fetch(`${apiUrl}/api/v1/players`);
        if (!playersResponse.ok) {
          throw new Error(`HTTP ${playersResponse.status} fetching players`);
        }

        const players = await playersResponse.json();
        const out: SquadRow[] = [];

        // Fetch summary for each player (limit to first 20 for performance)
        const playersToFetch = players.slice(0, 20);

        for (const p of playersToFetch) {
          try {
            const summaryResponse = await fetch(
              `${apiUrl}/api/v1/advanced-analytics/ml/player/${p.id}/summary`
            );

            if (!summaryResponse.ok) {
              console.warn(`Failed to fetch summary for player ${p.id}`);
              continue;
            }

            const json = await summaryResponse.json();

            out.push({
              player_id: p.id,
              name: `${p.first_name || ""} ${p.last_name || ""}`.trim() || p.id,
              role: p.role_primary || "-",
              avg_xg: json.avg_xg || 0,
              avg_key_passes: json.avg_key_passes || 0,
              avg_duels_won: json.avg_duels_won || 0,
            });
          } catch (err) {
            console.error(`Error fetching data for player ${p.id}:`, err);
          }
        }

        setRows(out);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch squad table data:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    })();
  }, [apiUrl]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-gray-500">Loading squad data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-gray-500">No players found</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border border-gray-300 divide-y divide-gray-300">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-r">
              Player
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-r">
              Role
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider border-r">
              Avg xG
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider border-r">
              Key Passes
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider">
              Duels Won
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {rows.map((r) => (
            <tr key={r.player_id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-sm text-gray-900 border-r">{r.name || r.player_id}</td>
              <td className="px-4 py-3 text-sm text-gray-600 border-r">{r.role || "-"}</td>
              <td className="px-4 py-3 text-sm text-center text-gray-900 border-r">
                {r.avg_xg.toFixed(2)}
              </td>
              <td className="px-4 py-3 text-sm text-center text-gray-900 border-r">
                {r.avg_key_passes.toFixed(1)}
              </td>
              <td className="px-4 py-3 text-sm text-center text-gray-900">
                {r.avg_duels_won.toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
