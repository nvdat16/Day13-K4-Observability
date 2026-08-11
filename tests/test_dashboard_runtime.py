from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.dashboard import build_dashboard_snapshot, render_dashboard_html


def _record(ts: str, event: str, **fields) -> dict:
    return {"ts": ts, "event": event, **fields}


def test_dashboard_snapshot_aggregates_all_six_panels(tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    records = [
        _record("2026-08-11T09:00:00Z", "request_received"),
        _record("2026-08-11T09:00:01Z", "response_sent", latency_ms=100, cost_usd=0.1, tokens_in=10, tokens_out=20, quality_score=0.8),
        _record("2026-08-11T09:01:00Z", "request_received"),
        _record("2026-08-11T09:01:01Z", "request_failed", error_type="TimeoutError"),
        _record("2026-08-11T09:01:02Z", "response_sent", latency_ms=5000, cost_usd=0.2, tokens_in=30, tokens_out=40, quality_score=0.6),
        _record("2026-08-11T07:00:00Z", "request_received"),
    ]
    log_path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

    snapshot = build_dashboard_snapshot(
        log_path,
        now=datetime(2026, 8, 11, 9, 30, tzinfo=timezone.utc),
    )

    assert set(snapshot["panels"]) == {"latency", "traffic", "errors", "cost", "tokens", "quality"}
    assert snapshot["panels"]["latency"] == {
        "title": "Latency percentiles",
        "unit": "ms",
        "threshold": {"aggregation": "p95", "operator": "lte", "value": 3000},
        "p50": 100.0,
        "p95": 5000.0,
        "p99": 5000.0,
        "series": [{"label": "09:00", "value": 100.0}, {"label": "09:01", "value": 5000.0}],
    }
    assert snapshot["panels"]["traffic"]["count"] == 2
    assert snapshot["panels"]["errors"]["error_rate_pct"] == 50.0
    assert snapshot["panels"]["errors"]["breakdown"] == {"TimeoutError": 1}
    assert snapshot["panels"]["cost"]["total"] == 0.3
    assert snapshot["panels"]["tokens"]["tokens_in"] == 40
    assert snapshot["panels"]["tokens"]["tokens_out"] == 60
    assert snapshot["panels"]["quality"]["mean"] == 0.7


def test_dashboard_html_exposes_contract_and_refresh() -> None:
    html = render_dashboard_html("baseline")

    for panel_id in ("latency", "traffic", "errors", "cost", "tokens", "quality"):
        assert f"panel('{panel_id}'" in html
    assert "data/logs.jsonl" in html
    assert "/dashboard/data?phase=baseline" in html
    assert "setInterval(refresh,30000)" in html


def test_dashboard_can_select_baseline_and_incident_phases(tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    records = [
        _record("2026-08-11T09:00:00Z", "request_received"),
        _record("2026-08-11T09:00:01Z", "response_sent", latency_ms=100, cost_usd=0.1, tokens_in=10, tokens_out=20, quality_score=0.8),
        _record("2026-08-11T09:05:00Z", "incident_enabled"),
        _record("2026-08-11T09:05:01Z", "request_received"),
        _record("2026-08-11T09:05:05Z", "response_sent", latency_ms=4000, cost_usd=0.1, tokens_in=10, tokens_out=20, quality_score=0.8),
        _record("2026-08-11T09:06:00Z", "incident_disabled"),
    ]
    log_path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

    baseline = build_dashboard_snapshot(log_path, now=datetime(2026, 8, 11, 9, 30, tzinfo=timezone.utc), phase="baseline")
    incident = build_dashboard_snapshot(log_path, now=datetime(2026, 8, 11, 9, 30, tzinfo=timezone.utc), phase="incident")

    assert baseline["panels"]["latency"]["p95"] == 100.0
    assert incident["panels"]["latency"]["p95"] == 4000.0
