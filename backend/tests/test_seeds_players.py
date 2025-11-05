"""
Player Seeding Tests

Tests idempotent player seeding with robust natural key strategies:
1. external_id (primary)
2. (organization_id, team_id, jersey_number) (secondary)
3. (organization_id, team_id, last_name, first_name, date_of_birth) (fallback)

Validates:
- Idempotence (multiple runs produce same result)
- FK resolution (organization and team lookups)
- Enum parsing (PlayerRole, DominantFoot, DominantArm)
- Unique constraint enforcement
- Minor player guardian info
"""

import pytest
from datetime import date
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.player import Player, PlayerRole, DominantFoot, DominantArm
from app.models.organization import Organization
from app.models.team import Team
from seeds.steps.05_players import seed as seed_players, _resolve_org, _resolve_team


class TestPlayerSeedIdempotence:
    """Test idempotent player seeding."""

    def test_seed_players_idempotent_external_id(self, db_session: Session):
        """Test idempotence using external_id as natural key."""
        # Create organization first
        org = Organization(
            slug="test-fc",
            name="Test FC",
            country="IT",
            quota_players=100,
            quota_storage_gb=10,
        )
        db_session.add(org)
        db_session.flush()

        # Create team
        team = Team(
            organization_id=org.id,
            name="Prima Squadra",
            category="U19",
        )
        db_session.add(team)
        db_session.flush()

        # Player data with external_id
        player_data = [
            {
                "external_id": "test-fc-ps-10",
                "organization_slug": "test-fc",
                "team_name": "Prima Squadra",
                "first_name": "Marco",
                "last_name": "Rossi",
                "date_of_birth": "2008-05-15",
                "nationality": "IT",
                "role_primary": "FW",
                "dominant_foot": "RIGHT",
                "dominant_arm": "RIGHT",
                "jersey_number": 10,
                "tactical_awareness": 75,
                "positioning": 70,
                "decision_making": 68,
                "work_rate": 80,
                "mental_strength": 72,
                "leadership": 65,
                "concentration": 70,
                "adaptability": 75,
            }
        ]

        # First run
        result1 = seed_players(db_session, player_data)
        db_session.commit()

        assert result1["Players"]["inserted"] == 1
        assert result1["Players"]["updated"] == 0
        assert result1["Players"]["skipped"] == 0

        # Verify player created
        player = db_session.execute(
            select(Player).where(Player.external_id == "test-fc-ps-10")
        ).scalar_one()

        assert player.first_name == "Marco"
        assert player.last_name == "Rossi"
        assert player.jersey_number == 10
        assert player.role_primary == PlayerRole.FW

        # Second run with same data (should skip)
        result2 = seed_players(db_session, player_data)
        db_session.commit()

        assert result2["Players"]["inserted"] == 0
        assert result2["Players"]["updated"] == 0
        assert result2["Players"]["skipped"] == 1

        # Third run with updated tactical score (should update)
        player_data[0]["tactical_awareness"] = 85
        result3 = seed_players(db_session, player_data)
        db_session.commit()

        assert result3["Players"]["inserted"] == 0
        assert result3["Players"]["updated"] == 1
        assert result3["Players"]["skipped"] == 0

        # Verify update
        player = db_session.execute(
            select(Player).where(Player.external_id == "test-fc-ps-10")
        ).scalar_one()

        assert player.tactical_awareness == 85

        # Verify only one player exists
        count = db_session.execute(
            text("SELECT COUNT(*) FROM players WHERE external_id = :ext_id"),
            {"ext_id": "test-fc-ps-10"},
        ).scalar()

        assert count == 1

    def test_seed_players_idempotent_composite_key(self, db_session: Session):
        """Test idempotence using (org, team, jersey_number) composite key."""
        # Create organization and team
        org = Organization(
            slug="staging-fc",
            name="Staging FC",
            country="IT",
            quota_players=100,
            quota_storage_gb=10,
        )
        db_session.add(org)
        db_session.flush()

        team = Team(
            organization_id=org.id,
            name="Primavera",
            category="U17",
        )
        db_session.add(team)
        db_session.flush()

        # Player without external_id (uses composite key)
        player_data = [
            {
                "organization_slug": "staging-fc",
                "team_name": "Primavera",
                "first_name": "Luca",
                "last_name": "Bianchi",
                "date_of_birth": "2007-03-10",
                "nationality": "IT",
                "role_primary": "MF",
                "dominant_foot": "LEFT",
                "dominant_arm": "LEFT",
                "jersey_number": 8,
                "tactical_awareness": 60,
                "positioning": 62,
                "decision_making": 58,
                "work_rate": 70,
                "mental_strength": 55,
                "leadership": 50,
                "concentration": 60,
                "adaptability": 65,
            }
        ]

        # First run
        result1 = seed_players(db_session, player_data)
        db_session.commit()

        assert result1["Players"]["inserted"] == 1

        # Second run (should skip)
        result2 = seed_players(db_session, player_data)
        db_session.commit()

        assert result2["Players"]["inserted"] == 0
        assert result2["Players"]["skipped"] == 1

        # Verify only one player
        count = db_session.execute(
            text(
                "SELECT COUNT(*) FROM players WHERE organization_id = :org_id AND jersey_number = :jersey"
            ),
            {"org_id": str(org.id), "jersey": 8},
        ).scalar()

        assert count == 1

    def test_seed_players_idempotent_identity_fallback(self, db_session: Session):
        """Test idempotence using identity (name + dob) fallback."""
        # Create organization and team
        org = Organization(
            slug="demo-fc",
            name="Demo FC",
            country="IT",
            quota_players=100,
            quota_storage_gb=10,
        )
        db_session.add(org)
        db_session.flush()

        team = Team(
            organization_id=org.id,
            name="Giovanissimi",
            category="U15",
        )
        db_session.add(team)
        db_session.flush()

        # Player without external_id AND without jersey_number (uses identity fallback)
        player_data = [
            {
                "organization_slug": "demo-fc",
                "team_name": "Giovanissimi",
                "first_name": "Alessandro",
                "last_name": "Verdi",
                "date_of_birth": "2009-11-20",
                "nationality": "IT",
                "role_primary": "DF",
                "dominant_foot": "RIGHT",
                "dominant_arm": "RIGHT",
                # NO jersey_number - uses identity fallback
                "tactical_awareness": 50,
                "positioning": 52,
                "decision_making": 48,
                "work_rate": 60,
                "mental_strength": 50,
                "leadership": 45,
                "concentration": 55,
                "adaptability": 50,
            }
        ]

        # First run
        result1 = seed_players(db_session, player_data)
        db_session.commit()

        assert result1["Players"]["inserted"] == 1

        # Second run (should skip by identity)
        result2 = seed_players(db_session, player_data)
        db_session.commit()

        assert result2["Players"]["inserted"] == 0
        assert result2["Players"]["skipped"] == 1

        # Verify player exists
        player = db_session.execute(
            select(Player).where(
                Player.first_name == "Alessandro",
                Player.last_name == "Verdi",
                Player.date_of_birth == date(2009, 11, 20),
            )
        ).scalar_one()

        assert player.jersey_number is None  # No jersey assigned
        assert player.role_primary == PlayerRole.DF


class TestPlayerSeedFKResolution:
    """Test FK resolution for organizations and teams."""

    def test_resolve_org_success(self, db_session: Session):
        """Test successful organization resolution by slug."""
        org = Organization(
            slug="fk-test-fc",
            name="FK Test FC",
            country="IT",
            quota_players=100,
            quota_storage_gb=10,
        )
        db_session.add(org)
        db_session.flush()

        resolved = _resolve_org(db_session, "fk-test-fc")

        assert resolved is not None
        assert resolved["slug"] == "fk-test-fc"
        assert resolved["name"] == "FK Test FC"
        assert str(resolved["id"]) == str(org.id)

    def test_resolve_org_not_found(self, db_session: Session):
        """Test organization resolution with non-existent slug."""
        resolved = _resolve_org(db_session, "nonexistent-fc")

        assert resolved is None

    def test_resolve_team_by_name(self, db_session: Session):
        """Test team resolution by name."""
        org = Organization(
            slug="team-test-fc",
            name="Team Test FC",
            country="IT",
            quota_players=100,
            quota_storage_gb=10,
        )
        db_session.add(org)
        db_session.flush()

        team = Team(
            organization_id=org.id,
            name="Under 17",
            category="U17",
        )
        db_session.add(team)
        db_session.flush()

        resolved = _resolve_team(db_session, str(org.id), "Under 17", None)

        assert resolved is not None
        assert resolved["name"] == "Under 17"
        assert resolved["category"] == "U17"
        assert str(resolved["id"]) == str(team.id)

    def test_resolve_team_by_code(self, db_session: Session):
        """Test team resolution by code (category)."""
        org = Organization(
            slug="code-test-fc",
            name="Code Test FC",
            country="IT",
            quota_players=100,
            quota_storage_gb=10,
        )
        db_session.add(org)
        db_session.flush()

        team = Team(
            organization_id=org.id,
            name="Juniores",
            category="U19",
        )
        db_session.add(team)
        db_session.flush()

        resolved = _resolve_team(db_session, str(org.id), None, "U19")

        assert resolved is not None
        assert resolved["category"] == "U19"

    def test_resolve_team_not_found(self, db_session: Session):
        """Test team resolution with non-existent team."""
        org = Organization(
            slug="empty-fc",
            name="Empty FC",
            country="IT",
            quota_players=100,
            quota_storage_gb=10,
        )
        db_session.add(org)
        db_session.flush()

        resolved = _resolve_team(db_session, str(org.id), "Nonexistent Team", None)

        assert resolved is None


class TestPlayerSeedEnumParsing:
    """Test enum parsing for PlayerRole, DominantFoot, DominantArm."""

    def test_seed_player_with_all_enums(self, db_session: Session):
        """Test player seeding with all enum fields."""
        # Create dependencies
        org = Organization(
            slug="enum-fc",
            name="Enum FC",
            country="IT",
            quota_players=100,
            quota_storage_gb=10,
        )
        db_session.add(org)
        db_session.flush()

        team = Team(
            organization_id=org.id,
            name="First Team",
            category="Senior",
        )
        db_session.add(team)
        db_session.flush()

        player_data = [
            {
                "external_id": "enum-test-1",
                "organization_slug": "enum-fc",
                "team_name": "First Team",
                "first_name": "Enum",
                "last_name": "Tester",
                "date_of_birth": "2000-01-01",
                "nationality": "IT",
                "role_primary": "GK",
                "role_secondary": "DF",
                "dominant_foot": "BOTH",
                "dominant_arm": "LEFT",
                "jersey_number": 1,
                "tactical_awareness": 80,
                "positioning": 85,
                "decision_making": 75,
                "work_rate": 60,
                "mental_strength": 90,
                "leadership": 95,
                "concentration": 92,
                "adaptability": 70,
            }
        ]

        result = seed_players(db_session, player_data)
        db_session.commit()

        assert result["Players"]["inserted"] == 1

        # Verify enums were parsed correctly
        player = db_session.execute(
            select(Player).where(Player.external_id == "enum-test-1")
        ).scalar_one()

        assert player.role_primary == PlayerRole.GK
        assert player.role_secondary == PlayerRole.DF
        assert player.dominant_foot == DominantFoot.BOTH
        assert player.dominant_arm == DominantArm.LEFT


class TestPlayerSeedMinorGuardian:
    """Test minor player with guardian information."""

    def test_seed_minor_with_guardian(self, db_session: Session):
        """Test seeding minor player with guardian info."""
        # Create dependencies
        org = Organization(
            slug="minor-fc",
            name="Minor FC",
            country="IT",
            quota_players=100,
            quota_storage_gb=10,
        )
        db_session.add(org)
        db_session.flush()

        team = Team(
            organization_id=org.id,
            name="Youth Team",
            category="U17",
        )
        db_session.add(team)
        db_session.flush()

        player_data = [
            {
                "external_id": "minor-1",
                "organization_slug": "minor-fc",
                "team_name": "Youth Team",
                "first_name": "Giovane",
                "last_name": "Promessa",
                "date_of_birth": "2008-06-15",
                "nationality": "IT",
                "role_primary": "FW",
                "dominant_foot": "RIGHT",
                "dominant_arm": "RIGHT",
                "jersey_number": 9,
                "is_minor": True,
                "guardian_name": "Maria Promessa",
                "guardian_email": "maria.promessa@example.com",
                "guardian_phone": "+39 333 1234567",
                "tactical_awareness": 65,
                "positioning": 70,
                "decision_making": 60,
                "work_rate": 85,
                "mental_strength": 60,
                "leadership": 50,
                "concentration": 65,
                "adaptability": 75,
            }
        ]

        result = seed_players(db_session, player_data)
        db_session.commit()

        assert result["Players"]["inserted"] == 1

        # Verify guardian info
        player = db_session.execute(
            select(Player).where(Player.external_id == "minor-1")
        ).scalar_one()

        assert player.is_minor is True
        assert player.guardian_name == "Maria Promessa"
        assert player.guardian_email == "maria.promessa@example.com"
        assert player.guardian_phone == "+39 333 1234567"


class TestPlayerSeedErrorHandling:
    """Test error handling and validation."""

    def test_seed_players_missing_required_fields(self, db_session: Session):
        """Test seeding with missing required fields."""
        player_data = [
            {
                # Missing first_name, last_name, organization_slug
                "date_of_birth": "2000-01-01",
            }
        ]

        result = seed_players(db_session, player_data)

        # Should skip due to validation error
        assert result["Players"]["inserted"] == 0
        assert result["Players"]["skipped"] >= 1

    def test_seed_players_nonexistent_organization(self, db_session: Session):
        """Test seeding with non-existent organization."""
        player_data = [
            {
                "organization_slug": "does-not-exist",
                "team_name": "Some Team",
                "first_name": "Test",
                "last_name": "Player",
                "date_of_birth": "2000-01-01",
                "nationality": "IT",
                "role_primary": "MF",
                "dominant_foot": "RIGHT",
                "dominant_arm": "RIGHT",
                "jersey_number": 5,
            }
        ]

        result = seed_players(db_session, player_data)

        # Should skip due to org not found
        assert result["Players"]["inserted"] == 0
        assert result["Players"]["skipped"] >= 1

    def test_seed_players_nonexistent_team(self, db_session: Session):
        """Test seeding with non-existent team."""
        # Create organization but not team
        org = Organization(
            slug="no-team-fc",
            name="No Team FC",
            country="IT",
            quota_players=100,
            quota_storage_gb=10,
        )
        db_session.add(org)
        db_session.flush()

        player_data = [
            {
                "organization_slug": "no-team-fc",
                "team_name": "Nonexistent Team",
                "first_name": "Test",
                "last_name": "Player",
                "date_of_birth": "2000-01-01",
                "nationality": "IT",
                "role_primary": "MF",
                "dominant_foot": "RIGHT",
                "dominant_arm": "RIGHT",
                "jersey_number": 7,
            }
        ]

        result = seed_players(db_session, player_data)

        # Should skip due to team not found
        assert result["Players"]["inserted"] == 0
        assert result["Players"]["skipped"] >= 1
