import json
import logging

import httpx
import pytest

from ops_platform import monitor, runbooks
from ops_platform.config import settings
from ops_platform.logging_setup import JsonFormatter


def test_json_formatter_emits_parseable_json():
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    out = json.loads(JsonFormatter().format(record))
    assert out["msg"] == "hello world"
    assert out["level"] == "INFO"


def test_runbook_lookup_and_traversal_guard(monkeypatch, tmp_path):
    (tmp_path / "service-down.md").write_text("# Service down")
    monkeypatch.setattr(settings, "runbook_dir", str(tmp_path))

    assert runbooks.list_runbooks() == ["service-down"]
    assert runbooks.read_runbook("service-down") == "# Service down"
    assert runbooks.read_runbook("../../etc/passwd") is None
    assert runbooks.read_runbook("missing") is None


def test_check_service_flags_error_status(monkeypatch):
    class FakeResponse:
        status_code = 503

    monkeypatch.setattr(monitor.httpx, "get", lambda url, timeout: FakeResponse())
    result = monitor.check_service("http://example/health")
    assert result["up"] is False
    assert result["status_code"] == 503


def test_check_service_handles_connection_failure(monkeypatch):
    def boom(url, timeout):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(monitor.httpx, "get", boom)
    result = monitor.check_service("http://example/health")
    assert result["up"] is False
    assert "connection refused" in result["error"]
