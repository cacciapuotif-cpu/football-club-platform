# Video Tagging Guidelines

## Objective
- Standardize event tagging for Sessions & Wellness analytics.

## Roles
- Performance Analyst: primary tagger.
- Assistant Coach: reviewer within 24h.

## Workflow
1. Upload raw video to analysis platform.
2. Sync with session metadata (tenant_id, session_id).
3. Tag events:
   - Warm-up, Main Drill, Small-Sided Game, Conditioning, Recovery.
   - Injury incident, High RPE cluster, Fatigue indicators.
4. Annotate athlete involvement (athlete_id).
5. Add contextual tags:
   - Load category (High/Medium/Low)
   - Tactical phase (Build-up, Transition, Set-piece)
   - Wellness note links (if alert triggered).

## Quality Standards
- 95% of events must have athlete tagging.
- Timestamp precision ±1 second.
- Review random 10% sample weekly.

## Integration
- Export JSON conforming to `video_annotations` schema (see unified-schema).
- Feed summary metrics into feature store (future work).
# Video Tagging Guidelines

## Tag Taxonomy
- **Event Types**: PASS, SHOT, TACKLE, SAVE, PRESS, SPRINT.
- **Body Region**: LOWER_BODY, UPPER_BODY, HEAD.
- **Outcome**: SUCCESS, FAIL, FOUL.
- **Intensity**: LOW, MEDIUM, HIGH (align with load metrics).

## Workflow
1. Upload raw footage to `videos` table with metadata (tenant_id, match_id).
2. Analysts tag clips in 5–10 s windows.
3. Each tag linked to `session_id` and `athlete_id`.
4. Enforce double-review for injury-related clips.

## Quality Criteria
- Agreement >90 % between two analysts before finalizing.
- Missing tags flagged by Great Expectations (`video_tags` suite).

## Integration
- Expose tagged clips through `/api/v1/video/tags`.
- Surface in Athlete 360 “Video” tab (future).

