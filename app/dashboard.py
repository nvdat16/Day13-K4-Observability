from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"
DEFAULT_LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((percentile / 100) * len(ordered)) - 1))
    return round(float(ordered[index]), 2)


def _load_records(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def build_dashboard_snapshot(
    log_path: Path = DEFAULT_LOG_PATH,
    config_path: Path = DASHBOARD_CONFIG_PATH,
    *,
    now: datetime | None = None,
    phase: str = "all",
) -> dict[str, Any]:
    dashboard = yaml.safe_load(config_path.read_text(encoding="utf-8"))["dashboard"]
    panel_config = {panel["id"]: panel for panel in dashboard["panels"]}
    reference_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = reference_time - timedelta(minutes=dashboard["time_range_minutes"])

    window_records: list[tuple[datetime, dict[str, Any]]] = []
    for record in _load_records(log_path):
        timestamp = _parse_timestamp(record.get("ts"))
        if timestamp is not None and cutoff <= timestamp <= reference_time:
            window_records.append((timestamp, record))

    phase = phase if phase in {"all", "baseline", "incident"} else "all"
    enabled_at = [ts for ts, rec in window_records if rec.get("event") == "incident_enabled"]
    disabled_at = [ts for ts, rec in window_records if rec.get("event") == "incident_disabled"]
    if phase == "baseline" and enabled_at:
        first_incident = min(enabled_at)
        window_records = [(ts, rec) for ts, rec in window_records if ts < first_incident]
    elif phase == "incident" and enabled_at:
        last_incident = max(enabled_at)
        following_disables = [ts for ts in disabled_at if ts > last_incident]
        incident_end = min(following_disables) if following_disables else reference_time
        window_records = [(ts, rec) for ts, rec in window_records if last_incident <= ts <= incident_end]

    requests = [(ts, rec) for ts, rec in window_records if rec.get("event") == "request_received"]
    responses = [(ts, rec) for ts, rec in window_records if rec.get("event") == "response_sent"]
    failures = [(ts, rec) for ts, rec in window_records if rec.get("event") == "request_failed"]

    latency_values = [float(rec["latency_ms"]) for _, rec in responses if isinstance(rec.get("latency_ms"), (int, float))]
    costs = [float(rec["cost_usd"]) for _, rec in responses if isinstance(rec.get("cost_usd"), (int, float))]
    qualities = [float(rec["quality_score"]) for _, rec in responses if isinstance(rec.get("quality_score"), (int, float))]

    traffic_by_minute: Counter[str] = Counter()
    cost_by_minute: defaultdict[str, float] = defaultdict(float)
    latency_by_minute: defaultdict[str, list[float]] = defaultdict(list)
    for timestamp, _ in requests:
        traffic_by_minute[timestamp.strftime("%H:%M")] += 1
    for timestamp, record in responses:
        bucket = timestamp.strftime("%H:%M")
        if isinstance(record.get("cost_usd"), (int, float)):
            cost_by_minute[bucket] += float(record["cost_usd"])
        if isinstance(record.get("latency_ms"), (int, float)):
            latency_by_minute[bucket].append(float(record["latency_ms"]))

    minute_labels = sorted(set(traffic_by_minute) | set(cost_by_minute) | set(latency_by_minute))
    error_breakdown = Counter(str(rec.get("error_type") or "UnknownError") for _, rec in failures)
    request_count = len(requests)
    error_rate = round((len(failures) / request_count * 100), 2) if request_count else 0.0
    active_minutes = max(1, len(traffic_by_minute))

    return {
        "meta": {
            "title": dashboard["title"],
            "time_range_minutes": dashboard["time_range_minutes"],
            "refresh_seconds": dashboard["refresh_seconds"],
            "generated_at": reference_time.isoformat(),
            "records_in_window": len(window_records),
            "source": "data/logs.jsonl",
            "phase": phase,
        },
        "panels": {
            "latency": {
                "title": panel_config["latency"]["title"],
                "unit": panel_config["latency"]["unit"],
                "threshold": panel_config["latency"]["threshold"],
                "p50": _percentile(latency_values, 50),
                "p95": _percentile(latency_values, 95),
                "p99": _percentile(latency_values, 99),
                "series": [{"label": label, "value": _percentile(latency_by_minute[label], 95)} for label in minute_labels],
            },
            "traffic": {
                "title": panel_config["traffic"]["title"],
                "unit": panel_config["traffic"]["unit"],
                "threshold": panel_config["traffic"]["threshold"],
                "count": request_count,
                "rate_per_minute": round(request_count / active_minutes, 2),
                "series": [{"label": label, "value": traffic_by_minute[label]} for label in minute_labels],
            },
            "errors": {
                "title": panel_config["errors"]["title"],
                "unit": panel_config["errors"]["unit"],
                "threshold": panel_config["errors"]["threshold"],
                "error_rate_pct": error_rate,
                "count": len(failures),
                "breakdown": dict(error_breakdown),
            },
            "cost": {
                "title": panel_config["cost"]["title"],
                "unit": panel_config["cost"]["unit"],
                "threshold": panel_config["cost"]["threshold"],
                "total": round(sum(costs), 6),
                "series": [{"label": label, "value": round(cost_by_minute[label], 6)} for label in minute_labels],
            },
            "tokens": {
                "title": panel_config["tokens"]["title"],
                "unit": panel_config["tokens"]["unit"],
                "threshold": panel_config["tokens"]["threshold"],
                "tokens_in": sum(int(rec.get("tokens_in", 0)) for _, rec in responses),
                "tokens_out": sum(int(rec.get("tokens_out", 0)) for _, rec in responses),
            },
            "quality": {
                "title": panel_config["quality"]["title"],
                "unit": panel_config["quality"]["unit"],
                "threshold": panel_config["quality"]["threshold"],
                "mean": round(mean(qualities), 3) if qualities else 0.0,
                "samples": len(qualities),
            },
        },
    }


def render_dashboard_html(phase: str = "all") -> str:
    phase = phase if phase in {"all", "baseline", "incident"} else "all"
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Day 13 AI Observability</title>
  <style>
    :root { color-scheme: dark; --bg:#07111f; --card:#0d1b2d; --line:#1e3350; --text:#f3f7ff; --muted:#93a8c2; --blue:#5da9ff; --cyan:#42d7c8; --amber:#ffbf69; --red:#ff6b7a; --green:#63e6a6; }
    * { box-sizing: border-box; }
    body { margin:0; min-height:100vh; background:radial-gradient(circle at 15% 0%,#12335a 0,transparent 28%),var(--bg); color:var(--text); font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif; }
    main { max-width:1440px; margin:auto; padding:32px; }
    header { display:flex; justify-content:space-between; gap:20px; align-items:flex-end; margin-bottom:24px; }
    h1 { margin:0; font-size:30px; letter-spacing:-.04em; }
    .eyebrow { color:var(--cyan); text-transform:uppercase; letter-spacing:.16em; font-size:12px; font-weight:800; margin-bottom:8px; }
    .meta { color:var(--muted); text-align:right; font-size:13px; line-height:1.7; }
    .grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }
    .panel { background:linear-gradient(145deg,rgba(18,39,65,.96),rgba(10,25,43,.96)); border:1px solid var(--line); border-radius:16px; padding:20px; min-height:255px; box-shadow:0 18px 45px rgba(0,0,0,.18); }
    .panel-head { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
    .panel h2 { margin:0; font-size:16px; }
    .unit { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.08em; }
    .metric { font-size:34px; font-weight:800; letter-spacing:-.04em; margin:22px 0 6px; }
    .submetrics { display:flex; gap:18px; color:var(--muted); font-size:13px; }
    .submetrics strong { color:var(--text); }
    .threshold { margin-top:15px; padding:8px 10px; border-radius:9px; font-size:12px; color:var(--muted); background:#091524; border:1px solid var(--line); }
    .threshold.pass { border-color:rgba(99,230,166,.45); color:var(--green); }
    .threshold.fail { border-color:rgba(255,107,122,.55); color:var(--red); }
    .bars { height:72px; display:flex; align-items:flex-end; gap:4px; margin-top:20px; border-bottom:1px solid var(--line); }
    .bar { flex:1; min-width:4px; background:linear-gradient(180deg,var(--cyan),var(--blue)); border-radius:4px 4px 0 0; opacity:.9; }
    .dual { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:23px; }
    .token { padding:14px; border-radius:12px; background:#091524; }
    .token b { display:block; font-size:25px; margin-top:5px; }
    .gauge { height:12px; border-radius:20px; background:#091524; overflow:hidden; margin-top:24px; border:1px solid var(--line); }
    .gauge > div { height:100%; background:linear-gradient(90deg,var(--amber),var(--green)); }
    .empty { color:var(--muted); padding-top:46px; text-align:center; }
    footer { color:var(--muted); margin-top:20px; font-size:12px; display:flex; justify-content:space-between; }
    @media (max-width:1000px) { .grid { grid-template-columns:repeat(2,1fr); } }
    @media (max-width:650px) { main{padding:18px}.grid{grid-template-columns:1fr}header{align-items:flex-start;flex-direction:column}.meta{text-align:left} }
  </style>
</head>
<body>
<main>
  <header><div><div class="eyebrow">K4 · Runtime dashboard · PHASE_LABEL</div><h1>Day 13 AI Observability</h1></div><div class="meta" id="meta">Loading data/logs.jsonl…</div></header>
  <section class="grid" id="grid"></section>
  <footer><span>Source: data/logs.jsonl · Contract: config/dashboard.yaml</span><span>Auto-refresh every 30 seconds</span></footer>
</main>
<script>
const fmt=(v,d=0)=>Number(v||0).toLocaleString(undefined,{minimumFractionDigits:d,maximumFractionDigits:d});
const status=(value,t)=>t.operator==='lte'?value<=t.value:value>=t.value;
const threshold=(value,t,unit)=>`<div class="threshold ${status(value,t)?'pass':'fail'}">${status(value,t)?'✓ Within':'! Breached'} SLO · ${t.aggregation} ${t.operator==='lte'?'≤':'≥'} ${t.value} ${unit}</div>`;
const bars=series=>{const values=series.map(x=>Number(x.value));const max=Math.max(...values,1);return `<div class="bars" title="Per-minute series">${values.slice(-24).map(v=>`<div class="bar" style="height:${Math.max(4,v/max*100)}%" title="${v}"></div>`).join('')}</div>`};
const panel=(id,title,unit,body)=>`<article class="panel" data-panel="${id}"><div class="panel-head"><h2>${title}</h2><span class="unit">${unit}</span></div>${body}</article>`;
async function refresh(){
  const data=await fetch('/dashboard/data?phase=PHASE_VALUE',{cache:'no-store'}).then(r=>r.json()); const p=data.panels;
  document.getElementById('meta').innerHTML=`Last ${data.meta.time_range_minutes} minutes · ${data.meta.records_in_window} records<br>Updated ${new Date(data.meta.generated_at).toLocaleTimeString()}`;
  document.getElementById('grid').innerHTML=
    panel('latency',p.latency.title,p.latency.unit,`<div class="metric">${fmt(p.latency.p95)} ms</div><div class="submetrics"><span>P50 <strong>${fmt(p.latency.p50)}</strong></span><span>P95 <strong>${fmt(p.latency.p95)}</strong></span><span>P99 <strong>${fmt(p.latency.p99)}</strong></span></div>${bars(p.latency.series)}${threshold(p.latency.p95,p.latency.threshold,'ms')}`)+
    panel('traffic',p.traffic.title,p.traffic.unit,`<div class="metric">${fmt(p.traffic.rate_per_minute,2)} rpm</div><div class="submetrics"><span>Requests <strong>${fmt(p.traffic.count)}</strong></span></div>${bars(p.traffic.series)}${threshold(p.traffic.rate_per_minute,p.traffic.threshold,'rpm')}`)+
    panel('errors',p.errors.title,p.errors.unit,`<div class="metric">${fmt(p.errors.error_rate_pct,2)}%</div><div class="submetrics"><span>Failures <strong>${p.errors.count}</strong></span><span>Types <strong>${Object.keys(p.errors.breakdown).length}</strong></span></div><div class="empty">${Object.keys(p.errors.breakdown).length?Object.entries(p.errors.breakdown).map(([k,v])=>`${k}: ${v}`).join(' · '):'No errors in selected window'}</div>${threshold(p.errors.error_rate_pct,p.errors.threshold,'%')}`)+
    panel('cost',p.cost.title,p.cost.unit,`<div class="metric">$${fmt(p.cost.total,4)}</div><div class="submetrics"><span>Total in selected window</span></div>${bars(p.cost.series)}${threshold(p.cost.total,p.cost.threshold,'USD')}`)+
    panel('tokens',p.tokens.title,p.tokens.unit,`<div class="dual"><div class="token">Input<b>${fmt(p.tokens.tokens_in)}</b></div><div class="token">Output<b>${fmt(p.tokens.tokens_out)}</b></div></div><div class="metric">${fmt(p.tokens.tokens_in+p.tokens.tokens_out)}</div>${threshold(Math.max(p.tokens.tokens_in,p.tokens.tokens_out),p.tokens.threshold,'tokens')}`)+
    panel('quality',p.quality.title,p.quality.unit,`<div class="metric">${fmt(p.quality.mean,3)}</div><div class="submetrics"><span>Samples <strong>${p.quality.samples}</strong></span></div><div class="gauge"><div style="width:${Math.min(100,p.quality.mean*100)}%"></div></div>${threshold(p.quality.mean,p.quality.threshold,'score')}`);
}
refresh().catch(e=>document.getElementById('grid').innerHTML=`<article class="panel"><h2>Dashboard error</h2><p>${e}</p></article>`);
setInterval(refresh,30000);
</script>
</body>
</html>""".replace("PHASE_VALUE", phase).replace("PHASE_LABEL", phase.upper())
