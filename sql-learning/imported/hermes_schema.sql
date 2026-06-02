-- =============================================================
-- Hermes XCore PostgreSQL Schema — DDL
-- Apply via: psql -h 127.0.0.1 -U postgres -d hermes_logs -f hermes_schema.sql
-- =============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------
-- hermes_run_log: one row per task run across any node
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_run_log (
    run_id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id         VARCHAR(64) NOT NULL,
    start_ts        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_ts          TIMESTAMPTZ,
    status          VARCHAR(32) NOT NULL CHECK (status IN ('started','success','failed','timeout')),
    error_msg       TEXT,
    payload_hash    CHAR(64),           -- SHA-256 of serialized task payload
    duration_ms     INTEGER GENERATED ALWAYS AS
                    (EXTRACT(EPOCH FROM (end_ts - start_ts)) * 1000) STORED
) PARTITION BY RANGE (start_ts);

-- Monthly partitions for hermes_run_log
CREATE TABLE hermes_run_log_2026_06 PARTITION OF hermes_run_log
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE hermes_run_log_2026_07 PARTITION OF hermes_run_log
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
-- (Continue pattern for additional months)

-- -----------------------------------------------------------
-- hermes_feature_log: features extracted per run
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_feature_log (
    feature_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID        NOT NULL REFERENCES hermes_run_log(run_id) ON DELETE CASCADE,
    feature_name    VARCHAR(256) NOT NULL,
    feature_type    VARCHAR(64) CHECK (feature_type IN ('numeric','categorical','text_embedding','composite')),
    correlation_score FLOAT,
    p_value         FLOAT,
    source_table    VARCHAR(256),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------
-- hermes_model_registry: champion/challenger model inventory
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_model_registry (
    model_id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name      VARCHAR(256) NOT NULL,
    version         VARCHAR(64) NOT NULL,
    artifact_path   TEXT NOT NULL,      -- D:/DevDrive/ai-hub/checkpoints/{file}
    training_run_id UUID        REFERENCES hermes_run_log(run_id),
    eval_score      FLOAT,
    deployed_at     TIMESTAMPTZ,
    is_active       BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (model_name, version)
);

-- -----------------------------------------------------------
-- hermes_feedback_log: reward signals from downstream
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_feedback_log (
    feedback_id     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      VARCHAR(128) NOT NULL,
    model_id        UUID        REFERENCES hermes_model_registry(model_id),
    input_hash      CHAR(64)    NOT NULL,   -- SHA-256 of serialized input
    output_hash     CHAR(64)    NOT NULL,   -- SHA-256 of serialized output
    reward_signal   FLOAT       NOT NULL CHECK (reward_signal BETWEEN -1.0 AND 1.0),
    context_vector  JSONB,                  -- compressed context (128-dim latent)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE hermes_feedback_log_2026_06 PARTITION OF hermes_feedback_log
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

-- -----------------------------------------------------------
-- hermes_routing_decisions: bandit arm selection log
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_routing_decisions (
    decision_id     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      VARCHAR(128) NOT NULL,
    input_context   JSONB       NOT NULL,
    selected_arm    VARCHAR(128) NOT NULL,
    confidence      FLOAT       NOT NULL,
    actual_reward   FLOAT,                  -- populated async after feedback
    ts              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------
-- hermes_secondary_vars: discovered secondary feature variables
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hermes_secondary_vars (
    var_id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    var_name            VARCHAR(256) NOT NULL,
    discovered_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_chain   JSONB,              -- interaction path from source to target
    significance_score  FLOAT,
    included_in_model   BOOLEAN     NOT NULL DEFAULT FALSE
);

-- -----------------------------------------------------------
-- INDEXES
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_run_log_node_id    ON hermes_run_log (node_id);
CREATE INDEX IF NOT EXISTS idx_run_log_start_ts   ON hermes_run_log (start_ts);
CREATE INDEX IF NOT EXISTS idx_run_log_status     ON hermes_run_log (status);
CREATE INDEX IF NOT EXISTS idx_feature_run_id     ON hermes_feature_log (run_id);
CREATE INDEX IF NOT EXISTS idx_feature_created_at ON hermes_feature_log (created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_model_id  ON hermes_feedback_log (model_id);
CREATE INDEX IF NOT EXISTS idx_feedback_session   ON hermes_feedback_log (session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created   ON hermes_feedback_log (created_at);
CREATE INDEX IF NOT EXISTS idx_routing_session    ON hermes_routing_decisions (session_id);
CREATE INDEX IF NOT EXISTS idx_routing_ts         ON hermes_routing_decisions (ts);
CREATE INDEX IF NOT EXISTS idx_routing_arm        ON hermes_routing_decisions (selected_arm);
CREATE INDEX IF NOT EXISTS idx_secondary_score    ON hermes_secondary_vars (significance_score DESC);
2.2 — Feature Extraction Pipeline
