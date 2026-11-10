# Runbook: Monitoring Target Down

**Alert:** `MonitoringTargetDown`
**Severity:** critical

## Impact
Prometheus cannot scrape a target, so you have a blind spot. Alerts for that target may not fire.

## Diagnose
1. Open Prometheus at `:9090` > Status > Targets and read the error.
2. Confirm the target container is running and its `/metrics` endpoint responds.

## Recover
1. Restart the target. Check its network and DNS name from the Prometheus container.
2. If the target is the Ops API, check the database connection first.
