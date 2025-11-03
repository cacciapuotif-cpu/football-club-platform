"""Complete data seed script with 50+ realistic players and training sessions."""

import asyncio
import random
from datetime import datetime, timedelta, date
from uuid import uuid4
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import get_async_session
from app.models.player import Player, PlayerRole, DominantFoot
from app.models.team import Team, Season
from app.models.organization import Organization
from app.models.session import TrainingSession, SessionType, SessionIntensity
from app.models.player_training_stats import PlayerTrainingStats


# Real player data based on top Serie A players
REAL_PLAYERS_DATA = [
    # GOALKEEPERS
    {
        "first_name": "Gianluigi", "last_name": "Donnarumma", "role_primary": PlayerRole.GK,
        "age": 24, "nationality": "IT", "height_cm": 196, "weight_kg": 90,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 88, "positioning": 92, "decision_making": 85, "work_rate": 80,
        "mental_strength": 90, "leadership": 85, "concentration": 88, "adaptability": 82,
        "overall_rating": 8.7, "potential_rating": 9.2, "market_value_eur": 45000000
    },
    {
        "first_name": "Mike", "last_name": "Maignan", "role_primary": PlayerRole.GK,
        "age": 28, "nationality": "FR", "height_cm": 191, "weight_kg": 89,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 86, "positioning": 90, "decision_making": 87, "work_rate": 82,
        "mental_strength": 88, "leadership": 82, "concentration": 90, "adaptability": 80,
        "overall_rating": 8.5, "potential_rating": 8.8, "market_value_eur": 40000000
    },
    {
        "first_name": "Alex", "last_name": "Meret", "role_primary": PlayerRole.GK,
        "age": 26, "nationality": "IT", "height_cm": 190, "weight_kg": 82,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "good",
        "tactical_awareness": 80, "positioning": 84, "decision_making": 78, "work_rate": 75,
        "mental_strength": 76, "leadership": 70, "concentration": 80, "adaptability": 75,
        "overall_rating": 7.8, "potential_rating": 8.3, "market_value_eur": 25000000
    },

    # DEFENDERS
    {
        "first_name": "Alessandro", "last_name": "Bastoni", "role_primary": PlayerRole.DF,
        "age": 24, "nationality": "IT", "height_cm": 190, "weight_kg": 82,
        "dominant_foot": DominantFoot.LEFT, "physical_condition": "excellent",
        "tactical_awareness": 85, "positioning": 87, "decision_making": 83, "work_rate": 84,
        "mental_strength": 82, "leadership": 80, "concentration": 85, "adaptability": 78,
        "overall_rating": 8.4, "potential_rating": 9.0, "market_value_eur": 60000000
    },
    {
        "first_name": "Gleison", "last_name": "Bremer", "role_primary": PlayerRole.DF,
        "age": 26, "nationality": "BR", "height_cm": 188, "weight_kg": 84,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 82, "positioning": 88, "decision_making": 80, "work_rate": 87,
        "mental_strength": 85, "leadership": 78, "concentration": 84, "adaptability": 76,
        "overall_rating": 8.3, "potential_rating": 8.7, "market_value_eur": 55000000
    },
    {
        "first_name": "Kim", "last_name": "Min-jae", "role_primary": PlayerRole.DF,
        "age": 27, "nationality": "KR", "height_cm": 190, "weight_kg": 86,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 83, "positioning": 89, "decision_making": 81, "work_rate": 88,
        "mental_strength": 87, "leadership": 80, "concentration": 86, "adaptability": 79,
        "overall_rating": 8.5, "potential_rating": 8.8, "market_value_eur": 58000000
    },
    {
        "first_name": "Rafael", "last_name": "Toloi", "role_primary": PlayerRole.DF,
        "age": 32, "nationality": "BR", "height_cm": 185, "weight_kg": 79,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "good",
        "tactical_awareness": 80, "positioning": 84, "decision_making": 82, "work_rate": 80,
        "mental_strength": 84, "leadership": 82, "concentration": 83, "adaptability": 77,
        "overall_rating": 7.9, "potential_rating": 7.9, "market_value_eur": 15000000
    },
    {
        "first_name": "Theo", "last_name": "Hernandez", "role_primary": PlayerRole.DF,
        "age": 25, "nationality": "FR", "height_cm": 184, "weight_kg": 81,
        "dominant_foot": DominantFoot.LEFT, "physical_condition": "excellent",
        "tactical_awareness": 78, "positioning": 75, "decision_making": 76, "work_rate": 92,
        "mental_strength": 85, "leadership": 75, "concentration": 76, "adaptability": 80,
        "overall_rating": 8.3, "potential_rating": 8.7, "market_value_eur": 50000000
    },
    {
        "first_name": "Federico", "last_name": "Dimarco", "role_primary": PlayerRole.DF,
        "age": 26, "nationality": "IT", "height_cm": 176, "weight_kg": 75,
        "dominant_foot": DominantFoot.LEFT, "physical_condition": "excellent",
        "tactical_awareness": 82, "positioning": 80, "decision_making": 79, "work_rate": 88,
        "mental_strength": 80, "leadership": 75, "concentration": 81, "adaptability": 78,
        "overall_rating": 8.0, "potential_rating": 8.4, "market_value_eur": 35000000
    },
    {
        "first_name": "Giovanni", "last_name": "Di Lorenzo", "role_primary": PlayerRole.DF,
        "age": 30, "nationality": "IT", "height_cm": 183, "weight_kg": 76,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "good",
        "tactical_awareness": 83, "positioning": 85, "decision_making": 82, "work_rate": 90,
        "mental_strength": 86, "leadership": 84, "concentration": 84, "adaptability": 80,
        "overall_rating": 8.1, "potential_rating": 8.1, "market_value_eur": 25000000
    },
    {
        "first_name": "Juan", "last_name": "Cuadrado", "role_primary": PlayerRole.DF,
        "age": 35, "nationality": "CO", "height_cm": 179, "weight_kg": 72,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "normal",
        "tactical_awareness": 85, "positioning": 80, "decision_making": 83, "work_rate": 82,
        "mental_strength": 88, "leadership": 85, "concentration": 82, "adaptability": 86,
        "overall_rating": 7.7, "potential_rating": 7.5, "market_value_eur": 8000000
    },

    # MIDFIELDERS
    {
        "first_name": "Nicolò", "last_name": "Barella", "role_primary": PlayerRole.MF,
        "age": 26, "nationality": "IT", "height_cm": 175, "weight_kg": 68,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 87, "positioning": 85, "decision_making": 88, "work_rate": 92,
        "mental_strength": 90, "leadership": 86, "concentration": 87, "adaptability": 85,
        "overall_rating": 8.8, "potential_rating": 9.1, "market_value_eur": 75000000
    },
    {
        "first_name": "Hakan", "last_name": "Calhanoglu", "role_primary": PlayerRole.MF,
        "age": 29, "nationality": "TR", "height_cm": 178, "weight_kg": 75,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 86, "positioning": 84, "decision_making": 87, "work_rate": 86,
        "mental_strength": 84, "leadership": 82, "concentration": 86, "adaptability": 83,
        "overall_rating": 8.4, "potential_rating": 8.5, "market_value_eur": 40000000
    },
    {
        "first_name": "Sergej", "last_name": "Milinkovic-Savic", "role_primary": PlayerRole.MF,
        "age": 28, "nationality": "RS", "height_cm": 191, "weight_kg": 80,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 84, "positioning": 83, "decision_making": 85, "work_rate": 85,
        "mental_strength": 86, "leadership": 80, "concentration": 84, "adaptability": 81,
        "overall_rating": 8.3, "potential_rating": 8.6, "market_value_eur": 55000000
    },
    {
        "first_name": "Franck", "last_name": "Kessie", "role_primary": PlayerRole.MF,
        "age": 27, "nationality": "CI", "height_cm": 183, "weight_kg": 78,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 79, "positioning": 78, "decision_making": 77, "work_rate": 90,
        "mental_strength": 85, "leadership": 78, "concentration": 80, "adaptability": 76,
        "overall_rating": 7.9, "potential_rating": 8.2, "market_value_eur": 30000000
    },
    {
        "first_name": "Stanislav", "last_name": "Lobotka", "role_primary": PlayerRole.MF,
        "age": 28, "nationality": "SK", "height_cm": 173, "weight_kg": 66,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "good",
        "tactical_awareness": 88, "positioning": 86, "decision_making": 89, "work_rate": 84,
        "mental_strength": 82, "leadership": 75, "concentration": 87, "adaptability": 83,
        "overall_rating": 8.2, "potential_rating": 8.4, "market_value_eur": 35000000
    },
    {
        "first_name": "Marcelo", "last_name": "Brozovic", "role_primary": PlayerRole.MF,
        "age": 31, "nationality": "HR", "height_cm": 181, "weight_kg": 68,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "good",
        "tactical_awareness": 87, "positioning": 88, "decision_making": 86, "work_rate": 85,
        "mental_strength": 87, "leadership": 84, "concentration": 88, "adaptability": 84,
        "overall_rating": 8.3, "potential_rating": 8.3, "market_value_eur": 25000000
    },
    {
        "first_name": "Henrikh", "last_name": "Mkhitaryan", "role_primary": PlayerRole.MF,
        "age": 34, "nationality": "AM", "height_cm": 177, "weight_kg": 75,
        "dominant_foot": DominantFoot.BOTH, "physical_condition": "normal",
        "tactical_awareness": 85, "positioning": 82, "decision_making": 88, "work_rate": 80,
        "mental_strength": 88, "leadership": 86, "concentration": 84, "adaptability": 87,
        "overall_rating": 7.8, "potential_rating": 7.6, "market_value_eur": 10000000
    },
    {
        "first_name": "Sandro", "last_name": "Tonali", "role_primary": PlayerRole.MF,
        "age": 23, "nationality": "IT", "height_cm": 181, "weight_kg": 76,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 82, "positioning": 80, "decision_making": 79, "work_rate": 89,
        "mental_strength": 78, "leadership": 76, "concentration": 80, "adaptability": 75,
        "overall_rating": 7.9, "potential_rating": 8.7, "market_value_eur": 45000000
    },
    {
        "first_name": "Tijjani", "last_name": "Reijnders", "role_primary": PlayerRole.MF,
        "age": 25, "nationality": "NL", "height_cm": 180, "weight_kg": 74,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "good",
        "tactical_awareness": 76, "positioning": 74, "decision_making": 78, "work_rate": 82,
        "mental_strength": 74, "leadership": 70, "concentration": 76, "adaptability": 77,
        "overall_rating": 7.4, "potential_rating": 8.2, "market_value_eur": 28000000
    },
    {
        "first_name": "Piotr", "last_name": "Zielinski", "role_primary": PlayerRole.MF,
        "age": 29, "nationality": "PL", "height_cm": 180, "weight_kg": 74,
        "dominant_foot": DominantFoot.BOTH, "physical_condition": "good",
        "tactical_awareness": 82, "positioning": 79, "decision_making": 84, "work_rate": 80,
        "mental_strength": 80, "leadership": 75, "concentration": 82, "adaptability": 81,
        "overall_rating": 7.9, "potential_rating": 8.0, "market_value_eur": 22000000
    },

    # FORWARDS
    {
        "first_name": "Victor", "last_name": "Osimhen", "role_primary": PlayerRole.FW,
        "age": 24, "nationality": "NG", "height_cm": 185, "weight_kg": 78,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 78, "positioning": 85, "decision_making": 76, "work_rate": 90,
        "mental_strength": 88, "leadership": 75, "concentration": 80, "adaptability": 82,
        "overall_rating": 8.6, "potential_rating": 9.3, "market_value_eur": 120000000
    },
    {
        "first_name": "Lautaro", "last_name": "Martinez", "role_primary": PlayerRole.FW,
        "age": 26, "nationality": "AR", "height_cm": 174, "weight_kg": 72,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 84, "positioning": 88, "decision_making": 82, "work_rate": 89,
        "mental_strength": 86, "leadership": 82, "concentration": 84, "adaptability": 81,
        "overall_rating": 8.7, "potential_rating": 9.0, "market_value_eur": 100000000
    },
    {
        "first_name": "Rafael", "last_name": "Leao", "role_primary": PlayerRole.FW,
        "age": 24, "nationality": "PT", "height_cm": 188, "weight_kg": 84,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 75, "positioning": 78, "decision_making": 74, "work_rate": 76,
        "mental_strength": 76, "leadership": 70, "concentration": 74, "adaptability": 78,
        "overall_rating": 8.2, "potential_rating": 9.0, "market_value_eur": 85000000
    },
    {
        "first_name": "Dusan", "last_name": "Vlahovic", "role_primary": PlayerRole.FW,
        "age": 23, "nationality": "RS", "height_cm": 190, "weight_kg": 80,
        "dominant_foot": DominantFoot.LEFT, "physical_condition": "excellent",
        "tactical_awareness": 76, "positioning": 82, "decision_making": 75, "work_rate": 82,
        "mental_strength": 80, "leadership": 75, "concentration": 78, "adaptability": 76,
        "overall_rating": 8.1, "potential_rating": 8.9, "market_value_eur": 70000000
    },
    {
        "first_name": "Khvicha", "last_name": "Kvaratskhelia", "role_primary": PlayerRole.FW,
        "age": 22, "nationality": "GE", "height_cm": 183, "weight_kg": 75,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 76, "positioning": 80, "decision_making": 77, "work_rate": 84,
        "mental_strength": 80, "leadership": 72, "concentration": 78, "adaptability": 82,
        "overall_rating": 8.3, "potential_rating": 9.2, "market_value_eur": 80000000
    },
    {
        "first_name": "Marcus", "last_name": "Thuram", "role_primary": PlayerRole.FW,
        "age": 26, "nationality": "FR", "height_cm": 192, "weight_kg": 88,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "excellent",
        "tactical_awareness": 78, "positioning": 81, "decision_making": 76, "work_rate": 86,
        "mental_strength": 82, "leadership": 76, "concentration": 79, "adaptability": 80,
        "overall_rating": 8.0, "potential_rating": 8.6, "market_value_eur": 45000000
    },
    {
        "first_name": "Olivier", "last_name": "Giroud", "role_primary": PlayerRole.FW,
        "age": 37, "nationality": "FR", "height_cm": 193, "weight_kg": 93,
        "dominant_foot": DominantFoot.LEFT, "physical_condition": "good",
        "tactical_awareness": 84, "positioning": 88, "decision_making": 85, "work_rate": 78,
        "mental_strength": 90, "leadership": 88, "concentration": 86, "adaptability": 85,
        "overall_rating": 7.8, "potential_rating": 7.5, "market_value_eur": 5000000
    },
    {
        "first_name": "Paulo", "last_name": "Dybala", "role_primary": PlayerRole.FW,
        "age": 30, "nationality": "AR", "height_cm": 177, "weight_kg": 75,
        "dominant_foot": DominantFoot.LEFT, "physical_condition": "normal",
        "tactical_awareness": 86, "positioning": 84, "decision_making": 87, "work_rate": 75,
        "mental_strength": 83, "leadership": 78, "concentration": 84, "adaptability": 82,
        "overall_rating": 8.2, "potential_rating": 8.3, "market_value_eur": 30000000
    },
    {
        "first_name": "Romelu", "last_name": "Lukaku", "role_primary": PlayerRole.FW,
        "age": 30, "nationality": "BE", "height_cm": 191, "weight_kg": 94,
        "dominant_foot": DominantFoot.LEFT, "physical_condition": "normal",
        "tactical_awareness": 76, "positioning": 84, "decision_making": 74, "work_rate": 80,
        "mental_strength": 78, "leadership": 76, "concentration": 76, "adaptability": 75,
        "overall_rating": 7.9, "potential_rating": 7.9, "market_value_eur": 25000000
    },
    {
        "first_name": "Ciro", "last_name": "Immobile", "role_primary": PlayerRole.FW,
        "age": 33, "nationality": "IT", "height_cm": 185, "weight_kg": 78,
        "dominant_foot": DominantFoot.RIGHT, "physical_condition": "good",
        "tactical_awareness": 82, "positioning": 90, "decision_making": 80, "work_rate": 82,
        "mental_strength": 86, "leadership": 84, "concentration": 84, "adaptability": 80,
        "overall_rating": 8.0, "potential_rating": 7.8, "market_value_eur": 12000000
    },
]

# Additional players to reach 50+
ADDITIONAL_PLAYERS = [
    # More GKs
    {"first_name": "Wojciech", "last_name": "Szczesny", "role": PlayerRole.GK, "age": 33, "rating": 7.9, "market_value": 10000000},
    {"first_name": "Ivan", "last_name": "Provedel", "role": PlayerRole.GK, "age": 29, "rating": 7.5, "market_value": 8000000},
    # More DFs
    {"first_name": "Matteo", "last_name": "Darmian", "role": PlayerRole.DF, "age": 34, "rating": 7.3, "market_value": 3000000},
    {"first_name": "Stefan", "last_name": "de Vrij", "role": PlayerRole.DF, "age": 31, "rating": 7.8, "market_value": 12000000},
    {"first_name": "Alessandro", "last_name": "Florenzi", "role": PlayerRole.DF, "age": 32, "rating": 7.4, "market_value": 5000000},
    {"first_name": "Merih", "last_name": "Demiral", "role": PlayerRole.DF, "age": 25, "rating": 7.6, "market_value": 20000000},
    {"first_name": "Alessio", "last_name": "Romagnoli", "role": PlayerRole.DF, "age": 28, "rating": 7.5, "market_value": 15000000},
    {"first_name": "Mario", "last_name": "Rui", "role": PlayerRole.DF, "age": 32, "rating": 7.2, "market_value": 4000000},
    {"first_name": "Davide", "last_name": "Calabria", "role": PlayerRole.DF, "age": 27, "rating": 7.4, "market_value": 12000000},
    {"first_name": "Danilo", "last_name": "D'Ambrosio", "role": PlayerRole.DF, "age": 35, "rating": 7.1, "market_value": 2000000},
    # More MFs
    {"first_name": "Roberto", "last_name": "Gagliardini", "role": PlayerRole.MF, "age": 29, "rating": 6.9, "market_value": 6000000},
    {"first_name": "Matteo", "last_name": "Pessina", "role": PlayerRole.MF, "age": 26, "rating": 7.3, "market_value": 15000000},
    {"first_name": "Ruslan", "last_name": "Malinovskyi", "role": PlayerRole.MF, "age": 30, "rating": 7.4, "market_value": 10000000},
    {"first_name": "Luis", "last_name": "Alberto", "role": PlayerRole.MF, "age": 31, "rating": 7.8, "market_value": 15000000},
    {"first_name": "Teun", "last_name": "Koopmeiners", "role": PlayerRole.MF, "age": 25, "rating": 7.7, "market_value": 30000000},
    {"first_name": "Matias", "last_name": "Vecino", "role": PlayerRole.MF, "age": 32, "rating": 7.2, "market_value": 5000000},
    {"first_name": "Bryan", "last_name": "Cristante", "role": PlayerRole.MF, "age": 28, "rating": 7.3, "market_value": 12000000},
    {"first_name": "Davide", "last_name": "Frattesi", "role": PlayerRole.MF, "age": 24, "rating": 7.4, "market_value": 25000000},
    # More FWs
    {"first_name": "Tammy", "last_name": "Abraham", "role": PlayerRole.FW, "age": 26, "rating": 7.5, "market_value": 30000000},
    {"first_name": "Giacomo", "last_name": "Raspadori", "role": PlayerRole.FW, "age": 23, "rating": 7.3, "market_value": 25000000},
    {"first_name": "Alexis", "last_name": "Saelemaekers", "role": PlayerRole.FW, "age": 24, "rating": 7.2, "market_value": 12000000},
    {"first_name": "Matteo", "last_name": "Politano", "role": PlayerRole.FW, "age": 30, "rating": 7.6, "market_value": 18000000},
    {"first_name": "Andrea", "last_name": "Belotti", "role": PlayerRole.FW, "age": 30, "rating": 7.3, "market_value": 8000000},
    {"first_name": "Marko", "last_name": "Arnautovic", "role": PlayerRole.FW, "age": 34, "rating": 7.2, "market_value": 4000000},
    {"first_name": "Lorenzo", "last_name": "Pellegrini", "role": PlayerRole.FW, "age": 27, "rating": 7.7, "market_value": 28000000},
]


def generate_complete_player_data(base_data: dict, team_id: str, org_id: str) -> dict:
    """Generate complete player data with all fields."""
    age = base_data.get("age", random.randint(18, 35))
    birth_year = datetime.now().year - age

    player_data = {
        "id": uuid4(),
        "first_name": base_data["first_name"],
        "last_name": base_data["last_name"],
        "date_of_birth": date(birth_year, random.randint(1, 12), random.randint(1, 28)),
        "nationality": base_data.get("nationality", "IT"),
        "role_primary": base_data["role_primary"],
        "dominant_foot": base_data.get("dominant_foot", DominantFoot.RIGHT),

        # Physical data
        "height_cm": base_data.get("height_cm", random.uniform(170, 195)),
        "weight_kg": base_data.get("weight_kg", random.uniform(65, 95)),
        "physical_condition": base_data.get("physical_condition", random.choice(["excellent", "good", "normal"])),
        "injury_prone": random.random() < 0.15,  # 15% chance

        # Tactical attributes
        "tactical_awareness": base_data.get("tactical_awareness", random.randint(50, 90)),
        "positioning": base_data.get("positioning", random.randint(50, 90)),
        "decision_making": base_data.get("decision_making", random.randint(50, 90)),
        "work_rate": base_data.get("work_rate", random.randint(50, 95)),

        # Psychological attributes
        "mental_strength": base_data.get("mental_strength", random.randint(50, 90)),
        "leadership": base_data.get("leadership", random.randint(40, 90)),
        "concentration": base_data.get("concentration", random.randint(50, 90)),
        "adaptability": base_data.get("adaptability", random.randint(50, 90)),

        # Ratings
        "overall_rating": base_data.get("overall_rating", random.uniform(6.0, 8.5)),
        "potential_rating": base_data.get("potential_rating", random.uniform(6.5, 9.0)),
        "form_level": random.uniform(5.0, 8.0),
        "market_value_eur": base_data.get("market_value_eur", random.uniform(1000000, 50000000)),

        # Metadata
        "team_id": team_id,
        "organization_id": org_id,
        "is_active": True,
        "is_injured": random.random() < 0.1,  # 10% injured
        "consent_given": True,
        "medical_clearance": True,
    }

    return player_data


def generate_additional_player(base_data: dict, team_id: str, org_id: str) -> dict:
    """Generate additional player with minimal data."""
    age = base_data.get("age", random.randint(20, 32))
    birth_year = datetime.now().year - age
    rating = base_data.get("rating", 7.0)

    return {
        "id": uuid4(),
        "first_name": base_data["first_name"],
        "last_name": base_data["last_name"],
        "date_of_birth": date(birth_year, random.randint(1, 12), random.randint(1, 28)),
        "nationality": "IT",
        "role_primary": base_data["role"],
        "dominant_foot": DominantFoot.RIGHT,
        "height_cm": random.uniform(170, 190),
        "weight_kg": random.uniform(70, 85),
        "physical_condition": random.choice(["excellent", "good", "normal"]),
        "injury_prone": False,
        "tactical_awareness": int(rating * 10) + random.randint(-5, 5),
        "positioning": int(rating * 10) + random.randint(-5, 5),
        "decision_making": int(rating * 10) + random.randint(-5, 5),
        "work_rate": int(rating * 10) + random.randint(-10, 10),
        "mental_strength": int(rating * 10) + random.randint(-5, 5),
        "leadership": int(rating * 10) + random.randint(-10, 5),
        "concentration": int(rating * 10) + random.randint(-5, 5),
        "adaptability": int(rating * 10) + random.randint(-5, 5),
        "overall_rating": rating,
        "potential_rating": rating + random.uniform(0.0, 1.0),
        "form_level": random.uniform(5.0, 8.0),
        "market_value_eur": base_data.get("market_value", 10000000),
        "team_id": team_id,
        "organization_id": org_id,
        "is_active": True,
        "is_injured": False,
        "consent_given": True,
        "medical_clearance": True,
    }


async def create_training_sessions(
    session: AsyncSession,
    team_id: str,
    org_id: str,
    players: List[Player]
) -> None:
    """Create 10 training sessions with statistics for all players."""

    session_types_data = [
        {"type": SessionType.TECHNICAL, "focus": "passing_accuracy", "intensity": SessionIntensity.HIGH},
        {"type": SessionType.TACTICAL, "focus": "defensive_positioning", "intensity": SessionIntensity.MEDIUM},
        {"type": SessionType.PHYSICAL, "focus": "aerobic_capacity", "intensity": SessionIntensity.HIGH},
        {"type": SessionType.TECHNICAL, "focus": "finishing", "intensity": SessionIntensity.MEDIUM},
        {"type": SessionType.PSYCHOLOGICAL, "focus": "pressure_handling", "intensity": SessionIntensity.LOW},
        {"type": SessionType.TACTICAL, "focus": "attacking_patterns", "intensity": SessionIntensity.MEDIUM},
        {"type": SessionType.PHYSICAL, "focus": "strength_training", "intensity": SessionIntensity.HIGH},
        {"type": SessionType.TECHNICAL, "focus": "dribbling", "intensity": SessionIntensity.MEDIUM},
        {"type": SessionType.TACTICAL, "focus": "set_pieces", "intensity": SessionIntensity.LOW},
        {"type": SessionType.RECOVERY, "focus": "active_recovery", "intensity": SessionIntensity.LOW},
    ]

    for i, session_info in enumerate(session_types_data):
        training_session = TrainingSession(
            id=uuid4(),
            session_date=datetime.now() - timedelta(days=14-i),
            session_type=session_info["type"],
            duration_min=90,
            team_id=team_id,
            focus_area=session_info["focus"],
            intensity=session_info["intensity"],
            description=f"Training session focused on {session_info['focus']}",
            coach_notes="Good session overall, players showed commitment",
            organization_id=org_id,
        )

        session.add(training_session)
        await session.flush()

        # Create training stats for each player
        for player in players:
            # Random but realistic performance
            base_performance = random.randint(5, 9)

            training_stats = PlayerTrainingStats(
                id=uuid4(),
                player_id=player.id,
                training_session_id=training_session.id,
                attendance=random.random() > 0.05,  # 95% attendance
                technical_rating=min(10, max(1, base_performance + random.randint(-1, 2))),
                tactical_execution=min(10, max(1, base_performance + random.randint(-1, 2))),
                physical_performance=min(10, max(1, base_performance + random.randint(-2, 1))),
                mental_focus=min(10, max(1, base_performance + random.randint(-1, 1))),
                passing_accuracy=random.uniform(70, 95),
                shooting_accuracy=random.uniform(60, 90),
                dribbling_success=random.uniform(65, 88),
                first_touch_quality=random.uniform(70, 92),
                defensive_actions=random.randint(5, 20),
                speed_kmh=random.uniform(28, 35),
                endurance_index=random.uniform(70, 95),
                recovery_rate=random.uniform(75, 98),
                distance_covered_m=random.uniform(5000, 8000),
                hi_intensity_runs=random.randint(15, 40),
                sprints_count=random.randint(10, 30),
                aerobic_capacity=random.uniform(50, 75),
                rpe_score=random.randint(4, 8),
                fatigue_level=random.randint(3, 7),
                sleep_quality=random.randint(6, 9),
                coach_feedback="Solid performance, showing improvement",
                areas_to_improve="Continue working on decision making under pressure",
                attitude_rating=min(10, max(1, base_performance + random.randint(-1, 1))),
                teamwork_rating=min(10, max(1, base_performance + random.randint(0, 2))),
                organization_id=org_id,
            )

            session.add(training_stats)

    await session.commit()
    print(f"✅ Created 10 training sessions with stats for {len(players)} players")


async def seed_complete_data():
    """Main function to seed complete data."""
    print("🚀 Starting complete data seed...")

    async for db_session in get_async_session():
        try:
            # Get or create organization
            stmt = select(Organization).limit(1)
            result = await db_session.execute(stmt)
            organization = result.scalar_one_or_none()

            if not organization:
                organization = Organization(
                    id=uuid4(),
                    name="Football Club Platform",
                    is_active=True
                )
                db_session.add(organization)
                await db_session.commit()
                await db_session.refresh(organization)

            org_id = organization.id
            print(f"📋 Using organization: {organization.name}")

            # Get or create team
            stmt = select(Team).where(Team.organization_id == org_id).limit(1)
            result = await db_session.execute(stmt)
            team = result.scalar_one_or_none()

            if not team:
                team = Team(
                    id=uuid4(),
                    name="Serie A All-Stars",
                    category="Senior",
                    organization_id=org_id,
                    is_active=True
                )
                db_session.add(team)
                await db_session.commit()
                await db_session.refresh(team)

            team_id = team.id
            print(f"⚽ Using team: {team.name}")

            # Delete existing players for clean slate
            from app.models.player import Player
            stmt = select(Player).where(Player.team_id == team_id)
            result = await db_session.execute(stmt)
            existing_players = result.scalars().all()

            for player in existing_players:
                await db_session.delete(player)

            await db_session.commit()
            print("🗑️  Cleared existing players")

            # Create main players
            all_players = []
            for player_data in REAL_PLAYERS_DATA:
                complete_data = generate_complete_player_data(player_data, team_id, org_id)
                player = Player(**complete_data)
                db_session.add(player)
                all_players.append(player)

            print(f"✅ Created {len(REAL_PLAYERS_DATA)} main players")

            # Create additional players
            for player_data in ADDITIONAL_PLAYERS:
                complete_data = generate_additional_player(player_data, team_id, org_id)
                player = Player(**complete_data)
                db_session.add(player)
                all_players.append(player)

            print(f"✅ Created {len(ADDITIONAL_PLAYERS)} additional players")

            await db_session.commit()

            # Refresh all players to get IDs
            for player in all_players:
                await db_session.refresh(player)

            print(f"🎯 Total players created: {len(all_players)}")

            # Create training sessions
            await create_training_sessions(db_session, team_id, org_id, all_players)

            print("🎉 Complete data seed finished successfully!")
            print(f"\n📊 Summary:")
            print(f"   - Organization: {organization.name}")
            print(f"   - Team: {team.name}")
            print(f"   - Players: {len(all_players)}")
            print(f"   - Training Sessions: 10")
            print(f"   - Training Stats: {len(all_players) * 10}")

        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            await db_session.rollback()
            raise
        finally:
            await db_session.close()


if __name__ == "__main__":
    asyncio.run(seed_complete_data())
