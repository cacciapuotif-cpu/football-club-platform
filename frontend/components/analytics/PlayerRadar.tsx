"use client";

import React, { useEffect, useState } from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

type RadarDatum = { metric: string; value: number; fullMark: number };

interface PlayerRadarProps {
  playerId: string;
  apiUrl?: string;
}

export default function PlayerRadar({
  playerId,
  apiUrl = "http://localhost:8000",
}: PlayerRadarProps) {
  const [data, setData] = useState<RadarDatum[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `${apiUrl}/api/v1/advanced-analytics/ml/player/${playerId}/summary`
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const json = await response.json();

        const arr: RadarDatum[] = [
          {
            metric: "xG",
            value: parseFloat((json.avg_xg || 0).toFixed(2)),
            fullMark: 1,
          },
          {
            metric: "Key Passes",
            value: parseFloat((json.avg_key_passes || 0).toFixed(1)),
            fullMark: 5,
          },
          {
            metric: "Duels Won",
            value: parseFloat((json.avg_duels_won || 0).toFixed(1)),
            fullMark: 10,
          },
          {
            metric: "Form Trend",
            value: Math.max(0, (json.trend_form_last_10 || 0) + 0.5),
            fullMark: 1,
          },
        ];

        setData(arr);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch player radar data:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    })();
  }, [playerId, apiUrl]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-80">
        <p className="text-gray-500">Loading radar chart...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-80">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-80">
        <p className="text-gray-500">No data available</p>
      </div>
    );
  }

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="metric" />
          <PolarRadiusAxis angle={90} domain={[0, "dataMax"]} />
          <Radar
            name="Player Stats"
            dataKey="value"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.6}
          />
          <Legend />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
