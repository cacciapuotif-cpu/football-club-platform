import requests
import json
from datetime import datetime, timedelta

base_url = "http://localhost:8000/api/v1"

# Prima registriamo un utente
import random
import string

# Genera email e slug unici per evitare conflitti
random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

print("=== Registrazione utente ===")
signup_data = {
    "email": f"admin{random_suffix}@football_club_platform.com",
    "password": "admin123",
    "full_name": "Admin Football Club Platform",
    "organization_name": f"Football Club Platform Club {random_suffix}",
    "organization_slug": f"football_club_platform-club-{random_suffix}"
}
print(f"Tentativo signup con email: {signup_data['email']}")

try:
    response = requests.post(f"{base_url}/auth/signup", json=signup_data)
    if response.status_code == 201:
        token_data = response.json()
        access_token = token_data["access_token"]
        print(f"[OK] Utente registrato! Token ricevuto")
        print(f"Email: {signup_data['email']}")
        print(f"Password: {signup_data['password']}")
        print(f"Organization: {signup_data['organization_name']}")
    else:
        print(f"[ERROR] Registrazione fallita: {response.status_code}")
        print(f"Dettagli: {response.text}")
        exit(1)
except Exception as e:
    print(f"[ERROR] Errore autenticazione: {e}")
    exit(1)

# Headers con token
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Crea giocatori di test
players = [
    {
        "first_name": "Mario",
        "last_name": "Rossi",
        "date_of_birth": "2000-05-15",
        "place_of_birth": "Roma",
        "nationality": "IT",
        "email": "mario.rossi@example.com",
        "phone": "+39 333 1234567",
        "role_primary": "FW",
        "dominant_foot": "RIGHT",
        "dominant_arm": "RIGHT",
        "jersey_number": 10,
        "height_cm": 180.0,
        "weight_kg": 75.0,
        "is_active": True
    },
    {
        "first_name": "Luigi",
        "last_name": "Bianchi",
        "date_of_birth": "1998-08-20",
        "place_of_birth": "Milano",
        "nationality": "IT",
        "email": "luigi.bianchi@example.com",
        "phone": "+39 333 7654321",
        "role_primary": "MF",
        "dominant_foot": "LEFT",
        "dominant_arm": "RIGHT",
        "jersey_number": 8,
        "height_cm": 175.0,
        "weight_kg": 72.0,
        "is_active": True
    },
    {
        "first_name": "Giuseppe",
        "last_name": "Verdi",
        "date_of_birth": "2001-03-10",
        "place_of_birth": "Napoli",
        "nationality": "IT",
        "email": "giuseppe.verdi@example.com",
        "role_primary": "DF",
        "dominant_foot": "RIGHT",
        "dominant_arm": "RIGHT",
        "jersey_number": 5,
        "height_cm": 182.0,
        "weight_kg": 78.0,
        "is_active": True
    }
]

player_ids = []

print("\nCreazione giocatori...")
for player in players:
    try:
        response = requests.post(f"{base_url}/players", json=player, headers=headers)
        if response.status_code == 201:
            player_data = response.json()
            player_ids.append(player_data["id"])
            print(f"[OK] Creato: {player['first_name']} {player['last_name']} (ID: {player_data['id']})")
        else:
            print(f"[ERROR] Errore creazione {player['first_name']}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERROR] Errore: {e}")

# Crea dati wellness per ogni giocatore
print("\nCreazione dati wellness...")
for player_id in player_ids:
    for days_ago in range(7):
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        wellness_data = {
            "date": date,
            "player_id": player_id,
            "sleep_hours": 7.0 + (days_ago % 3),
            "sleep_quality": 3 + (days_ago % 3),
            "fatigue_rating": 2 + (days_ago % 4),
            "stress_rating": 2 + ((days_ago + 1) % 4),
            "mood_rating": 3 + (days_ago % 3),
            "motivation_rating": 3 + ((days_ago + 2) % 3),
            "srpe": 5 + (days_ago % 5),
            "session_duration_min": 90,
            "training_load": (5 + (days_ago % 5)) * 90
        }
        try:
            response = requests.post(f"{base_url}/wellness", json=wellness_data, headers=headers)
            if response.status_code == 201:
                print(f"[OK] Wellness creato per player {player_id[:8]}... del {date}")
            else:
                print(f"[ERROR] Errore wellness: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Errore: {e}")

print(f"\n[DONE] Completato! Creati {len(player_ids)} giocatori con dati wellness.")
print(f"Puoi ora vedere i giocatori su: http://localhost:3000/players")
print(f"E aprire la dashboard di un giocatore cliccando su 'Dashboard'")
