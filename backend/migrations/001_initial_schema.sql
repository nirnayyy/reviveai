-- =====================================================================
-- ReviveAI — PostgreSQL / Supabase Initial Schema Migration
-- Migration ID: 001_initial_schema.sql
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    customer_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    email VARCHAR(128) NOT NULL,
    phone VARCHAR(32),
    ltv_inr NUMERIC(12, 2) DEFAULT 0.00,
    risk_tier VARCHAR(32) DEFAULT 'STANDARD',
    payment_methods_count INTEGER DEFAULT 1,
    historical_recovery_rate NUMERIC(5, 4) DEFAULT 0.6500,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_customers_customer_id ON customers(customer_id);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- 2. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    payment_id VARCHAR(64) UNIQUE NOT NULL,
    order_id VARCHAR(64),
    customer_id VARCHAR(64) REFERENCES customers(customer_id) ON DELETE CASCADE,
    amount_inr NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(8) DEFAULT 'INR',
    method VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    error_code VARCHAR(64),
    error_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id);
CREATE INDEX IF NOT EXISTS idx_payments_customer_id ON payments(customer_id);

-- 3. Subscriptions Table
CREATE TABLE IF NOT EXISTS subscriptions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    subscription_id VARCHAR(64) UNIQUE NOT NULL,
    plan_id VARCHAR(64) NOT NULL,
    customer_id VARCHAR(64) REFERENCES customers(customer_id) ON DELETE CASCADE,
    amount_inr NUMERIC(12, 2) NOT NULL,
    status VARCHAR(32) NOT NULL,
    total_count INTEGER DEFAULT 12,
    paid_count INTEGER DEFAULT 0,
    current_cycle_start TIMESTAMP WITH TIME ZONE,
    current_cycle_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_sub_id ON subscriptions(subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_customer_id ON subscriptions(customer_id);

-- 4. Webhook Events Table (Idempotency & Auditing)
CREATE TABLE IF NOT EXISTS webhook_events (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    event_id VARCHAR(64) UNIQUE NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    payload_json TEXT NOT NULL,
    signature VARCHAR(128),
    status VARCHAR(32) DEFAULT 'PROCESSED',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_webhook_events_event_id ON webhook_events(event_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_event_type ON webhook_events(event_type);

-- 5. Recovery Cases Table
CREATE TABLE IF NOT EXISTS recovery_cases (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    case_number VARCHAR(32) UNIQUE NOT NULL,
    customer_id VARCHAR(64) REFERENCES customers(customer_id) ON DELETE CASCADE,
    payment_id VARCHAR(64),
    subscription_id VARCHAR(64),
    webhook_event_id VARCHAR(64),
    amount_at_risk_inr NUMERIC(12, 2) NOT NULL,
    customer_ltv_inr NUMERIC(12, 2) DEFAULT 0.00,
    urgency_score NUMERIC(4, 2) DEFAULT 0.50,
    risk_age_hours NUMERIC(6, 1) DEFAULT 0.0,
    failure_reason VARCHAR(64) NOT NULL,
    error_code VARCHAR(64),
    error_description TEXT,
    payment_method VARCHAR(32) DEFAULT 'card',
    status VARCHAR(32) DEFAULT 'DETECTED',
    retry_count INTEGER DEFAULT 0,
    contact_count INTEGER DEFAULT 0,
    last_action_timestamp TIMESTAMP WITH TIME ZONE,
    expected_recovery_probability NUMERIC(5, 4) DEFAULT 0.0000,
    expected_recovery_value_inr NUMERIC(12, 2) DEFAULT 0.00,
    confidence_score NUMERIC(5, 4) DEFAULT 0.0000,
    recovery_mode VARCHAR(32) DEFAULT 'SANDBOX_SIMULATION',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX IF NOT EXISTS idx_recovery_cases_case_number ON recovery_cases(case_number);
CREATE INDEX IF NOT EXISTS idx_recovery_cases_status ON recovery_cases(status);
CREATE INDEX IF NOT EXISTS idx_recovery_cases_customer_id ON recovery_cases(customer_id);

-- 6. AI Decisions Table
CREATE TABLE IF NOT EXISTS ai_decisions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    case_id VARCHAR(36) REFERENCES recovery_cases(id) ON DELETE CASCADE,
    model_name VARCHAR(64) DEFAULT 'gemini-3.7-flash',
    diagnosis_category VARCHAR(64) NOT NULL,
    diagnosis_reasoning TEXT NOT NULL,
    recommended_action VARCHAR(64) NOT NULL,
    timing_schedule_minutes INTEGER DEFAULT 0,
    expected_recovery_probability NUMERIC(5, 4) NOT NULL,
    confidence_score NUMERIC(5, 4) NOT NULL,
    reasoning_summary TEXT NOT NULL,
    known_facts_json TEXT DEFAULT '[]',
    inferred_factors_json TEXT DEFAULT '[]',
    unknown_factors_json TEXT DEFAULT '[]',
    counterfactuals_json TEXT DEFAULT '[]',
    requires_human_review BOOLEAN DEFAULT FALSE,
    is_fallback BOOLEAN DEFAULT FALSE,
    raw_response TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_case_id ON ai_decisions(case_id);

-- 7. Policy Decisions Table
CREATE TABLE IF NOT EXISTS policy_decisions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    case_id VARCHAR(36) REFERENCES recovery_cases(id) ON DELETE CASCADE,
    ai_decision_id VARCHAR(36) REFERENCES ai_decisions(id) ON DELETE SET NULL,
    is_authorized BOOLEAN DEFAULT FALSE,
    action_approved VARCHAR(64),
    stopping_rule_triggered VARCHAR(64),
    rule_evaluations_json TEXT DEFAULT '[]',
    rejection_reasons_json TEXT DEFAULT '[]',
    requires_human_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_policy_decisions_case_id ON policy_decisions(case_id);

-- 8. Recovery Actions Table
CREATE TABLE IF NOT EXISTS recovery_actions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    case_id VARCHAR(36) REFERENCES recovery_cases(id) ON DELETE CASCADE,
    policy_decision_id VARCHAR(36) REFERENCES policy_decisions(id) ON DELETE SET NULL,
    action_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'SCHEDULED',
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    executed_at TIMESTAMP WITH TIME ZONE,
    cost_inr NUMERIC(10, 2) DEFAULT 0.00,
    friction_penalty NUMERIC(10, 2) DEFAULT 0.00,
    execution_mode VARCHAR(32) DEFAULT 'SANDBOX_SIMULATION',
    execution_details_json TEXT DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_recovery_actions_case_id ON recovery_actions(case_id);

-- 9. Recovery Outcomes Table
CREATE TABLE IF NOT EXISTS recovery_outcomes (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    case_id VARCHAR(36) REFERENCES recovery_cases(id) ON DELETE CASCADE,
    action_id VARCHAR(36) REFERENCES recovery_actions(id) ON DELETE SET NULL,
    is_recovered BOOLEAN DEFAULT FALSE,
    recovered_amount_inr NUMERIC(12, 2) DEFAULT 0.00,
    time_to_recovery_hours NUMERIC(6, 2) DEFAULT 0.00,
    actual_cost_inr NUMERIC(10, 2) DEFAULT 0.00,
    outcome_reason VARCHAR(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_recovery_outcomes_case_id ON recovery_outcomes(case_id);

-- 10. Audit Logs Table (Append-Only)
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    case_id VARCHAR(36) REFERENCES recovery_cases(id) ON DELETE SET NULL,
    actor VARCHAR(32) NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_case_id ON audit_logs(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Row Level Security (RLS) policies for Supabase
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recovery_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Allow authenticated backend service role full access
CREATE POLICY service_role_all ON customers FOR ALL TO service_role USING (true);
CREATE POLICY service_role_all ON payments FOR ALL TO service_role USING (true);
CREATE POLICY service_role_all ON subscriptions FOR ALL TO service_role USING (true);
CREATE POLICY service_role_all ON recovery_cases FOR ALL TO service_role USING (true);
CREATE POLICY service_role_all ON audit_logs FOR ALL TO service_role USING (true);
