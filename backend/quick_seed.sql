-- Quick seed script for Football Club Platform

-- Insert organization
INSERT INTO organizations (id, name, slug, country, email, is_active, benchmark_opt_in, timezone, locale, quota_players, quota_storage_gb, current_storage_gb, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'Demo FC',
  'demo-fc',
  'IT',
  'info@demofc.com',
  true,
  false,
  'Europe/Rome',
  'it-IT',
  100,
  50,
  0.0,
  NOW(),
  NOW()
) ON CONFLICT DO NOTHING
RETURNING id;

-- Store the organization ID
WITH org AS (
  SELECT id FROM organizations WHERE slug = 'demo-fc' LIMIT 1
)
-- Insert 5 demo players
INSERT INTO players (id, first_name, last_name, date_of_birth, role_primary, jersey_number, dominant_foot, is_active, organization_id, created_at, updated_at)
SELECT
  gen_random_uuid(),
  first_name,
  last_name,
  date_of_birth::date,
  role_primary::playerrole,
  jersey_number,
  'RIGHT'::dominantfoot,
  true,
  (SELECT id FROM org),
  NOW(),
  NOW()
FROM (VALUES
  ('Marco', 'Rossi', '2008-05-15', 'FW', 10),
  ('Luca', 'Bianchi', '2009-03-22', 'MF', 8),
  ('Giovanni', 'Verdi', '2008-11-08', 'DF', 5),
  ('Andrea', 'Neri', '2009-07-30', 'MF', 6),
  ('Francesco', 'Gialli', '2008-09-12', 'GK', 1)
) AS players(first_name, last_name, date_of_birth, role_primary, jersey_number);

-- Show result
SELECT COUNT(*) as player_count FROM players;
SELECT id, first_name, last_name, jersey_number, role_primary FROM players ORDER BY jersey_number;
