-- ============================================================
-- SOMA Migrations V014 + V015 - Supabase gjbibzfwvxiaudtfkiou
-- ============================================================

-- V014: plan columns on users
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS plan_code              VARCHAR(20)  NOT NULL DEFAULT 'free',
  ADD COLUMN IF NOT EXISTS plan_status            VARCHAR(20)  NOT NULL DEFAULT 'active',
  ADD COLUMN IF NOT EXISTS billing_provider       VARCHAR(20)  NULL,
  ADD COLUMN IF NOT EXISTS stripe_customer_id     VARCHAR(255) NULL,
  ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255) NULL,
  ADD COLUMN IF NOT EXISTS plan_started_at        TIMESTAMPTZ  NULL,
  ADD COLUMN IF NOT EXISTS plan_expires_at        TIMESTAMPTZ  NULL,
  ADD COLUMN IF NOT EXISTS trial_ends_at          TIMESTAMPTZ  NULL;

CREATE INDEX IF NOT EXISTS ix_users_plan_code       ON users(plan_code);
CREATE INDEX IF NOT EXISTS ix_users_stripe_customer ON users(stripe_customer_id);

CREATE TABLE IF NOT EXISTS plans (
  code VARCHAR(20) PRIMARY KEY, name VARCHAR(100) NOT NULL, rank INTEGER NOT NULL, is_active BOOLEAN NOT NULL DEFAULT true
);
CREATE TABLE IF NOT EXISTS plan_features (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), plan_code VARCHAR(20) NOT NULL REFERENCES plans(code) ON DELETE CASCADE, feature_code VARCHAR(100) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_plan_features_plan ON plan_features(plan_code);
CREATE TABLE IF NOT EXISTS feature_entitlements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  feature_code VARCHAR(100) NOT NULL, is_enabled BOOLEAN NOT NULL DEFAULT true, source VARCHAR(30) NOT NULL DEFAULT 'plan', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_entitlements_user ON feature_entitlements(user_id);

INSERT INTO plans (code, name, rank) VALUES ('free','SOMA Free',1),('ai','SOMA AI',2),('performance','SOMA Performance',3) ON CONFLICT (code) DO NOTHING;

INSERT INTO plan_features (plan_code, feature_code) VALUES
('free','basic_dashboard'),('free','basic_health_metrics'),('free','local_ai_tips'),
('ai','basic_dashboard'),('ai','basic_health_metrics'),('ai','local_ai_tips'),
('ai','ai_coach'),('ai','daily_briefing'),('ai','advanced_insights'),('ai','pdf_reports'),('ai','anomaly_detection'),('ai','biological_age'),
('performance','basic_dashboard'),('performance','basic_health_metrics'),('performance','local_ai_tips'),
('performance','ai_coach'),('performance','daily_briefing'),('performance','advanced_insights'),('performance','pdf_reports'),('performance','anomaly_detection'),('performance','biological_age'),
('performance','readiness_score'),('performance','injury_prediction'),('performance','biomechanics_vision'),('performance','advanced_vo2max'),('performance','training_load')
ON CONFLICT DO NOTHING;

-- V015: is_superuser + idempotency + usage analytics + app_settings
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS stripe_webhook_events (
  event_id VARCHAR(255) PRIMARY KEY, event_type VARCHAR(100) NOT NULL, received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS feature_usage_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL, feature_code VARCHAR(100) NULL, plan_code VARCHAR(20) NULL, metadata TEXT NULL, occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_feature_usage_user     ON feature_usage_events(user_id);
CREATE INDEX IF NOT EXISTS ix_feature_usage_type     ON feature_usage_events(event_type);
CREATE INDEX IF NOT EXISTS ix_feature_usage_occurred ON feature_usage_events(occurred_at);

CREATE TABLE IF NOT EXISTS app_settings (
  key VARCHAR(100) PRIMARY KEY, value TEXT NULL, description TEXT NULL, category VARCHAR(50) NOT NULL DEFAULT 'general', updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_by VARCHAR(100) NULL
);
INSERT INTO app_settings (key, value, description, category) VALUES
('free_plan_daily_ai_limit','10','Max requetes IA/jour plan free','ai'),
('free_plan_max_prompt_chars','1200','Max chars prompt plan free','ai'),
('free_plan_ai_timeout_seconds','15','Timeout IA (s) plan free','ai'),
('ai_plan_daily_ai_limit','100','Max requetes IA/jour plan AI','ai'),
('performance_plan_daily_ai_limit','500','Max requetes IA/jour plan Performance','ai'),
('stripe_price_ai_monthly','','Stripe Price ID - AI mensuel','billing'),
('stripe_price_ai_yearly','','Stripe Price ID - AI annuel','billing'),
('stripe_price_perf_monthly','','Stripe Price ID - Performance mensuel','billing'),
('stripe_price_perf_yearly','','Stripe Price ID - Performance annuel','billing'),
('trial_ai_days','7','Duree essai plan AI (jours)','billing'),
('trial_performance_days','3','Duree essai plan Performance (jours)','billing'),
('ollama_model','llama3.2:3b','Modele Ollama plan free','ai'),
('claude_standard_model','claude-3-5-haiku-20241022','Modele Claude plan AI','ai'),
('claude_advanced_model','claude-3-5-sonnet-20241022','Modele Claude plan Performance','ai')
ON CONFLICT (key) DO NOTHING;

SELECT 'plans' AS tbl, COUNT(*) AS rows FROM plans
UNION ALL SELECT 'plan_features', COUNT(*) FROM plan_features
UNION ALL SELECT 'app_settings', COUNT(*) FROM app_settings;
