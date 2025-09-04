-- Minimal helper function to recompute KPIs (noop wrapper on view)
CREATE OR REPLACE FUNCTION recompute_kpis() RETURNS VOID AS $$
BEGIN
  -- No-op because vw_daily_kpis is a view; touch to ensure it compiles
  PERFORM 1;
END;
$$ LANGUAGE plpgsql;
