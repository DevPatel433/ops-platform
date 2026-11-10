# Runbook: Host High CPU

**Alert:** `HostHighCPU`
**Severity:** warning

## Diagnose
1. Find the busiest processes with `top` or `docker stats`.
2. Check whether load matches a scheduled job or a traffic spike.

## Recover
1. Stop or reschedule runaway batch jobs.
2. Scale out the busiest service if the load is legitimate.
