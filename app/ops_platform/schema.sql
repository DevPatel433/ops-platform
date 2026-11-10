CREATE TABLE IF NOT EXISTS services (
    id          SERIAL PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,
    health_url  TEXT NOT NULL,
    owner       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS service_checks (
    id          BIGSERIAL PRIMARY KEY,
    service_id  INT NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    checked_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    up          BOOLEAN NOT NULL,
    latency_ms  DOUBLE PRECISION,
    status_code INT,
    error       TEXT
);
CREATE INDEX IF NOT EXISTS idx_checks_service_time
    ON service_checks (service_id, checked_at DESC);

CREATE TABLE IF NOT EXISTS incidents (
    id           BIGSERIAL PRIMARY KEY,
    fingerprint  TEXT UNIQUE NOT NULL,
    alert_name   TEXT NOT NULL,
    severity     TEXT,
    service      TEXT,
    summary      TEXT,
    runbook_url  TEXT,
    status       TEXT NOT NULL DEFAULT 'firing',
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at  TIMESTAMPTZ
);
