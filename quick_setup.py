"""Quick setup script to initialize Football Club Platform with demo data via API."""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def create_organization_and_owner():
    """Create organization and owner user via signup."""
    print(">> Creating organization and owner...")

    signup_data = {
        "email": "admin@football_club_platform.demo",
        "password": "admin123",
        "full_name": "Admin User",
        "organization_name": "ASD Calcio Demo",
        "organization_slug": "asd-calcio-demo"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data, timeout=10)
        if response.status_code == 201:
            data = response.json()
            print(f"[OK] Organization created successfully!")
            print(f"[OK] Admin user: {signup_data['email']} / {signup_data['password']}")
            return data["access_token"]
        elif response.status_code == 400:
            # Organization might already exist, try login
            print("[WARN] Organization already exists, trying login...")
            login_data = {
                "email": signup_data["email"],
                "password": signup_data["password"]
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Logged in as admin!")
                return data["access_token"]

        print(f"[ERROR] {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        print("[WARN] Make sure the backend is running on http://localhost:8000")
        return None

def main():
    """Main setup function."""
    print("=" * 60)
    print("Football Club Platform Quick Setup")
    print("=" * 60)
    print()

    # Create organization and get token
    token = create_organization_and_owner()

    if token:
        print()
        print("=" * 60)
        print("[SUCCESS] Setup Complete!")
        print("=" * 60)
        print()
        print("You can now login with:")
        print("   Email:    admin@football_club_platform.demo")
        print("   Password: admin123")
        print()
        print("Access the application:")
        print("   Frontend:  http://localhost:3000")
        print("   API Docs:  http://localhost:8000/docs")
        print()
        print("Next steps:")
        print("   1. Login with the credentials above")
        print("   2. Create teams and players")
        print("   3. Add training sessions and wellness data")
        print("=" * 60)
    else:
        print()
        print("[ERROR] Setup failed! Please check:")
        print("   1. Backend is running: docker ps | grep football_club_platform-backend")
        print("   2. Database is accessible")
        print("   3. Check backend logs: docker logs football_club_platform-backend")

if __name__ == "__main__":
    main()
