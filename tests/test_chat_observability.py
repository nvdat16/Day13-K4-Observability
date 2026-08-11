from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app


def test_chat_response_log_exposes_quality_for_dashboard(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Explain observability",
            },
        )

    assert response.status_code == 200
    correlation_id = response.json()["correlation_id"]
    assert re.fullmatch(r"req-[0-9a-f]{8}", correlation_id)
    assert response.headers["x-request-id"] == correlation_id
    assert float(response.headers["x-response-time-ms"]) >= 0

    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    request_event = next(event for event in events if event["event"] == "request_received")
    response_event = next(event for event in events if event["event"] == "response_sent")
    assert request_event["correlation_id"] == correlation_id
    assert response_event["correlation_id"] == correlation_id
    assert request_event["session_id"] == "session-01"
    assert request_event["feature"] == "qa"
    assert request_event["model"]
    assert request_event["env"]
    assert request_event["user_id_hash"] != "student-01"
    assert response_event["quality_score"] == response.json()["quality_score"]
