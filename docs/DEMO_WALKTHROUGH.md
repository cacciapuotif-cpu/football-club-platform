# Demo Walkthrough — Sessions & Wellness Release (Team C)

## Prerequisites

1. Backend services running with seeded data (see `backend/seeds/SEEDING_GUIDE.md`).
2. Frontend dependencies installed (`npm install` inside `frontend/`).
3. Playwright binaries installed once (`npx playwright install`).

## 1. Start the stack

```bash
# From repository root
docker compose up -d db redis

# Backend API
cd backend
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

Navigate to `http://localhost:3000`.

## 2. Sessions index

- Visit `/sessions`.
- Expected: list view showing seeded sessions with badges for load/RPE and toggle to calendar view.
- Filters: team/type/date selectors respond instantly; calendar renders grouped sessions.
- KPI: deep-link to session detail by clicking a card.

## 3. Session detail & snapshot

- Navigate to a session (`/sessions/<sessionId>`).
- Check:
  - Participation table with load/RPE per athlete.
  - Wellness snapshot sidebar summarising readiness, top drivers and open alerts.
  - `Vai a Athlete 360` link routes to athlete page.
- Ack an alert → status changes and moves into resolved list.

## 4. Wellness dashboard

- Visit `/wellness`.
- Select team / date; Heatmap cards show readiness, Δ, alert count and link to Athlete 360.
- Policies panel lists alert rules with cooldown & completeness.

## 5. Athlete 360

- From heatmap or session page follow link to `/athletes/<athleteId>`.
- Verify:
  - Tabs for “Wellness & Readiness” and “Sessioni recenti”.
  - Trend polyline, latest feature snapshot, open/resolved alerts with acknowledge CTA.
  - Sessions tab lists recent workloads with links back to sessions.

## 6. Automated regression

```bash
cd frontend
npm run lint          # Next lint
npm run test:e2e      # Playwright suite (uses mocked APIs)
```

Expect both tests to pass:
- `wellness-heatmap.spec.ts`: heatmap → Athlete 360 → ack alert.
- `sessions-flow.spec.ts`: sessions list → session detail → Athlete 360 deep link.

## 7. Theming & localisation sanity

- Headers/buttons use tenant colours from `ThemeProvider`.
- Translation hooks (`useI18n`) render Italian copy by default.

## Troubleshooting

- **Missing dependencies** (e.g. `Module not found: date-fns`): run `npm install` inside `frontend/` after pulling latest changes.
- **Alert acknowledge errors**: backend must expose `/api/v1/wellness/alerts/{alertId}/ack`; ensure API is reachable with valid JWT/`SKIP_AUTH=true`.
- **Playwright failing to start**: ensure port 3000 free or set `PORT=3010` before running `npm run test:e2e`.

All flows above should function end-to-end on the seeded demo dataset.

