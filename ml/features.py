"""
Feature engineering for ML models.
Extracts features from player data for performance prediction and overload risk.
"""

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd


class FeatureEngineer:
    """Feature engineering for player performance prediction."""

    def __init__(self, lookback_weeks: int = 4):
        """
        Initialize feature engineer.

        Args:
            lookback_weeks: Number of weeks to look back for features
        """
        self.lookback_weeks = lookback_weeks

    def extract_features(self, player_data: dict[str, Any]) -> dict[str, float]:
        """
        Extract features from player data.

        Args:
            player_data: Dictionary with player metrics, wellness, tests, etc.

        Returns:
            Dictionary of features for ML model
        """
        features = {}

        # Load metrics
        df = self._prepare_dataframe(player_data)

        # Training load features
        features.update(self._load_features(df))

        # Wellness features
        features.update(self._wellness_features(df))

        # Performance features
        features.update(self._performance_features(df))

        # Injury history features
        features.update(self._injury_features(player_data))

        # Demographic features
        features.update(self._demographic_features(player_data))

        return features

    def _prepare_dataframe(self, player_data: dict[str, Any]) -> pd.DataFrame:
        """Prepare pandas DataFrame from player data."""
        # Combine sensor data, wellness, tests
        records = []

        # Sensor data (training loads)
        for item in player_data.get("sensor_data", []):
            records.append(
                {
                    "date": item["timestamp"],
                    "distance_km": item.get("distance_km", 0),
                    "hi_runs": item.get("hi_runs", 0),
                    "sprint_count": item.get("sprint_count", 0),
                    "player_load": item.get("player_load", 0),
                }
            )

        # Wellness data
        for item in player_data.get("wellness_data", []):
            records.append(
                {
                    "date": item["date"],
                    "hrv_ms": item.get("hrv_ms"),
                    "sleep_hours": item.get("sleep_hours"),
                    "sleep_quality": item.get("sleep_quality"),
                    "fatigue_rating": item.get("fatigue_rating"),
                    "stress_rating": item.get("stress_rating"),
                    "mood_rating": item.get("mood_rating"),
                    "srpe": item.get("srpe"),
                }
            )

        df = pd.DataFrame(records)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

        return df

    def _load_features(self, df: pd.DataFrame) -> dict[str, float]:
        """Extract training load features."""
        features = {}

        if df.empty:
            return {f"load_{k}": 0.0 for k in ["acwr", "monotony", "strain", "avg_km", "trend"]}

        # ACWR (Acute:Chronic Workload Ratio)
        # Acute = last 7 days average, Chronic = last 28 days average
        last_7d = df[df["date"] >= df["date"].max() - timedelta(days=7)]
        last_28d = df[df["date"] >= df["date"].max() - timedelta(days=28)]

        acute_load = last_7d["player_load"].mean() if not last_7d.empty else 0
        chronic_load = last_28d["player_load"].mean() if not last_28d.empty else 0

        features["load_acwr"] = acute_load / chronic_load if chronic_load > 0 else 1.0

        # Training monotony and strain
        if not last_7d.empty and len(last_7d) > 1:
            mean_load = last_7d["player_load"].mean()
            std_load = last_7d["player_load"].std()
            features["load_monotony"] = mean_load / std_load if std_load > 0 else 0
            features["load_strain"] = mean_load * features["load_monotony"]
        else:
            features["load_monotony"] = 0.0
            features["load_strain"] = 0.0

        # Average distance
        features["load_avg_km"] = last_7d["distance_km"].mean() if not last_7d.empty else 0.0

        # Load trend (slope of last 4 weeks)
        if len(df) > 7:
            weekly_loads = df.set_index("date")["player_load"].resample("W").sum()
            if len(weekly_loads) >= 2:
                x = np.arange(len(weekly_loads))
                y = weekly_loads.values
                features["load_trend"] = np.polyfit(x, y, 1)[0]
            else:
                features["load_trend"] = 0.0
        else:
            features["load_trend"] = 0.0

        return features

    def _wellness_features(self, df: pd.DataFrame) -> dict[str, float]:
        """Extract wellness and recovery features."""
        features = {}

        if df.empty:
            return {f"wellness_{k}": 0.0 for k in ["hrv_avg", "hrv_trend", "sleep_avg", "fatigue_avg", "stress_avg"]}

        last_7d = df[df["date"] >= df["date"].max() - timedelta(days=7)]

        # HRV average and trend
        if "hrv_ms" in df.columns:
            hrv_data = last_7d["hrv_ms"].dropna()
            features["wellness_hrv_avg"] = hrv_data.mean() if not hrv_data.empty else 0.0

            # HRV trend
            if len(hrv_data) >= 2:
                features["wellness_hrv_trend"] = (hrv_data.iloc[-1] - hrv_data.iloc[0]) / hrv_data.iloc[0] if hrv_data.iloc[0] > 0 else 0
            else:
                features["wellness_hrv_trend"] = 0.0
        else:
            features["wellness_hrv_avg"] = 0.0
            features["wellness_hrv_trend"] = 0.0

        # Sleep
        if "sleep_hours" in df.columns:
            features["wellness_sleep_avg"] = last_7d["sleep_hours"].mean() if not last_7d.empty else 0.0
        else:
            features["wellness_sleep_avg"] = 0.0

        # Fatigue and stress
        features["wellness_fatigue_avg"] = last_7d["fatigue_rating"].mean() if "fatigue_rating" in df.columns and not last_7d.empty else 0.0
        features["wellness_stress_avg"] = last_7d["stress_rating"].mean() if "stress_rating" in df.columns and not last_7d.empty else 0.0

        return features

    def _performance_features(self, df: pd.DataFrame) -> dict[str, float]:
        """Extract performance features."""
        features = {}

        # sRPE average
        if not df.empty and "srpe" in df.columns:
            last_7d = df[df["date"] >= df["date"].max() - timedelta(days=7)]
            features["perf_srpe_avg"] = last_7d["srpe"].mean() if not last_7d.empty else 0.0
        else:
            features["perf_srpe_avg"] = 0.0

        return features

    def _injury_features(self, player_data: dict[str, Any]) -> dict[str, float]:
        """Extract injury history features."""
        injuries = player_data.get("injuries", [])

        features = {
            "injury_count_6m": 0,
            "injury_days_out_total": 0,
            "injury_recurrence_count": 0,
        }

        if injuries:
            six_months_ago = datetime.now() - timedelta(days=180)
            recent_injuries = [inj for inj in injuries if inj.get("injury_date") and pd.to_datetime(inj["injury_date"]) >= six_months_ago]

            features["injury_count_6m"] = len(recent_injuries)
            features["injury_days_out_total"] = sum(inj.get("days_out", 0) for inj in recent_injuries)
            features["injury_recurrence_count"] = sum(1 for inj in recent_injuries if inj.get("is_recurrence"))

        return features

    def _demographic_features(self, player_data: dict[str, Any]) -> dict[str, float]:
        """Extract demographic features."""
        player = player_data.get("player", {})

        # Age
        if player.get("date_of_birth"):
            dob = pd.to_datetime(player["date_of_birth"])
            age = (datetime.now() - dob).days / 365.25
        else:
            age = 25.0  # Default

        # Role encoding
        role_map = {"GK": 0, "DF": 1, "MF": 2, "FW": 3}
        role = player.get("role_primary", "MF")
        role_encoded = role_map.get(role, 2)

        return {"demo_age": age, "demo_role": role_encoded}

    def get_feature_names(self) -> list[str]:
        """Get list of feature names."""
        return [
            # Load features
            "load_acwr",
            "load_monotony",
            "load_strain",
            "load_avg_km",
            "load_trend",
            # Wellness features
            "wellness_hrv_avg",
            "wellness_hrv_trend",
            "wellness_sleep_avg",
            "wellness_fatigue_avg",
            "wellness_stress_avg",
            # Performance features
            "perf_srpe_avg",
            # Injury features
            "injury_count_6m",
            "injury_days_out_total",
            "injury_recurrence_count",
            # Demographic features
            "demo_age",
            "demo_role",
        ]
