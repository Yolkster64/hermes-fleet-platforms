-- Hermes XCore PostgreSQL Schema (integrated from pasted bundle)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS hermes_run_log (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id VARCHAR(64) NOT NULL,
    start_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_ts TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL CHECK (status IN ('started','success','failed','timeout')),
    error_msg TEXT,
    payload_hash CHAR(64)
);

CREATE TABLE IF NOT EXISTS hermes_feature_log (
    feature_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES hermes_run_log(run_id) ON DELETE CASCADE,
    feature_name VARCHAR(256) NOT NULL,
    feature_type VARCHAR(64) CHECK (feature_type IN ('numeric','categorical','text_embedding','composite')),
    correlation_score FLOAT,
    p_value FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hermes_model_registry (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(256) NOT NULL,
    version VARCHAR(64) NOT NULL,
    artifact_path TEXT NOT NULL,
    eval_score FLOAT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (model_name, version)
);

CREATE TABLE IF NOT EXISTS hermes_feedback_log (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(128) NOT NULL,
    model_id UUID REFERENCES hermes_model_registry(model_id),
    reward_signal FLOAT NOT NULL CHECK (reward_signal BETWEEN -1.0 AND 1.0),
    context_vector JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hermes_routing_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(128) NOT NULL,
    input_context JSONB NOT NULL,
    selected_arm VARCHAR(128) NOT NULL,
    confidence FLOAT NOT NULL,
    actual_reward FLOAT,
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

