"""
Youth Soccer Feature Engineering Module.
INNOVATIVE feature extraction for young soccer players development.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.player import Player
from app.models.session import TrainingSession
from app.models.performance import TechnicalStats, TacticalCognitive, PsychologicalProfile
from app.models.test import PhysicalTest
from app.models.wellness import WellnessData
from app.models.match import Match

logger = logging.getLogger(__name__)


class YouthSoccerFeatureEngine:
    """
    Motore di feature engineering INNOVATIVO per giovani calciatori.
    Feature specifiche per sviluppo giovanile e crescita atletica.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.feature_cache = {}

    async def calculate_growth_aware_metrics(self, player_id: str, days_back: int = 90) -> Dict:
        """
        Metriche che considerano lo sviluppo puberale e la crescita.
        """
        result = await self.db.execute(select(Player).where(Player.id == player_id))
        player = result.scalar_one_or_none()

        if not player:
            return {}

        # Età biologica vs cronologica
        biological_age = self._estimate_biological_age(player)
        age_factor = biological_age / player.age if player.age else 1.0

        # Carico tollerabile età-specifico
        load_data = await self._get_training_load_data(player_id, days_back)
        tolerance_ratio = self._calculate_load_tolerance(load_data, age_factor)

        return {
            "biological_age_factor": biological_age,
            "load_tolerance_ratio": tolerance_ratio,
            "growth_velocity_indicator": await self._calculate_growth_velocity(player_id),
            "pubertal_development_score": self._estimate_pubertal_stage(player)
        }

    async def calculate_skill_acquisition_metrics(self, player_id: str) -> Dict:
        """
        Misura la velocità di apprendimento e adattamento.
        """
        technical_data = await self._get_technical_improvement_data(player_id)
        tactical_data = await self._get_tactical_learning_data(player_id)

        skill_rate = self._calculate_learning_velocity(technical_data)
        decision_speed = self._calculate_decision_making_improvement(tactical_data)

        return {
            "skill_acquisition_rate": skill_rate,
            "decision_making_velocity": decision_speed,
            "adaptability_index": await self._calculate_adaptability(player_id),
            "consistency_score": await self._calculate_performance_consistency(player_id)
        }

    async def calculate_mental_resilience_metrics(self, player_id: str) -> Dict:
        """
        Metriche psicologiche specifiche per giovani atleti.
        """
        wellness_data = await self._get_wellness_data(player_id, 30)
        match_performance = await self._get_performance_under_pressure(player_id)

        return {
            "pressure_performance_ratio": match_performance.get("pressure_ratio", 0.5),
            "mental_fatigue_resistance": self._calculate_mental_recovery(wellness_data),
            "motivation_consistency": self._calculate_motivation_stability(wellness_data),
            "focus_durability": await self._calculate_focus_metrics(player_id)
        }

    async def create_player_feature_vector(self, player_id: str) -> Dict:
        """
        Crea un vettore di feature completo per il ML.
        """
        growth_metrics = await self.calculate_growth_aware_metrics(player_id)
        skill_metrics = await self.calculate_skill_acquisition_metrics(player_id)
        mental_metrics = await self.calculate_mental_resilience_metrics(player_id)
        physical_metrics = await self._calculate_physical_profile(player_id)

        # Feature composite innovative
        composite_features = {
            "potential_gap_score": await self._calculate_potential_gap(player_id),
            "development_trajectory": await self._calculate_trajectory_slope(player_id),
            "risk_benefit_ratio": await self._calculate_risk_benefit(player_id)
        }

        return {
            **growth_metrics,
            **skill_metrics,
            **mental_metrics,
            **physical_metrics,
            **composite_features,
            "timestamp": datetime.utcnow().isoformat()
        }

    # ===== METODI PRIVATI PER CALCOLI COMPLESSI =====

    def _estimate_biological_age(self, player: Player) -> float:
        """Stima età biologica basata su sviluppo fisico."""
        # Implementazione semplificata - in produzione usare metriche antropometriche
        base_age = player.age or 16
        # Aggiustamento basato su altezza/peso vs medie età
        height_factor = 1.0
        if player.height and player.weight:
            # Logica semplificata per demo
            bmi = player.weight / ((player.height / 100) ** 2)
            if bmi > 22:  # Sviluppo avanzato
                height_factor = 1.1
            elif bmi < 18:  # Sviluppo ritardato
                height_factor = 0.9
        return base_age * height_factor

    def _calculate_load_tolerance(self, load_data: List, age_factor: float) -> float:
        """Calcola rapporto carico tollerato vs carico applicato."""
        if not load_data:
            return 0.5

        loads = [ld.get('load', 0) for ld in load_data if ld.get('load')]
        if not loads:
            return 0.5

        avg_load = np.mean(loads)
        max_tolerable = 100 * age_factor  # Semplificato
        return min(avg_load / max_tolerable, 1.0) if max_tolerable > 0 else 0.5

    def _calculate_learning_velocity(self, tech_data: List) -> float:
        """Calcola velocità di apprendimento skills tecniche."""
        if len(tech_data) < 2:
            return 0.5

        improvements = []
        for i in range(1, len(tech_data)):
            if tech_data[i].get('value', 0) > tech_data[i-1].get('value', 0):
                improvement = tech_data[i]['value'] - tech_data[i-1]['value']
                improvements.append(improvement)

        return float(np.mean(improvements)) if improvements else 0.0

    async def _calculate_potential_gap(self, player_id: str) -> float:
        """Calcola il gap tra potenziale stimato e performance attuale."""
        # Implementazione semplificata
        current_perf = await self._get_current_performance(player_id)
        estimated_potential = await self._estimate_potential(player_id)

        if estimated_potential > 0:
            return current_perf / estimated_potential
        return 0.7  # Default

    async def _get_training_load_data(self, player_id: str, days: int) -> List:
        """Recupera dati carico allenamento."""
        # Query semplificata - in produzione fare join con player_sessions
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        # TODO: Implementare query reale quando player_session_data sarà disponibile
        return []

    async def _get_technical_improvement_data(self, player_id: str) -> List:
        """Recupera dati miglioramento tecnico."""
        # TODO: Query su TechnicalStats ordinata per data
        return []

    async def _get_tactical_learning_data(self, player_id: str) -> List:
        """Recupera dati apprendimento tattico."""
        # TODO: Query su TacticalCognitive ordinata per data
        return []

    async def _get_wellness_data(self, player_id: str, days: int) -> List:
        """Recupera dati wellness."""
        # TODO: Query su WellnessData
        return []

    async def _get_current_performance(self, player_id: str) -> float:
        """Recupera performance corrente."""
        # TODO: Implementare logica reale
        return 0.7

    async def _estimate_potential(self, player_id: str) -> float:
        """Stima potenziale del giocatore."""
        # TODO: Implementare algoritmo di stima potenziale
        return 0.85

    # Altri metodi privati semplificati per demo
    async def _calculate_growth_velocity(self, player_id: str) -> float:
        return 0.5

    def _estimate_pubertal_stage(self, player: Player) -> float:
        return 0.5

    def _calculate_decision_making_improvement(self, tactical_data: List) -> float:
        return 0.5

    async def _calculate_adaptability(self, player_id: str) -> float:
        return 0.5

    async def _calculate_performance_consistency(self, player_id: str) -> float:
        return 0.5

    def _calculate_mental_recovery(self, wellness_data: List) -> float:
        return 0.5

    def _calculate_motivation_stability(self, wellness_data: List) -> float:
        return 0.5

    async def _calculate_focus_metrics(self, player_id: str) -> float:
        return 0.5

    async def _calculate_physical_profile(self, player_id: str) -> Dict:
        return {"physical_readiness": 0.7}

    async def _calculate_trajectory_slope(self, player_id: str) -> float:
        return 0.5

    async def _calculate_risk_benefit(self, player_id: str) -> float:
        return 0.5

    async def _get_performance_under_pressure(self, player_id: str) -> Dict:
        return {"pressure_ratio": 0.5}
