# Runbook: Host High Memory

**Alert:** `HostHighMemory`
**Severity:** critical

## Impact
Sustained memory pressure can trigger the OOM killer and terminate services.

## Diagnose
1. Find the largest consumers with `docker stats` or `kubectl top pods -n ops-platform`.
2. Look for memory growth over time, which suggests a leak.

## Recover
1. Restart the process that is leaking, then open a ticket to investigate.
2. Raise the memory limit only if the usage is expected.
