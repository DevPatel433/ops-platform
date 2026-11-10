import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://ops:ops@localhost:5432/ops")
    check_interval: int = int(os.getenv("CHECK_INTERVAL_SECONDS", "15"))
    check_timeout: float = float(os.getenv("CHECK_TIMEOUT_SECONDS", "3"))
    runbook_dir: str = os.getenv("RUNBOOK_DIR", "/app/runbooks")
    seed_services: str = os.getenv("MONITORED_SERVICES", "[]")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    enable_monitor: bool = os.getenv("ENABLE_MONITOR", "true").lower() == "true"


settings = Settings()
