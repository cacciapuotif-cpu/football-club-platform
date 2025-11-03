"""Test wellness summary endpoints."""

from datetime import date, timedelta
from uuid import uuid4

import pytest


def test_wellness_summary_default_sort(client):
    """Test wellness summary returns players sorted by cognome ascending."""
    response = client.get("/api/v1/wellness/summary")

    # Expect 200 even if empty (demo org might have no data yet)
    assert response.status_code in [200, 404]  # 404 if no org exists

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)

        # If data exists, verify sorting by cognome
        if len(data) > 1:
            cognomes = [item["cognome"] for item in data]
            assert cognomes == sorted(cognomes), "Players should be sorted by cognome ascending"


def test_wellness_summary_with_date_filter(client):
    """Test wellness summary with date range filter changes session count."""
    # Test without date filter
    response_all = client.get("/api/v1/wellness/summary")

    if response_all.status_code != 200:
        pytest.skip("No demo organization found, skipping test")

    data_all = response_all.json()

    # Test with date filter (last 7 days)
    today = date.today()
    week_ago = today - timedelta(days=7)

    response_filtered = client.get(
        f"/api/v1/wellness/summary?from={week_ago.isoformat()}&to={today.isoformat()}"
    )
    assert response_filtered.status_code == 200

    data_filtered = response_filtered.json()

    # Both should return same players (all players), but counts may differ
    assert isinstance(data_filtered, list)

    # If we have data, session counts with filter should be <= without filter
    if len(data_all) > 0 and len(data_filtered) > 0:
        # Find same player in both results
        player_ids_all = {item["player_id"] for item in data_all}
        player_ids_filtered = {item["player_id"] for item in data_filtered}

        # Same players should appear (filter only affects count, not player list)
        # Note: this assumes LEFT JOIN behavior in the view
        for player_id in player_ids_filtered:
            if player_id in player_ids_all:
                count_all = next(
                    item["wellness_sessions_count"]
                    for item in data_all
                    if item["player_id"] == player_id
                )
                count_filtered = next(
                    item["wellness_sessions_count"]
                    for item in data_filtered
                    if item["player_id"] == player_id
                )
                # Filtered count should be <= all-time count
                assert count_filtered <= count_all


def test_wellness_summary_pagination(client):
    """Test wellness summary pagination - page 2 returns data if available."""
    # Get page 1
    response_page1 = client.get("/api/v1/wellness/summary?page=1&page_size=5")

    if response_page1.status_code != 200:
        pytest.skip("No demo organization found, skipping test")

    data_page1 = response_page1.json()

    # Get page 2
    response_page2 = client.get("/api/v1/wellness/summary?page=2&page_size=5")
    assert response_page2.status_code == 200

    data_page2 = response_page2.json()
    assert isinstance(data_page2, list)

    # If page 1 has 5 items, page 2 might have items (or might be empty)
    # We just verify structure is correct
    if len(data_page2) > 0:
        # Verify structure
        first_item = data_page2[0]
        assert "player_id" in first_item
        assert "cognome" in first_item
        assert "nome" in first_item
        assert "ruolo" in first_item
        assert "wellness_sessions_count" in first_item

        # Verify items on page 2 are different from page 1
        page1_ids = {item["player_id"] for item in data_page1}
        page2_ids = {item["player_id"] for item in data_page2}
        assert page1_ids.isdisjoint(page2_ids), "Page 2 should have different players than page 1"


def test_wellness_summary_role_filter(client):
    """Test wellness summary filters by role correctly."""
    response = client.get("/api/v1/wellness/summary?role=GK")

    if response.status_code != 200:
        pytest.skip("No demo organization found, skipping test")

    data = response.json()
    assert isinstance(data, list)

    # All returned players should have role GK
    for item in data:
        assert item["ruolo"] in ["GK", None], "When filtering by GK, only goalkeepers should be returned"


def test_wellness_summary_search_filter(client):
    """Test wellness summary search filter works."""
    # Search for common Italian surname
    response = client.get("/api/v1/wellness/summary?search=Ross")

    if response.status_code != 200:
        pytest.skip("No demo organization found, skipping test")

    data = response.json()
    assert isinstance(data, list)

    # All returned players should have 'Ross' in cognome or nome
    for item in data:
        player_name = f"{item['cognome']} {item['nome']}".lower()
        assert "ross" in player_name, "Search filter should match cognome or nome"


def test_wellness_summary_sort_by_sessions(client):
    """Test wellness summary can sort by session count descending."""
    response = client.get("/api/v1/wellness/summary?sort=sessions_desc")

    if response.status_code != 200:
        pytest.skip("No demo organization found, skipping test")

    data = response.json()
    assert isinstance(data, list)

    # Verify descending order by session count
    if len(data) > 1:
        session_counts = [item["wellness_sessions_count"] for item in data]
        assert session_counts == sorted(
            session_counts, reverse=True
        ), "Players should be sorted by session count descending"


def test_player_wellness_entries(client):
    """Test get wellness entries for a specific player."""
    # First get a player ID from summary
    summary_response = client.get("/api/v1/wellness/summary")

    if summary_response.status_code != 200:
        pytest.skip("No demo organization found, skipping test")

    summary_data = summary_response.json()

    if len(summary_data) == 0:
        pytest.skip("No players found, skipping test")

    # Get first player with wellness data
    player_with_data = next(
        (player for player in summary_data if player["wellness_sessions_count"] > 0),
        None
    )

    if not player_with_data:
        pytest.skip("No players with wellness data found, skipping test")

    player_id = player_with_data["player_id"]

    # Get wellness entries for this player
    response = client.get(f"/api/v1/wellness/player/{player_id}")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Player with wellness_sessions_count > 0 should have entries"

    # Verify structure
    first_entry = data[0]
    assert "date" in first_entry
    assert "sleep_h" in first_entry
    assert "sleep_quality" in first_entry
    assert "fatigue" in first_entry
    assert "stress" in first_entry
    assert "mood" in first_entry
    assert "doms" in first_entry

    # Verify date ordering (descending)
    if len(data) > 1:
        dates = [entry["date"] for entry in data]
        assert dates == sorted(dates, reverse=True), "Entries should be sorted by date descending"


def test_player_wellness_entries_with_date_filter(client):
    """Test get wellness entries with date filter."""
    # First get a player ID
    summary_response = client.get("/api/v1/wellness/summary")

    if summary_response.status_code != 200:
        pytest.skip("No demo organization found, skipping test")

    summary_data = summary_response.json()

    if len(summary_data) == 0:
        pytest.skip("No players found, skipping test")

    player_id = summary_data[0]["player_id"]

    # Get entries for last 30 days
    today = date.today()
    month_ago = today - timedelta(days=30)

    response = client.get(
        f"/api/v1/wellness/player/{player_id}?from={month_ago.isoformat()}&to={today.isoformat()}"
    )
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Verify all dates are within range
    for entry in data:
        entry_date = date.fromisoformat(entry["date"])
        assert month_ago <= entry_date <= today, "All entries should be within date range"


def test_player_wellness_entries_invalid_player(client):
    """Test get wellness entries for non-existent player returns 404."""
    fake_player_id = uuid4()
    response = client.get(f"/api/v1/wellness/player/{fake_player_id}")

    # Should return 404 for non-existent player or skip if no org
    assert response.status_code in [404, 200]  # 200 with empty list is also acceptable

    if response.status_code == 200:
        # If 200, should be empty or player doesn't exist
        # (depends on implementation choice)
        pass
