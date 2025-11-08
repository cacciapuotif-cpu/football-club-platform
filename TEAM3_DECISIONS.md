# Team 3 - Production Hardening - Decision Log

**Branch**: `feature/arch-mvp-t3`
**Base**: `main` (merged Team 1 + Team 2 changes)
**Objective**: Remove mock implementations, implement real data flows, achieve DEMO_10×10 compliance

---

## Overview

Team 3 focused on production hardening by:
1. Removing all mock/stub implementations from Team 2
2. Implementing real database-backed data flows
3. Fixing seed system issues to support DEMO_10×10 compliance
4. Ensuring all endpoints return real data

---

## Key Decisions

### 1. **Removed Mock Fallback from Sessions Endpoint**

**Issue**: Team 2 had added a mock fallback that returned fake training sessions when filtering by `player_id` and no sessions were found in the database.

**Decision**: Completely removed the mock fallback logic and implemented proper JOIN with `PlayerSession` table.

**Implementation**:
- File: `backend/app/routers/sessions.py:72-103`
- Added proper SQLAlchemy JOIN query:
  ```python
  if player_id:
      from app.models.player_session import PlayerSession
      query = (
          select(TrainingSession)
          .join(PlayerSession, TrainingSession.id == PlayerSession.session_id)
          .where(
              TrainingSession.organization_id == org_id,
              PlayerSession.player_id == player_id
          )
      )
  ```

**Rationale**: Production systems must never return mock data. Real JOIN ensures data integrity and proper relationships.

---

### 2. **Fixed YAML Key Naming Convention**

**Issue**: Seed system uses hyphen-separated keys (`06-training-sessions`) but YAML had underscore-separated keys (`06-training_sessions`).

**Decision**: Updated `demo.yaml` to use hyphen-separated keys to match seed runner convention.

**Files Changed**:
- `backend/seeds/datasets/demo.yaml:372` (changed `06-training_sessions:` → `06-training-sessions:`)

**Rationale**: The seed runner does `step_name.replace("_", "-")` to look up YAML keys, so keys must use hyphens.

---

### 3. **Removed `session_name` Field Requirement**

**Issue**: Seed step for training sessions tried to use a `session_name` field that doesn't exist in the `TrainingSession` model.

**Decision**: Removed session_name from model requirements, used existing `focus` field instead.

**Implementation**:
- File: `backend/seeds/steps/06_training_sessions.py:77-89`
- Changed to use `focus` field (maps to session_name from YAML for backward compatibility)
- Check for duplicates by `(organization_id, team_id, session_date)` instead

**Rationale**: Avoid schema changes in Team 3. Use existing fields creatively rather than adding new columns.

---

### 4. **Fixed Intensity Enum Mapping**

**Issue**: YAML used intensity values like `"moderate"` and `"very_high"` but model only has `SessionIntensity` enum with `LOW`, `MEDIUM`, `HIGH`.

**Decision**: Added intensity mapping in seed step.

**Implementation**:
- File: `backend/seeds/steps/06_training_sessions.py:51-61`
  ```python
  intensity_map = {
      "low": SessionIntensity.LOW,
      "moderate": SessionIntensity.MEDIUM,
      "medium": SessionIntensity.MEDIUM,
      "high": SessionIntensity.HIGH,
      "very_high": SessionIntensity.HIGH,  # Map to HIGH
  }
  ```

**Rationale**: Support multiple input formats in seed data while maintaining strict enum types in the model.

---

### 5. **Fixed Player Seed UUID Generation**

**Issue**: Player seed was failing with `IntegrityError: null value in column "id"` because raw SQL INSERT doesn't trigger SQLModel's `default_factory=uuid4`.

**Decision**: Explicitly generate UUID in the seed payload.

**Implementation**:
- File: `backend/seeds/steps/05_players.py:167`
  ```python
  payload = {
      "id": str(uuid4()),  # Generate UUID for raw SQL insert
      ...
  }
  ```

**Rationale**: Raw SQL `upsert_advanced` bypasses SQLModel ORM, so UUIDs must be generated manually.

---

### 6. **Fixed Missing `is_injured` Field**

**Issue**: Player seed was failing with `IntegrityError: null value in column "is_injured" violates not-null constraint`.

**Decision**: Added `is_injured` field to payload with default value `False`.

**Implementation**:
- File: `backend/seeds/steps/05_players.py:183`
  ```python
  "is_injured": raw.get("is_injured", False),
  ```

**Rationale**: The `is_injured` field has a NOT NULL constraint but wasn't included in the seed payload.

---

### 7. **Implemented Auto-Linking for Player-Session Relationships**

**Issue**: DEMO_10×10 requires every player to have ≥10 training sessions, but manually defining all relationships in YAML would be tedious.

**Decision**: Created auto-linking seed step that links all players to their team's training sessions.

**Implementation**:
- File: `backend/seeds/steps/07_player_sessions.py`
- Auto-generates `PlayerSession` records for all players × their team's sessions
- Calculates realistic RPE (1-10) based on session intensity
- Calculates session_load = RPE × duration_min

**Rationale**: DRY principle - define sessions once per team, auto-link to all team players with realistic variations.

---

## DEMO_10×10 Compliance

**Final Status**: ✅ **ACHIEVED**

| Metric | Required | Actual | Status |
|--------|----------|--------|--------|
| Players | 10 | 10 | ✅ |
| Sessions per player | ≥10 | 12 | ✅ |
| Player-session links | ≥100 | 120 | ✅ |

**Verification Query**:
```sql
SELECT
    p.first_name || ' ' || p.last_name as player_name,
    t.name as team,
    COUNT(ps.session_id) as session_count
FROM players p
LEFT JOIN teams t ON p.team_id = t.id
LEFT JOIN player_session ps ON p.id = ps.player_id
GROUP BY p.id, p.first_name, p.last_name, t.name
ORDER BY session_count DESC;
```

**Results**:
- 8 Prima Squadra players: 12 sessions each
- 2 Primavera players: 12 sessions each
- Total: 10 players × 12 sessions = 120 player-session records

---

## API Testing

**Endpoint**: `GET /api/v1/sessions/?player_id={id}&limit=20`

**Test Result**: ✅ **PASS**
- Returns 12 real training sessions for Gianluigi Donnarumma
- Data includes: session_date, focus, focus_area, intensity, duration_min
- No mock data fallback

**Sample Response**:
```json
[
  {
    "session_date": "2025-11-07",
    "focus": "Allenamento Tattico",
    "focus_area": "tactical",
    "intensity": "HIGH",
    "duration_min": 90
  },
  ...
]
```

---

## Files Modified

### Seed System
1. `backend/seeds/config.py:108-117` - Added steps 06 & 07 to SEED_STEPS
2. `backend/seeds/steps/05_players.py:23,167,183` - Added UUID generation and is_injured field
3. `backend/seeds/steps/06_training_sessions.py` - Created new step for training sessions
4. `backend/seeds/steps/07_player_sessions.py` - Created new step for player-session auto-linking
5. `backend/seeds/utils.py:427` - Added IntegrityError logging for debugging
6. `backend/seeds/datasets/demo.yaml:372` - Fixed key naming (hyphen vs underscore)

### API Endpoints
7. `backend/app/routers/sessions.py:72-103` - Removed mock fallback, implemented real JOIN

---

## Testing Commands

### Seed DEMO_10×10
```bash
docker exec football_club_platform_backend bash -c "SEED_PROFILE=DEMO_10x10 SEED_ALLOW_PROD=true python seeds/seed_all.py"
```

### Verify Player Counts
```bash
docker exec football_club_platform_db psql -U app -d football_club_platform -c "
SELECT COUNT(*) as players,
       (SELECT COUNT(*) FROM training_sessions) as sessions,
       (SELECT COUNT(*) FROM player_session) as player_sessions
FROM players;"
```

### Test Sessions API
```bash
curl -s "http://localhost:8000/api/v1/sessions/?player_id={UUID}&limit=20" | python -m json.tool
```

---

## Known Issues & Limitations

### 1. **Pydantic v2 Literal Type Issue** (Team 2)
**Status**: Fixed in Team 2
- Changed `Literal[7, 14, 28]` to `int` with validation
- File: `backend/app/routers/predictions.py`

### 2. **Trailing Slash Redirects**
**Status**: Acceptable (FastAPI default behavior)
- Endpoints require trailing slash: `/api/v1/sessions/` not `/api/v1/sessions`
- Returns 307 Redirect if slash is missing

### 3. **No Session Name Field**
**Status**: Design decision
- Training sessions use `focus` field instead of explicit name
- Maps `session_name` from YAML to `focus` for compatibility

---

## Team 3 Achievements

✅ **Removed all mock implementations** from Team 2
✅ **Fixed seed system** to support production-grade data loading
✅ **Achieved DEMO_10×10 compliance** (10 players, 12 sessions each)
✅ **Implemented real database JOINs** for player-session filtering
✅ **Auto-linking system** for efficient relationship management
✅ **Production-ready endpoints** returning real data

---

## Next Steps (Future Teams)

1. **Add migration** for any new fields discovered during Team 3
2. **Optimize queries** - consider adding indexes on `(player_id, session_id)`
3. **Add caching** for frequently accessed session lists
4. **Implement pagination** for large result sets (>100 sessions)
5. **Add API tests** for sessions endpoint with player_id filter
6. **Document API** in OpenAPI/Swagger with examples

---

**Team 3 Status**: ✅ **COMPLETE**
**Ready for**: Merge to `main` and deployment to staging environment
