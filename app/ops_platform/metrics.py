from prometheus_client import Counter, Gauge, Histogram

SERVICE_UP = Gauge("ops_service_up", "1 if the monitored service passed its last health check", ["service"])
SERVICE_LATENCY = Histogram("ops_service_check_latency_seconds", "Health check latency in seconds", ["service"])
CHECK_FAILURES = Counter("ops_service_check_failures", "Failed health checks", ["service"])

HOST_CPU = Gauge("ops_host_cpu_percent", "Host CPU utilisation percent")
HOST_MEM = Gauge("ops_host_memory_percent", "Host memory utilisation percent")
HOST_DISK = Gauge("ops_host_disk_percent", "Disk utilisation percent", ["mount"])

ALERTS_RECEIVED = Counter("ops_alerts_received", "Alertmanager alerts received", ["status"])
