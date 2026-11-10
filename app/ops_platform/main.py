from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, HttpUrl

from . import db
from .config import settings
from .logging_setup import configure_logging
from .metrics import ALERTS_RECEIVED
from .monitor import seed_services, start_monitor
from .runbooks import list_runbooks, read_runbook

configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()
    seed_services()
    stop = start_monitor() if settings.enable_monitor else None
    yield
    if stop is not None:
        stop.set()


app = FastAPI(title="Ops Platform API", version="1.0.0", lifespan=lifespan)


class ServiceIn(BaseModel):
    name: str
    health_url: HttpUrl
    owner: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/services")
def list_services():
    with db.connect() as conn:
        return conn.execute(
            """
            SELECT s.name, s.health_url, s.owner, c.up, c.latency_ms, c.checked_at
            FROM services s
            LEFT JOIN LATERAL (
                SELECT up, latency_ms, checked_at FROM service_checks
                WHERE service_id = s.id ORDER BY checked_at DESC LIMIT 1
            ) c ON true
            ORDER BY s.name
            """
        ).fetchall()


@app.post("/api/services", status_code=status.HTTP_201_CREATED)
def upsert_service(svc: ServiceIn):
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO services (name, health_url, owner) VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE
            SET health_url = EXCLUDED.health_url, owner = EXCLUDED.owner
            """,
            (svc.name, str(svc.health_url), svc.owner),
        )
    return {"name": svc.name}


@app.delete("/api/services/{name}")
def delete_service(name: str):
    with db.connect() as conn:
        cur = conn.execute("DELETE FROM services WHERE name = %s", (name,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="service not found")
    return {"deleted": name}


@app.get("/api/services/{name}/checks")
def service_checks(name: str, limit: int = 50):
    limit = min(max(limit, 1), 500)
    with db.connect() as conn:
        return conn.execute(
            """
            SELECT c.checked_at, c.up, c.latency_ms, c.status_code, c.error
            FROM service_checks c JOIN services s ON s.id = c.service_id
            WHERE s.name = %s ORDER BY c.checked_at DESC LIMIT %s
            """,
            (name, limit),
        ).fetchall()


@app.get("/api/incidents")
def list_incidents(only_firing: bool = False):
    query = "SELECT * FROM incidents"
    if only_firing:
        query += " WHERE status = 'firing'"
    query += " ORDER BY started_at DESC LIMIT 200"
    with db.connect() as conn:
        return conn.execute(query).fetchall()


@app.post("/api/alerts/webhook")
def alertmanager_webhook(payload: dict):
    """Receives Alertmanager webhook payloads and turns alerts into incidents."""
    processed = 0
    with db.connect() as conn:
        for alert in payload.get("alerts", []):
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})
            state = alert.get("status", "firing")
            ALERTS_RECEIVED.labels(state).inc()

            fingerprint = alert.get("fingerprint") or f"{labels.get('alertname')}/{labels.get('service', '')}"
            if state == "resolved":
                conn.execute(
                    "UPDATE incidents SET status = 'resolved', resolved_at = now() WHERE fingerprint = %s",
                    (fingerprint,),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO incidents (fingerprint, alert_name, severity, service, summary, runbook_url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (fingerprint) DO UPDATE
                    SET status = 'firing', started_at = now(), resolved_at = NULL,
                        summary = EXCLUDED.summary
                    """,
                    (
                        fingerprint,
                        labels.get("alertname", "unknown"),
                        labels.get("severity"),
                        labels.get("service"),
                        annotations.get("summary"),
                        annotations.get("runbook_url"),
                    ),
                )
            processed += 1
    return {"processed": processed}


@app.get("/api/runbooks")
def runbooks_index():
    return {"runbooks": list_runbooks()}


@app.get("/api/runbooks/{name}", response_class=PlainTextResponse)
def runbook_detail(name: str):
    content = read_runbook(name)
    if content is None:
        raise HTTPException(status_code=404, detail="runbook not found")
    return content
