# Runbook: Host Disk Almost Full

**Alert:** `HostDiskAlmostFull`
**Severity:** warning

## Diagnose
1. Run `df -h /` and `du -sh /var/lib/docker/* | sort -h | tail` to find the largest directories.
2. Check the Prometheus and Loki volumes for retention problems.

## Recover
1. Prune unused images and stopped containers: `docker system prune`.
2. Confirm retention settings: Loki `retention_period` and Prometheus `--storage.tsdb.retention.time`.
3. Expand the volume if growth is expected.
