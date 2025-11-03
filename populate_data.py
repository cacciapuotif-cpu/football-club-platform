"""Script to populate database with sample players and training sessions."""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """Login and get access token."""
    print(">> Logging in...")
    login_data = {
        "email": "admin@football_club_platform.demo",
        "password": "admin123"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("[OK] Logged in successfully!")
            return data["access_token"]
        else:
            print(f"[ERROR] Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return None

def create_season(token, season_data):
    """Create a season."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(f"{BASE_URL}/seasons", json=season_data, headers=headers, timeout=10)
        if response.status_code == 201:
            data = response.json()
            print(f"[OK] Created season: {season_data['name']}")
            return data["id"]
        else:
            print(f"[ERROR] Failed to create season: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return None

def create_team(token, team_data):
    """Create a team."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(f"{BASE_URL}/teams", json=team_data, headers=headers, timeout=10)
        if response.status_code == 201:
            data = response.json()
            print(f"[OK] Created team: {team_data['name']}")
            return data["id"]
        else:
            print(f"[ERROR] Failed to create team: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return None

def create_player(token, player_data):
    """Create a player."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(f"{BASE_URL}/players", json=player_data, headers=headers, timeout=10)
        if response.status_code == 201:
            data = response.json()
            print(f"[OK] Created player: {player_data['first_name']} {player_data['last_name']}")
            return data["id"]
        else:
            print(f"[ERROR] Failed to create player: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return None

def create_training_session(token, session_data):
    """Create a training session."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(f"{BASE_URL}/sessions", json=session_data, headers=headers, timeout=10)
        if response.status_code == 201:
            data = response.json()
            return data["id"]
        else:
            print(f"[ERROR] Failed to create session: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return None

def calculate_birth_date(age):
    """Calculate birth date from age."""
    today = datetime.now()
    birth_year = today.year - age
    return datetime(birth_year, 1, 15).strftime("%Y-%m-%d")

def main():
    """Main function."""
    print("=" * 60)
    print("Football Club Platform - Populate Database with Sample Data")
    print("=" * 60)
    print()

    # Login
    token = login()
    if not token:
        print("\n[ERROR] Failed to login. Exiting.")
        return

    print()
    print("=" * 60)
    print("Creating Season and Team")
    print("=" * 60)

    # Create a season first
    current_year = datetime.now().year
    season_data = {
        "name": f"Stagione {current_year}/{current_year+1}",
        "start_date": f"{current_year}-09-01",
        "end_date": f"{current_year+1}-06-30",
        "is_active": True
    }

    season_id = create_season(token, season_data)
    if not season_id:
        print("\n[ERROR] Failed to create season. Exiting.")
        return

    # Create a team
    team_data = {
        "name": "Juniores U19",
        "category": "U19",
        "season_id": season_id
    }

    team_id = create_team(token, team_data)
    if not team_id:
        print("\n[ERROR] Failed to create team. Exiting.")
        return

    print()
    print("=" * 60)
    print("Creating Players")
    print("=" * 60)

    # Create Player 1 (16 years old)
    player1_data = {
        "first_name": "Marco",
        "last_name": "Rossi",
        "date_of_birth": calculate_birth_date(16),
        "place_of_birth": "Milano",
        "nationality": "IT",
        "role_primary": "FW",
        "dominant_foot": "RIGHT",
        "jersey_number": 10,
        "height_cm": 175.0,
        "weight_kg": 68.0,
        "is_active": True,
        "is_minor": True,
        "guardian_name": "Giuseppe Rossi",
        "guardian_email": "giuseppe.rossi@email.it",
        "guardian_phone": "+39 320 1234567",
        "consent_given": True,
        "consent_date": datetime.now().isoformat()
    }

    player1_id = create_player(token, player1_data)

    # Create Player 2 (18 years old)
    player2_data = {
        "first_name": "Luca",
        "last_name": "Bianchi",
        "date_of_birth": calculate_birth_date(18),
        "place_of_birth": "Roma",
        "nationality": "IT",
        "role_primary": "MF",
        "dominant_foot": "LEFT",
        "jersey_number": 8,
        "height_cm": 180.0,
        "weight_kg": 73.0,
        "is_active": True,
        "is_minor": False,
        "email": "luca.bianchi@email.it",
        "phone": "+39 340 7654321",
        "consent_given": True,
        "consent_date": datetime.now().isoformat()
    }

    player2_id = create_player(token, player2_data)

    if not player1_id or not player2_id:
        print("\n[ERROR] Failed to create players. Exiting.")
        return

    print()
    print("=" * 60)
    print("Creating Training Sessions")
    print("=" * 60)

    # Session types and focuses
    session_types = ["TRAINING", "TRAINING", "TRAINING", "GYM", "TACTICAL", "TRAINING", "FRIENDLY", "RECOVERY", "TRAINING", "TRAINING"]
    focuses = [
        "Lavoro tecnico sui passaggi",
        "Esercizi di resistenza e velocità",
        "Tattica difensiva e pressing",
        "Potenziamento muscolare",
        "Schema 4-3-3 e movimenti offensivi",
        "Possesso palla e transizioni",
        "Partita amichevole vs Juniores",
        "Recupero attivo e stretching",
        "Tiri in porta e finalizzazione",
        "Gioco posizionale e pressing alto"
    ]

    intensities = [7, 8, 6, 9, 5, 7, 8, 3, 8, 7]
    durations = [90, 90, 75, 60, 90, 90, 90, 45, 75, 90]

    # Create 10 sessions for Player 1
    print(f"\nCreating 10 sessions for {player1_data['first_name']} {player1_data['last_name']}...")
    for i in range(10):
        session_date = datetime.now() - timedelta(days=(9 - i) * 2)

        session_data = {
            "session_date": session_date.isoformat(),
            "session_type": session_types[i],
            "duration_min": durations[i],
            "team_id": team_id,
            "focus": focuses[i],
            "planned_intensity": intensities[i],
            "description": f"Sessione {i+1}: {focuses[i]}"
        }

        session_id = create_training_session(token, session_data)
        if session_id:
            print(f"  [OK] Session {i+1}/10 created - {focuses[i]}")
        else:
            print(f"  [FAIL] Session {i+1}/10 failed")

    # Create 10 sessions for Player 2
    print(f"\nCreating 10 sessions for {player2_data['first_name']} {player2_data['last_name']}...")
    for i in range(10):
        session_date = datetime.now() - timedelta(days=(9 - i) * 2)

        session_data = {
            "session_date": session_date.isoformat(),
            "session_type": session_types[i],
            "duration_min": durations[i],
            "team_id": team_id,
            "focus": focuses[i],
            "planned_intensity": intensities[i],
            "description": f"Sessione {i+1}: {focuses[i]}"
        }

        session_id = create_training_session(token, session_data)
        if session_id:
            print(f"  [OK] Session {i+1}/10 created - {focuses[i]}")
        else:
            print(f"  [FAIL] Session {i+1}/10 failed")

    print()
    print("=" * 60)
    print("[SUCCESS] Database populated successfully!")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  - Created 2 players:")
    print(f"    • Marco Rossi (16 anni) - Attaccante #10")
    print(f"    • Luca Bianchi (18 anni) - Centrocampista #8")
    print(f"  - Created 20 training sessions total (10 per player)")
    print()
    print("You can now view them at:")
    print("  - Players: http://localhost:3000/players")
    print("  - Sessions: http://localhost:3000/sessions")
    print("=" * 60)

if __name__ == "__main__":
    main()
