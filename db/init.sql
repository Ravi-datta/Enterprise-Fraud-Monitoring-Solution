-- Schema initialization for fraud-e2e
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS accounts (
  account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  customer_id UUID NOT NULL DEFAULT uuid_generate_v4(),
  opened_at TIMESTAMP NOT NULL,
  region TEXT NOT NULL,
  risk_score NUMERIC(5,2) DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS cards (
  card_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  account_id UUID REFERENCES accounts(account_id),
  pan_last4 CHAR(4) NOT NULL,
  brand TEXT NOT NULL,
  exp_date DATE NOT NULL,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS merchants (
  merchant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  mcc INT NOT NULL,
  country TEXT NOT NULL,
  risk_tier INT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
  tx_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  card_id UUID REFERENCES cards(card_id),
  merchant_id UUID REFERENCES merchants(merchant_id),
  ts TIMESTAMP NOT NULL,
  amount NUMERIC(12,2) NOT NULL,
  currency TEXT NOT NULL,
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  channel TEXT NOT NULL,
  device_id TEXT,
  is_international BOOLEAN,
  label_fraud BOOLEAN DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
  alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tx_id UUID REFERENCES transactions(tx_id),
  rule_name TEXT NOT NULL,
  score NUMERIC,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status in ('OPEN','ACK','DISMISSED','CONFIRMED'))
);

CREATE TABLE IF NOT EXISTS labels (
  tx_id UUID PRIMARY KEY REFERENCES transactions(tx_id),
  source TEXT NOT NULL,
  label BOOLEAN NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rules (
  rule_name TEXT PRIMARY KEY,
  active BOOLEAN NOT NULL,
  params JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_scores (
  tx_id UUID REFERENCES transactions(tx_id),
  model_name TEXT NOT NULL,
  proba NUMERIC,
  predicted_label BOOLEAN,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_transactions_ts ON transactions(ts);
CREATE INDEX IF NOT EXISTS idx_transactions_card_ts ON transactions(card_id, ts);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant_ts ON transactions(merchant_id, ts);

-- Helper table for features
CREATE TABLE IF NOT EXISTS model_features (
  tx_id UUID PRIMARY KEY,
  label_fraud BOOLEAN,
  amount DOUBLE PRECISION,
  last_tx_delta_minutes DOUBLE PRECISION,
  tx_count_1h INT,
  tx_count_24h INT,
  amount_mean_24h DOUBLE PRECISION,
  geo_velocity_kmph_prev DOUBLE PRECISION,
  channel TEXT,
  device_id TEXT,
  merchant_risk_tier INT,
  brand TEXT,
  ts TIMESTAMP
);
