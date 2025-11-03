/**
 * Types for player metrics (ACWR, Monotony, Strain, Readiness)
 */

export type MetricDaily = {
  date: string;
  acwr: number | null;
  monotony: number | null;
  strain: number | null;
  readiness: number | null;
};

export type PlayerMetricsSummary = {
  player_id: string;
  metrics: MetricDaily[];
};

export type PlayerMetricsLatest = {
  player_id: string;
  date: string;
  acwr: number | null;
  monotony: number | null;
  strain: number | null;
  readiness: number | null;
};
