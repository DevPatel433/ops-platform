# Ops Platform: Centralised Monitoring and Application Operations

A centralised monitoring platform for application health, logs, resource usage, and alerting, with incident runbooks.

## Features

| Requirement | Implementation |
|---|---|
| Application health monitoring | `ops_platform/monitor.py` polls each registered service's health URL |
| Centralised log collection | Promtail collects container logs and ships them to Loki |
| Resource utilisation tracking | Host CPU, memory, and disk sampled with `psutil` and exposed as metrics |
| Automated alerting | Prometheus rules evaluated and routed through Alertmanager |
| Service availability monitoring | `ops_service_up` gauge, check history in PostgreSQL, uptime panels in Grafana |
| Incident runbooks and recovery | Alerts create incidents linked to runbooks served by `/api/runbooks` |

## Architecture

```
 services ──health──▶ Ops API (FastAPI) ──▶ PostgreSQL
                       │   ▲                 (services, checks, incidents)
          /metrics     │   │ webhook
                       ▼   │
 containers ─logs─▶ Promtail ─▶ Loki ◀─────── Grafana ◀── Prometheus ──▶ Alertmanager
```

## Quick start (Docker Compose)

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Ops API docs | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |
| Grafana (admin / change-me) | http://localhost:3000 |

Grafana loads the "Ops Platform Overview" dashboard automatically.

To trigger a real alert, stop the demo service: `docker compose stop demo-web`. After about one minute, `ServiceDown` fires, Alertmanager posts it to the API, and an incident appears at `GET /api/incidents?only_firing=true` with its runbook link.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check for the API itself |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/services` | Registered services with latest check result |
| POST | `/api/services` | Register or update a service `{name, health_url, owner}` |
| DELETE | `/api/services/{name}` | Remove a service |
| GET | `/api/services/{name}/checks?limit=50` | Recent check history |
| GET | `/api/incidents?only_firing=true` | Incidents created from alerts |
| POST | `/api/alerts/webhook` | Alertmanager receiver (do not call manually) |
| GET | `/api/runbooks` | List runbooks |
| GET | `/api/runbooks/{name}` | Runbook content as Markdown |

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://ops:ops@localhost:5432/ops` | PostgreSQL connection string |
| `MONITORED_SERVICES` | `[]` | JSON array of services to seed at startup |
| `CHECK_INTERVAL_SECONDS` | `15` | Time between check cycles |
| `CHECK_TIMEOUT_SECONDS` | `3` | Per-check HTTP timeout |
| `RUNBOOK_DIR` | `/app/runbooks` | Directory of runbook Markdown files |
| `ENABLE_MONITOR` | `true` | Set to `false` to disable background checks |
| `LOG_LEVEL` | `INFO` | Log level (logs are JSON) |

## Kubernetes

`k8s/ops-platform.yaml` deploys the namespace, PostgreSQL (StatefulSet), and the Ops API. Build and push your image first, then update the image name and secret values:

```bash
docker build -t ghcr.io/your-org/ops-platform-api:1.0.0 .
docker push ghcr.io/your-org/ops-platform-api:1.0.0
kubectl apply -f k8s/ops-platform.yaml
```

Prometheus, Alertmanager, Loki, Promtail, and Grafana are not included in the manifest. Install them with the `kube-prometheus-stack` and `loki` Helm charts, reusing the configs in `prometheus/`, `alertmanager/`, `loki/`, and `grafana/`. The Ops API pod carries `prometheus.io/*` annotations, but kube-prometheus-stack ignores them by default. Add a ServiceMonitor or scrape config for `ops-api:8000/metrics`.

## Tests

```bash
cd app
pip install -r requirements.txt
pytest
```

## Production notes

- The API has no authentication. Put it behind an ingress with SSO or an API gateway before exposing it.
- Replace all default passwords and use a secret manager.
- Run one API replica. Each process runs the monitor loop, so multiple replicas would duplicate checks.
- Retention: check history is kept 7 days, Loki 7 days, Prometheus 15 days. Adjust to your needs.

## Project layout

```
app/ops_platform/   FastAPI service, monitor, DB schema, metrics, runbook loader
app/tests/          Unit tests
prometheus/         Scrape config and alerting rules
alertmanager/       Routing to the incident webhook
loki/, promtail/    Log storage and collection
grafana/            Datasources, dashboard provisioning, dashboard JSON
runbooks/           Incident runbooks linked from alerts
k8s/                Kubernetes manifests
```

## License

MIT
