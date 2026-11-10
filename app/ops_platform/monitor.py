import json
import logging
import threading
import time

import httpx
import psutil

from . import db
from .config import settings
from .metrics import CHECK_FAILURES, HOST_CPU, HOST_DISK, HOST_MEM, SERVICE_LATENCY, SERVICE_UP

log = logging.getLogger("monitor")

RETENTION_INTERVAL = "7 days"
PRUNE_EVERY_N_CYCLES = 240  # roughly hourly at a 15s interval


def seed_services() -> None:
    """Upsert the services listed in MONITORED_SERVICES (JSON array)."""
    try:
        services = json.loads(settings.seed_services)
    except json.JSONDecodeError:
        log.error("MONITORED_SERVICES is not valid JSON; skipping seed")
        return
    with db.connect() as conn:
        for svc in services:
            conn.execute(
                """
                INSERT INTO services (name, health_url, owner) VALUES (%s, %s, %s)
                ON CONFLICT (name) DO UPDATE
                SET health_url = EXCLUDED.health_url, owner = EXCLUDED.owner
                """,
                (svc["name"], svc["health_url"], svc.get("owner")),
            )
    log.info("seeded %d services", len(services))


def check_service(url: str) -> dict:
    start = time.perf_counter()
    try:
        resp = httpx.get(url, timeout=settings.check_timeout)
    except httpx.HTTPError as exc:
        return {"up": False, "latency": None, "status_code": None, "error": str(exc)[:500]}
    latency = time.perf_counter() - start
    up = resp.status_code < 400
    return {
        "up": up,
        "latency": latency,
        "status_code": resp.status_code,
        "error": None if up else f"HTTP {resp.status_code}",
    }


def run_checks_once() -> None:
    with db.connect() as conn:
        services = conn.execute("SELECT id, name, health_url FROM services ORDER BY id").fetchall()

    for svc in services:
        result = check_service(svc["health_url"])
        name = svc["name"]
        SERVICE_UP.labels(name).set(1 if result["up"] else 0)
        if result["latency"] is not None:
            SERVICE_LATENCY.labels(name).observe(result["latency"])
        if not result["up"]:
            CHECK_FAILURES.labels(name).inc()
            log.warning("health check failed for %s: %s", name, result["error"])

        latency_ms = result["latency"] * 1000 if result["latency"] is not None else None
        with db.connect() as conn:
            conn.execute(
                """
                INSERT INTO service_checks (service_id, up, latency_ms, status_code, error)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (svc["id"], result["up"], latency_ms, result["status_code"], result["error"]),
            )


def sample_resources() -> None:
    HOST_CPU.set(psutil.cpu_percent(interval=None))
    HOST_MEM.set(psutil.virtual_memory().percent)
    HOST_DISK.labels("/").set(psutil.disk_usage("/").percent)


def prune_old_checks() -> None:
    with db.connect() as conn:
        conn.execute(
            "DELETE FROM service_checks WHERE checked_at < now() - %s::interval",
            (RETENTION_INTERVAL,),
        )


def _loop(stop: threading.Event) -> None:
    cycle = 0
    while not stop.is_set():
        try:
            run_checks_once()
            sample_resources()
            cycle += 1
            if cycle % PRUNE_EVERY_N_CYCLES == 0:
                prune_old_checks()
        except Exception:
            log.exception("monitor cycle failed")
        stop.wait(settings.check_interval)


def start_monitor() -> threading.Event:
    stop = threading.Event()
    threading.Thread(target=_loop, args=(stop,), name="monitor", daemon=True).start()
    log.info("monitor started, interval=%ss", settings.check_interval)
    return stop
