"""Automated insights generator using AI/ML to detect patterns and anomalies."""

import json
from datetime import date, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.advanced_tracking import AutomatedInsight, InsightPriority, InsightType, PlayerGoal
from app.models.player import Player
from app.models.test import PhysicalTest, TechnicalTest
from app.models.wellness import WellnessData


class InsightsGenerator:
    """Generate automated insights from player data."""

    def __init__(self, session: AsyncSession, organization_id: UUID):
        """Initialize insights generator."""
        self.session = session
        self.organization_id = organization_id

    async def generate_performance_drop_insight(
        self,
        player_id: UUID,
        metric_name: str,
        current_avg: float,
        baseline_avg: float,
        drop_pct: float
    ) -> Optional[AutomatedInsight]:
        """
        Generate insight for significant performance drop.

        Args:
            player_id: Player UUID
            metric_name: Name of metric (e.g., "pass_accuracy")
            current_avg: Current period average
            baseline_avg: Historical baseline
            drop_pct: Percentage drop (positive number)
        """
        if drop_pct < 10:  # Only alert if drop > 10%
            return None

        # Get player info
        player_result = await self.session.execute(
            select(Player).where(Player.id == player_id)
        )
        player = player_result.scalar_one_or_none()
        if not player:
            return None

        # Determine priority based on drop magnitude
        if drop_pct >= 25:
            priority = InsightPriority.CRITICAL
        elif drop_pct >= 15:
            priority = InsightPriority.HIGH
        else:
            priority = InsightPriority.MEDIUM

        title = f"{player.first_name} {player.last_name}: Calo {metric_name} -{drop_pct:.0f}%"
        description = (
            f"Il giocatore mostra un calo significativo in {metric_name}. "
            f"Media attuale: {current_avg:.1f}, baseline storico: {baseline_avg:.1f}. "
            f"Calo del {drop_pct:.0f}% rispetto al normale."
        )
        recommendation = (
            f"Consigliato: 1) Analizzare dati wellness recenti (sonno, fatica), "
            f"2) Verificare carico allenamenti, 3) Colloquio con giocatore per identificare cause."
        )

        supporting_data = json.dumps({
            "metric": metric_name,
            "current_avg": current_avg,
            "baseline_avg": baseline_avg,
            "drop_percentage": drop_pct,
            "period_days": 14
        })

        insight = AutomatedInsight(
            player_id=player_id,
            team_id=player.team_id,
            insight_type=InsightType.PERFORMANCE_DROP,
            priority=priority,
            category="PERFORMANCE",
            title=title,
            description=description,
            actionable_recommendation=recommendation,
            supporting_data=supporting_data,
            confidence_score=0.85,
            date_from=date.today() - timedelta(days=14),
            date_to=date.today(),
            organization_id=self.organization_id
        )

        return insight

    async def generate_injury_risk_insight(
        self,
        player_id: UUID,
        injury_risk: float,
        risk_factors: Dict
    ) -> Optional[AutomatedInsight]:
        """
        Generate insight for elevated injury risk.

        Args:
            player_id: Player UUID
            injury_risk: Risk score 0-1
            risk_factors: Dict of contributing factors
        """
        if injury_risk < 0.6:  # Only alert if risk > 60%
            return None

        # Get player
        player_result = await self.session.execute(
            select(Player).where(Player.id == player_id)
        )
        player = player_result.scalar_one_or_none()
        if not player:
            return None

        # Priority based on risk
        if injury_risk >= 0.8:
            priority = InsightPriority.CRITICAL
        elif injury_risk >= 0.7:
            priority = InsightPriority.HIGH
        else:
            priority = InsightPriority.MEDIUM

        title = f"{player.first_name} {player.last_name}: Rischio Infortunio {injury_risk*100:.0f}%"

        # Format risk factors
        factors_text = ", ".join([f"{k}: {v:.1f}" for k, v in risk_factors.items()])

        description = (
            f"Il giocatore presenta un rischio infortunio elevato ({injury_risk*100:.0f}%). "
            f"Fattori critici: {factors_text}. "
            f"Consigliato ridurre carico e monitorare attentamente."
        )

        recommendation = (
            f"Azioni immediate: 1) Ridurre intensità allenamento per 48-72h, "
            f"2) Sessione recupero attivo, 3) Valutazione medica se necessario, "
            f"4) Monitoraggio HRV e wellness giornaliero."
        )

        supporting_data = json.dumps({
            "injury_risk_0_1": injury_risk,
            "risk_factors": risk_factors,
            "date": date.today().isoformat()
        })

        insight = AutomatedInsight(
            player_id=player_id,
            team_id=player.team_id,
            insight_type=InsightType.INJURY_RISK,
            priority=priority,
            category="INJURY",
            title=title,
            description=description,
            actionable_recommendation=recommendation,
            supporting_data=supporting_data,
            confidence_score=0.78,
            date_from=date.today() - timedelta(days=7),
            date_to=date.today(),
            organization_id=self.organization_id
        )

        return insight

    async def generate_wellness_alert_insight(
        self,
        player_id: UUID,
        alert_metrics: List[str],
        avg_values: Dict
    ) -> Optional[AutomatedInsight]:
        """
        Generate insight for poor wellness metrics.

        Args:
            player_id: Player UUID
            alert_metrics: List of concerning metrics (e.g., ["sleep", "stress"])
            avg_values: Dict of average values
        """
        if not alert_metrics:
            return None

        # Get player
        player_result = await self.session.execute(
            select(Player).where(Player.id == player_id)
        )
        player = player_result.scalar_one_or_none()
        if not player:
            return None

        priority = InsightPriority.HIGH if len(alert_metrics) >= 3 else InsightPriority.MEDIUM

        metrics_str = ", ".join(alert_metrics)
        title = f"{player.first_name} {player.last_name}: Alert Wellness ({metrics_str})"

        description = (
            f"Giocatore mostra valori wellness preoccupanti negli ultimi 7 giorni. "
            f"Metriche sotto soglia: {metrics_str}. "
        )

        if "sleep" in alert_metrics:
            description += f" Sonno medio: {avg_values.get('sleep_hours', 0):.1f}h (ottimale >7.5h)."
        if "stress" in alert_metrics:
            description += f" Stress medio: {avg_values.get('stress_rating', 0):.1f}/5 (ottimale <2.5)."
        if "fatigue" in alert_metrics:
            description += f" Fatica media: {avg_values.get('fatigue_rating', 0):.1f}/5 (ottimale <3)."

        recommendation = (
            f"Interventi suggeriti: 1) Colloquio individuale con giocatore, "
            f"2) Valutare riduzione carico temporanea, "
            f"3) Supporto psicologico/nutrizionale se necessario."
        )

        supporting_data = json.dumps({
            "alert_metrics": alert_metrics,
            "avg_values": avg_values,
            "period_days": 7
        })

        insight = AutomatedInsight(
            player_id=player_id,
            team_id=player.team_id,
            insight_type=InsightType.WELLNESS_ALERT,
            priority=priority,
            category="WELLNESS",
            title=title,
            description=description,
            actionable_recommendation=recommendation,
            supporting_data=supporting_data,
            confidence_score=0.82,
            date_from=date.today() - timedelta(days=7),
            date_to=date.today(),
            organization_id=self.organization_id
        )

        return insight

    async def generate_goal_progress_insight(
        self,
        player_id: UUID,
        goal: PlayerGoal,
        is_on_track: bool,
        predicted_final_value: Optional[float] = None
    ) -> Optional[AutomatedInsight]:
        """
        Generate insight about goal progress.

        Args:
            player_id: Player UUID
            goal: PlayerGoal object
            is_on_track: Whether goal is on track
            predicted_final_value: ML prediction of final value
        """
        # Get player
        player_result = await self.session.execute(
            select(Player).where(Player.id == player_id)
        )
        player = player_result.scalar_one_or_none()
        if not player:
            return None

        if is_on_track:
            priority = InsightPriority.LOW
            title = f"{player.first_name} {player.last_name}: Obiettivo '{goal.title}' In Linea"
            description = (
                f"Il giocatore sta progredendo bene verso l'obiettivo '{goal.title}'. "
                f"Progresso attuale: {goal.progress_pct:.0f}%, "
                f"valore corrente: {goal.current_value:.1f} {goal.unit}. "
                f"Target: {goal.target_value:.1f} {goal.unit} entro {goal.target_date}."
            )
            recommendation = "Continuare con il piano attuale. Monitoraggio periodico."
        else:
            priority = InsightPriority.MEDIUM
            title = f"{player.first_name} {player.last_name}: Obiettivo '{goal.title}' A Rischio"
            description = (
                f"L'obiettivo '{goal.title}' rischia di non essere raggiunto. "
                f"Progresso attuale: {goal.progress_pct:.0f}%, "
                f"giorni rimanenti: {goal.days_remaining}. "
            )
            if predicted_final_value:
                description += f"Valore previsto a fine periodo: {predicted_final_value:.1f} {goal.unit} (target: {goal.target_value:.1f})."
            recommendation = (
                "Azioni correttive: 1) Rivedere piano allenamento per focus su metrica obiettivo, "
                "2) Aumentare frequenza allenamenti specifici, 3) Colloquio motivazionale con giocatore."
            )

        supporting_data = json.dumps({
            "goal_id": str(goal.id),
            "goal_title": goal.title,
            "metric": goal.metric_name,
            "current_value": goal.current_value,
            "target_value": goal.target_value,
            "progress_pct": goal.progress_pct,
            "days_remaining": goal.days_remaining,
            "is_on_track": is_on_track,
            "predicted_final_value": predicted_final_value
        })

        insight = AutomatedInsight(
            player_id=player_id,
            team_id=player.team_id,
            insight_type=InsightType.GOAL_PROGRESS,
            priority=priority,
            category="GOAL",
            title=title,
            description=description,
            actionable_recommendation=recommendation,
            supporting_data=supporting_data,
            confidence_score=0.75,
            date_from=goal.start_date,
            date_to=goal.target_date,
            organization_id=self.organization_id
        )

        return insight

    async def generate_performance_peak_insight(
        self,
        player_id: UUID,
        metric_name: str,
        current_value: float,
        percentile_vs_history: float
    ) -> Optional[AutomatedInsight]:
        """
        Generate insight for exceptional performance.

        Args:
            player_id: Player UUID
            metric_name: Metric name
            current_value: Current value
            percentile_vs_history: Percentile vs player's history (0-100)
        """
        if percentile_vs_history < 90:  # Only celebrate top 10% performances
            return None

        # Get player
        player_result = await self.session.execute(
            select(Player).where(Player.id == player_id)
        )
        player = player_result.scalar_one_or_none()
        if not player:
            return None

        priority = InsightPriority.LOW

        title = f"{player.first_name} {player.last_name}: Picco Performance in {metric_name}!"
        description = (
            f"Il giocatore ha raggiunto un picco di performance in {metric_name}. "
            f"Valore: {current_value:.1f}, percentile storico: {percentile_vs_history:.0f}º. "
            f"Uno dei migliori risultati personali!"
        )
        recommendation = (
            "Complimenti al giocatore! Analizzare i fattori che hanno contribuito al picco "
            "(wellness, carico allenamento, motivazione) per replicare il successo."
        )

        supporting_data = json.dumps({
            "metric": metric_name,
            "current_value": current_value,
            "percentile_vs_history": percentile_vs_history,
            "date": date.today().isoformat()
        })

        insight = AutomatedInsight(
            player_id=player_id,
            team_id=player.team_id,
            insight_type=InsightType.PERFORMANCE_PEAK,
            priority=priority,
            category="PERFORMANCE",
            title=title,
            description=description,
            actionable_recommendation=recommendation,
            supporting_data=supporting_data,
            confidence_score=0.90,
            date_from=date.today(),
            date_to=date.today(),
            organization_id=self.organization_id
        )

        return insight

    async def save_insight(self, insight: AutomatedInsight) -> AutomatedInsight:
        """Save insight to database."""
        self.session.add(insight)
        await self.session.commit()
        await self.session.refresh(insight)
        return insight

    async def generate_all_insights_for_player(self, player_id: UUID) -> List[AutomatedInsight]:
        """
        Generate all applicable insights for a player.

        Returns:
            List of generated insights
        """
        insights = []

        # TODO: Implement checks for each insight type
        # This is a skeleton - would need actual metric calculations

        # Example: Check for performance drops
        # ... calculate metrics ...
        # insight = await self.generate_performance_drop_insight(...)
        # if insight:
        #     insights.append(await self.save_insight(insight))

        return insights
