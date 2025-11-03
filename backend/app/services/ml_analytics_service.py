"""ML Analytics service with sklearn models (sync DB, UUID support)."""

import os
from datetime import date
from typing import Tuple
import pandas as pd
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, r2_score
from joblib import dump, load

from app.db_sync import get_db_context
from app.models.analytics import (
    PlayerTrainingLoad,
    PlayerFeatureDaily,
    PlayerPrediction,
    PlayerMatchStat,
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "../../ml/models")
os.makedirs(MODELS_DIR, exist_ok=True)

INJURY_MODEL_PATH = os.path.join(MODELS_DIR, "injury_risk_logreg.joblib")
PERF_MODEL_PATH = os.path.join(MODELS_DIR, "performance_linreg.joblib")
MODEL_VERSION = "1.0.0"


def _fetch_training_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch training data for ML models."""
    with get_db_context() as db:
        # Injury dataset
        q1 = db.query(
            PlayerTrainingLoad.player_id,
            PlayerTrainingLoad.load_acute,
            PlayerTrainingLoad.load_chronic,
            PlayerTrainingLoad.monotony,
            PlayerTrainingLoad.strain,
            PlayerTrainingLoad.injury_history_flag,
        ).all()

        df_injury = pd.DataFrame(
            q1,
            columns=["player_id", "load_acute", "load_chronic", "monotony", "strain", "injury_hist"],
        )

        if df_injury.empty:
            df_injury = pd.DataFrame(
                columns=["player_id", "load_acute", "load_chronic", "monotony", "strain", "injury_hist"]
            )
        else:
            # Synthetic target
            df_injury["injury_risk_flag"] = (
                (df_injury["load_acute"] / (df_injury["load_chronic"].replace(0, 1))).fillna(0) > 1.5
            ).astype(int)
            df_injury.loc[df_injury["monotony"] > 2.0, "injury_risk_flag"] = 1
            df_injury.loc[df_injury["injury_hist"] == True, "injury_risk_flag"] = 1

        # Performance dataset
        q2 = db.query(
            PlayerFeatureDaily.player_id,
            PlayerFeatureDaily.rolling_7d_load,
            PlayerFeatureDaily.rolling_21d_load,
            PlayerFeatureDaily.form_score,
        ).all()

        df_perf = pd.DataFrame(q2, columns=["player_id", "r7", "r21", "form_score"])

        if df_perf.empty:
            df_perf = pd.DataFrame(columns=["player_id", "r7", "r21", "form_score"])
        elif df_perf["form_score"].isnull().all():
            # Estimate from match stats
            q3 = db.query(PlayerMatchStat.player_id, PlayerMatchStat.xg).all()
            df_xg = pd.DataFrame(q3, columns=["player_id", "xg"])
            if not df_xg.empty:
                xg_mean = df_xg.groupby("player_id")["xg"].mean().reset_index()
                df_perf = df_perf.merge(xg_mean, on="player_id", how="left")
                df_perf["form_score"] = df_perf["xg"].fillna(0)
                df_perf.drop(columns=["xg"], inplace=True)
            else:
                df_perf["form_score"] = 0.0

        return df_injury, df_perf


def train_all() -> dict:
    """Train all ML models."""
    df_injury, df_perf = _fetch_training_data()
    results = {}

    # Injury (LogisticRegression)
    if not df_injury.empty and df_injury["injury_risk_flag"].nunique() > 1:
        X_inj = df_injury[["load_acute", "load_chronic", "monotony", "strain"]].fillna(0)
        y_inj = df_injury["injury_risk_flag"].astype(int)
        Xtr, Xte, ytr, yte = train_test_split(X_inj, y_inj, test_size=0.2, random_state=42, stratify=y_inj)
        clf = LogisticRegression(max_iter=1000)
        clf.fit(Xtr, ytr)
        dump(clf, INJURY_MODEL_PATH)
        proba = clf.predict_proba(Xte)[:, 1]
        results["injury_auc"] = float(roc_auc_score(yte, proba))
    else:
        clf = LogisticRegression(max_iter=1)
        dump(clf, INJURY_MODEL_PATH)
        results["injury_auc"] = None

    # Performance (LinearRegression)
    if not df_perf.empty and df_perf["form_score"].notnull().sum() > 5:
        Xp = df_perf[["r7", "r21"]].fillna(0)
        yp = df_perf["form_score"].fillna(0)
        Xtr, Xte, ytr, yte = train_test_split(Xp, yp, test_size=0.2, random_state=42)
        reg = LinearRegression()
        reg.fit(Xtr, ytr)
        dump(reg, PERF_MODEL_PATH)
        yhat = reg.predict(Xte)
        results["perf_r2"] = float(r2_score(yte, yhat))
    else:
        reg = LinearRegression()
        dump(reg, PERF_MODEL_PATH)
        results["perf_r2"] = None

    results["model_version"] = MODEL_VERSION
    return results


def predict_for_player(player_id: str) -> dict:
    """Generate predictions for a single player (UUID as string)."""
    with get_db_context() as db:
        # Fetch recent features
        feat = (
            db.query(PlayerFeatureDaily)
            .filter(PlayerFeatureDaily.player_id == player_id)
            .order_by(PlayerFeatureDaily.date.desc())
            .first()
        )

        load = (
            db.query(PlayerTrainingLoad)
            .filter(PlayerTrainingLoad.player_id == player_id)
            .order_by(PlayerTrainingLoad.id.desc())
            .first()
        )

        # Load models
        inj_model = load(INJURY_MODEL_PATH) if os.path.exists(INJURY_MODEL_PATH) else None
        perf_model = load(PERF_MODEL_PATH) if os.path.exists(PERF_MODEL_PATH) else None

        today = date.today()
        preds = []

        # Injury risk
        if inj_model and load:
            X = [[load.load_acute or 0, load.load_chronic or 0, load.monotony or 0, load.strain or 0]]
            try:
                proba = float(inj_model.predict_proba(X)[0][1])
            except Exception:
                proba = None

            # Get organization_id from load
            org_id = load.organization_id

            pred = PlayerPrediction(
                organization_id=org_id,
                player_id=player_id,
                date=today,
                target="injury_risk",
                model_name="LogisticRegression",
                model_version=MODEL_VERSION,
                y_pred=proba,
                y_proba=proba,
            )
            db.add(pred)
            preds.append(pred)

        # Performance index
        if perf_model and feat:
            X = [[feat.rolling_7d_load or 0, feat.rolling_21d_load or 0]]
            try:
                yhat = float(perf_model.predict(X)[0])
            except Exception:
                yhat = None

            org_id = feat.organization_id

            pred = PlayerPrediction(
                organization_id=org_id,
                player_id=player_id,
                date=today,
                target="performance_index",
                model_name="LinearRegression",
                model_version=MODEL_VERSION,
                y_pred=yhat,
                y_proba=None,
            )
            db.add(pred)
            preds.append(pred)

        db.commit()

        return {
            "player_id": str(player_id),
            "predictions": [
                {
                    "date": p.date,
                    "target": p.target,
                    "model_name": p.model_name,
                    "model_version": p.model_version,
                    "y_pred": p.y_pred,
                    "y_proba": p.y_proba,
                }
                for p in preds
            ],
        }
