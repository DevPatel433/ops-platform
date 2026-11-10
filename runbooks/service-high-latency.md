# Runbook: Service High Latency

**Alert:** `ServiceHighLatency`
**Severity:** warning

## Impact
Health checks take more than one second at p95. The service is up but degraded.

## Diagnose
1. Compare latency across services in the Grafana "Health check p95 latency" panel.
2. Check host CPU and memory on the Overview dashboard. Saturation is the usual cause.
3. Check the database: slow queries or connection exhaustion in PostgreSQL.

## Recover
1. Scale the service out or raise its CPU and memory limits.
2. If a recent deploy caused the regression, roll back.
3. If the database is the bottleneck, add an index or cap pool size.
