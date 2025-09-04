-- Views
CREATE OR REPLACE VIEW vw_daily_kpis AS
SELECT
  date_trunc('day', t.ts) AS date,
  COUNT(*) AS tx_count,
  COUNT(a.alert_id) AS alerts_count,
  -- Simple proxies for precision/recall using model predictions
  AVG(CASE WHEN ms.predicted_label THEN (CASE WHEN t.label_fraud THEN 1 ELSE 0 END) ELSE NULL END) AS precision_est,
  AVG(CASE WHEN t.label_fraud THEN (CASE WHEN ms.predicted_label THEN 1 ELSE 0 END) ELSE NULL END) AS recall_est,
  SUM(CASE WHEN a.alert_id IS NOT NULL AND t.label_fraud THEN t.amount ELSE 0 END) AS est_loss_avoided
FROM transactions t
LEFT JOIN alerts a ON a.tx_id = t.tx_id
LEFT JOIN LATERAL (
  SELECT * FROM model_scores ms2 WHERE ms2.tx_id = t.tx_id ORDER BY created_at DESC LIMIT 1
) ms ON true
GROUP BY 1
ORDER BY 1 DESC;

CREATE OR REPLACE VIEW vw_suspicious_latest AS
SELECT t.tx_id, t.ts, t.amount, t.currency, t.channel, t.device_id,
       c.card_id, c.brand, m.merchant_id, m.name AS merchant_name, m.mcc, m.risk_tier,
       a.rule_name, a.score, a.status AS alert_status,
       ms.model_name, ms.proba, ms.predicted_label
FROM transactions t
LEFT JOIN cards c ON c.card_id = t.card_id
LEFT JOIN merchants m ON m.merchant_id = t.merchant_id
LEFT JOIN LATERAL (
  SELECT * FROM alerts a2 WHERE a2.tx_id = t.tx_id ORDER BY created_at DESC LIMIT 1
) a ON true
LEFT JOIN LATERAL (
  SELECT * FROM model_scores ms2 WHERE ms2.tx_id = t.tx_id ORDER BY created_at DESC LIMIT 1
) ms ON true
ORDER BY t.ts DESC;
