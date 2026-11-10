# Runbook: Service Down

**Alert:** `ServiceDown` / `ServiceFlapping`
**Severity:** critical

## Impact
The monitored service failed its health check for over one minute. Users may be affected.

## Diagnose
1. Open `GET /api/services` and confirm the `up` flag and `error` for the service.
2. Check recent results with `GET /api/services/<name>/checks`.
3. Check container or pod status: `docker compose ps` or `kubectl get pods -n ops-platform`.
4. Read the last 100 log lines for the service (Grafana > Explore > Loki, `{container="<name>"}`).

## Recover
1. If the container or pod is crashlooping, read the log for the exit reason and fix config or dependencies.
2. Restart it: `docker compose restart <name>` or `kubectl rollout restart deployment/<name>`.
3. If the latest deploy caused it, roll back to the previous image.
4. Confirm recovery: the alert resolves and `ops_service_up` returns to 1.

## Escalate
If not recovered within 30 minutes, page the owner listed in the service registry.
