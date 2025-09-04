-- Optional seeds: a few merchants and accounts will be created via Python too.
-- This file is intentionally minimal; seeding is primarily handled by src.data_gen.

-- Example MCC seeded merchants
INSERT INTO merchants (merchant_id, name, mcc, country, risk_tier)
VALUES
  (uuid_generate_v4(), 'Globex Electronics', 5732, 'US', 2),
  (uuid_generate_v4(), 'Initech Online', 5967, 'US', 3),
  (uuid_generate_v4(), 'ACME Entertainment', 7996, 'US', 2)
ON CONFLICT DO NOTHING;
