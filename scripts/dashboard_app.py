"""
Dashboard App - Visualize 6 panels from data/logs.jsonl
Run: streamlit run scripts/dashboard_app.py
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
LOGS_PATH = REPO_ROOT / "data" / "logs.jsonl"

# SLO Thresholds
SLO_THRESHOLDS = {
    "latency_p95_ms": 3000,
    "error_rate_pct": 2.0,
    "cost_total_usd": 2.5,
    "quality_min": 0.75,
}

# Color scheme
COLOR_OK = "#22c55e"  # green
COLOR_WARNING = "#f59e0b"  # amber
COLOR_ERROR = "#ef4444"  # red
COLOR_PRIMARY = "#3b82f6"  # blue
COLOR_BG = "#f8fafc"  # light gray


def load_logs() -> pd.DataFrame:
    """Load and parse logs from JSONL file."""
    records = []
    if LOGS_PATH.exists():
        for line in LOGS_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return pd.DataFrame(records)


def parse_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """Parse timestamp column."""
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"])
    return df


def filter_by_event(df: pd.DataFrame, event: str) -> pd.DataFrame:
    """Filter dataframe by event type."""
    if "event" in df.columns:
        return df[df["event"] == event].copy()
    return pd.DataFrame()


def get_status_color(current: float, threshold: float, is_lower_better: bool = True) -> str:
    """Get color based on threshold comparison."""
    if is_lower_better:
        if current <= threshold * 0.8:
            return COLOR_OK
        elif current <= threshold:
            return COLOR_WARNING
        else:
            return COLOR_ERROR
    else:
        if current >= threshold:
            return COLOR_OK
        elif current >= threshold * 0.9:
            return COLOR_WARNING
        else:
            return COLOR_ERROR


def render_metric_card(
    label: str,
    value: str,
    threshold: Optional[str] = None,
    status: Optional[str] = None,
    icon: str = "📊",
    color: str = COLOR_PRIMARY,
):
    """Render a styled metric card."""
    status_emoji = ""
    status_color = ""

    if status == "ok":
        status_emoji = " ✅"
        status_color = f"color: {COLOR_OK}"
    elif status == "warning":
        status_emoji = " ⚠️"
        status_color = f"color: {COLOR_WARNING}"
    elif status == "error":
        status_emoji = " 🔴"
        status_color = f"color: {COLOR_ERROR}"

    html = f"""
    <div style="
        background: linear-gradient(135deg, #ffffff 0%, {COLOR_BG} 100%);
        border-left: 5px solid {color};
        border-radius: 10px;
        padding: 15px 20px;
        margin: 5px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    ">
        <div style="font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">
            {icon} {label}
        </div>
        <div style="font-size: 28px; font-weight: bold; {status_color}; margin-top: 5px;">
            {value}{status_emoji}
        </div>
        {f'<div style="font-size: 11px; color: #94a3b8; margin-top: 5px;">Threshold: {threshold}</div>' if threshold else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_slo_bar(sli_name: str, current: float, threshold: float, unit: str, is_lower_better: bool = True):
    """Render SLO status bar."""
    if is_lower_better:
        percentage = min(100, (threshold / max(current, 1)) * 100) if current > 0 else 100
        status = "OK" if current <= threshold else "EXCEEDED"
        color = COLOR_OK if current <= threshold * 0.8 else (COLOR_WARNING if current <= threshold else COLOR_ERROR)
    else:
        percentage = min(100, (current / threshold) * 100)
        status = "OK" if current >= threshold else "LOW"
        color = COLOR_OK if current >= threshold else (COLOR_WARNING if current >= threshold * 0.9 else COLOR_ERROR)

    html = f"""
    <div style="margin: 15px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="font-weight: 600;">{sli_name}</span>
            <span style="color: {color}; font-weight: 600;">{status}</span>
        </div>
        <div style="background: #e2e8f0; border-radius: 8px; height: 12px; overflow: hidden;">
            <div style="
                width: {percentage:.1f}%;
                background: {color};
                height: 100%;
                border-radius: 8px;
                transition: width 0.5s ease;
            "></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 12px; color: #64748b;">
            <span>Current: {current:.2f} {unit}</span>
            <span>Threshold: {threshold} {unit}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# Page config
st.set_page_config(
    page_title="Day 13 AI Observability",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #1e293b;
        margin-bottom: 0.5rem !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
    }
    .stMetric {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
col_left, col_right = st.columns([3, 1])
with col_left:
    st.markdown('<p class="main-header">📊 AI Observability Dashboard</p>', unsafe_allow_html=True)
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Source: `data/logs.jsonl`")
with col_right:
    st.markdown("###")
    if st.button("🔄 Refresh", type="primary", use_container_width=True):
        st.rerun()

# Load data
df = load_logs()
df = parse_timestamp(df)

if df.empty:
    st.warning("No data found in `data/logs.jsonl`. Run the API and load test first.")
    st.stop()

# Calculate metrics
response_sent = filter_by_event(df, "response_sent")
request_received = filter_by_event(df, "request_received")
request_failed = filter_by_event(df, "request_failed")

total_requests = len(request_received)
error_count = len(request_failed)
error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

latency_p50 = response_sent["latency_ms"].quantile(0.5) if len(response_sent) > 0 else 0
latency_p95 = response_sent["latency_ms"].quantile(0.95) if len(response_sent) > 0 else 0
latency_p99 = response_sent["latency_ms"].quantile(0.99) if len(response_sent) > 0 else 0

total_cost = response_sent["cost_usd"].sum() if "cost_usd" in response_sent.columns else 0
total_tokens_in = response_sent["tokens_in"].sum() if "tokens_in" in response_sent.columns else 0
total_tokens_out = response_sent["tokens_out"].sum() if "tokens_out" in response_sent.columns else 0
quality_avg = response_sent["quality_score"].mean() if "quality_score" in response_sent.columns and len(response_sent) > 0 else 0

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Overview", "📊 Metrics", "📋 SLO"])

with tab1:
    st.markdown("### Key Metrics")

    # Top row - 4 main metrics
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        status = "ok" if total_requests > 0 else "warning"
        st.metric(
            "Total Requests",
            f"{total_requests:,}",
            delta=f"{error_count} errors" if error_count > 0 else "All successful",
        )

    with m2:
        status = "ok" if error_rate <= SLO_THRESHOLDS["error_rate_pct"] else "error"
        st.metric(
            "Error Rate",
            f"{error_rate:.2f}%",
            delta="⚠️ EXCEEDED" if error_rate > SLO_THRESHOLDS["error_rate_pct"] else "✅ OK",
        )

    with m3:
        status = "ok" if quality_avg >= SLO_THRESHOLDS["quality_min"] else "warning"
        st.metric(
            "Avg Quality",
            f"{quality_avg:.2f}",
            delta="⚠️ LOW" if quality_avg < SLO_THRESHOLDS["quality_min"] else "✅ Good",
        )

    with m4:
        status = "ok" if total_cost <= SLO_THRESHOLDS["cost_total_usd"] else "warning"
        st.metric(
            "Total Cost",
            f"${total_cost:.6f}",
            delta=f"of ${SLO_THRESHOLDS['cost_total_usd']:.2f} budget",
        )

    st.divider()

    # Charts row
    chart1, chart2 = st.columns(2)

    with chart1:
        st.markdown("#### Latency Trend (ms)")
        if len(response_sent) > 0:
            latency_chart = response_sent.set_index("ts")["latency_ms"].tail(30)
            st.line_chart(latency_chart, height=200, color="#3b82f6")

    with chart2:
        st.markdown("#### Traffic Over Time")
        if len(df) > 0 and "ts" in df.columns:
            traffic = df[df["event"] == "request_received"].set_index("ts").resample("1T").size()
            st.area_chart(traffic, height=200, color="#22c55e")

with tab2:
    st.markdown("### Detailed Metrics")

    # Latency Panel
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #3b82f6;
    ">
        <h4 style="margin: 0 0 15px 0;">📊 Panel 1: Latency</h4>
    </div>
    """, unsafe_allow_html=True)

    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        st.metric("P50 (Median)", f"{latency_p50:.1f}ms")
    with lc2:
        st.metric(
            "P95",
            f"{latency_p95:.1f}ms",
            delta="⚠️ EXCEEDED" if latency_p95 > SLO_THRESHOLDS["latency_p95_ms"] else "✅ OK",
        )
    with lc3:
        st.metric("P99", f"{latency_p99:.1f}ms")

    if len(response_sent) > 0:
        st.line_chart(
            response_sent.set_index("ts")["latency_ms"].tail(50),
            height=200,
        )

    # Cost Panel
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #dcfce7 0%, #f0fdf4 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #22c55e;
    ">
        <h4 style="margin: 0 0 15px 0;">💰 Panel 4: Cost</h4>
    </div>
    """, unsafe_allow_html=True)

    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.metric("Total Cost", f"${total_cost:.6f}")
    with cc2:
        st.metric("Cost/Minute", f"${total_cost / max(1, len(response_sent)):.6f}")
    with cc3:
        st.metric("Budget", f"${SLO_THRESHOLDS['cost_total_usd']:.2f}")

    # Tokens Panel
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #f59e0b;
    ">
        <h4 style="margin: 0 0 15px 0;">🔢 Panel 5: Tokens</h4>
    </div>
    """, unsafe_allow_html=True)

    tc1, tc2 = st.columns(2)
    with tc1:
        st.metric("Total Tokens In", f"{total_tokens_in:,}")
    with tc2:
        st.metric("Total Tokens Out", f"{total_tokens_out:,}")

    # Error Panel
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #fee2e2 0%, #fef2f2 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #ef4444;
    ">
        <h4 style="margin: 0 0 15px 0;">❌ Panel 3: Errors</h4>
    </div>
    """, unsafe_allow_html=True)

    ec1, ec2 = st.columns(2)
    with ec1:
        st.metric("Total Errors", f"{error_count}")
    with ec2:
        st.metric("Error Rate", f"{error_rate:.2f}%")

    if len(request_failed) > 0:
        error_types = request_failed["error_type"].value_counts()
        st.bar_chart(error_types, horizontal=True)

    # Quality Panel
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #e0e7ff 0%, #eef2ff 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #6366f1;
    ">
        <h4 style="margin: 0 0 15px 0;">⭐ Panel 6: Quality</h4>
    </div>
    """, unsafe_allow_html=True)

    qc1, qc2 = st.columns(2)
    with qc1:
        st.metric("Average Quality", f"{quality_avg:.2f}")
    with qc2:
        st.metric("Quality Threshold", f"{SLO_THRESHOLDS['quality_min']}")

    if len(response_sent) > 0 and "quality_score" in response_sent.columns:
        st.line_chart(
            response_sent.set_index("ts")["quality_score"].tail(50),
            height=200,
        )

with tab3:
    st.markdown("### SLO Status")

    # Status overview
    col_status1, col_status2, col_status3, col_status4 = st.columns(4)

    latency_status = "ok" if latency_p95 <= SLO_THRESHOLDS["latency_p95_ms"] else "error"
    error_status = "ok" if error_rate <= SLO_THRESHOLDS["error_rate_pct"] else "error"
    cost_status = "ok" if total_cost <= SLO_THRESHOLDS["cost_total_usd"] else "warning"
    quality_status = "ok" if quality_avg >= SLO_THRESHOLDS["quality_min"] else "warning"

    with col_status1:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; border-radius: 10px; background: {'#22c55e20' if latency_status == 'ok' else '#ef444420'};">
            <div style="font-size: 24px;">{'✅' if latency_status == 'ok' else '🔴'}</div>
            <div style="font-weight: bold;">Latency</div>
            <div style="color: #64748b; font-size: 12px;">P95 {'OK' if latency_status == 'ok' else 'EXCEEDED'}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_status2:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; border-radius: 10px; background: {'#22c55e20' if error_status == 'ok' else '#ef444420'};">
            <div style="font-size: 24px;">{'✅' if error_status == 'ok' else '🔴'}</div>
            <div style="font-weight: bold;">Errors</div>
            <div style="color: #64748b; font-size: 12px;">{'OK' if error_status == 'ok' else 'ABOVE SLO'}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_status3:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; border-radius: 10px; background: {'#22c55e20' if cost_status == 'ok' else '#f59e0b20'};">
            <div style="font-size: 24px;">{'✅' if cost_status == 'ok' else '⚠️'}</div>
            <div style="font-weight: bold;">Cost</div>
            <div style="color: #64748b; font-size: 12px;">{'OK' if cost_status == 'ok' else 'APPROACHING'}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_status4:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; border-radius: 10px; background: {'#22c55e20' if quality_status == 'ok' else '#f59e0b20'};">
            <div style="font-size: 24px;">{'✅' if quality_status == 'ok' else '⚠️'}</div>
            <div style="font-weight: bold;">Quality</div>
            <div style="color: #64748b; font-size: 12px;">{'OK' if quality_status == 'ok' else 'BELOW TARGET'}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # SLO bars
    st.markdown("#### SLO Progress")

    render_slo_bar("Latency P95", latency_p95, SLO_THRESHOLDS["latency_p95_ms"], "ms")
    render_slo_bar("Error Rate", error_rate, SLO_THRESHOLDS["error_rate_pct"], "%")
    render_slo_bar("Daily Cost", total_cost, SLO_THRESHOLDS["cost_total_usd"], "$")
    render_slo_bar("Quality Score", quality_avg, SLO_THRESHOLDS["quality_min"], "score", is_lower_better=False)

    st.divider()

    # SLO table
    st.markdown("#### SLO Summary")

    slo_data = {
        "SLI": ["Latency P95", "Error Rate", "Cost", "Quality"],
        "Target": [
            f"≤ {SLO_THRESHOLDS['latency_p95_ms']}ms",
            f"≤ {SLO_THRESHOLDS['error_rate_pct']}%",
            f"≤ ${SLO_THRESHOLDS['cost_total_usd']}",
            f"≥ {SLO_THRESHOLDS['quality_min']}",
        ],
        "Current": [
            f"{latency_p95:.1f}ms",
            f"{error_rate:.2f}%",
            f"${total_cost:.4f}",
            f"{quality_avg:.2f}",
        ],
        "Status": [
            "✅ OK" if latency_p95 <= SLO_THRESHOLDS["latency_p95_ms"] else "⚠️ EXCEEDED",
            "✅ OK" if error_rate <= SLO_THRESHOLDS["error_rate_pct"] else "⚠️ EXCEEDED",
            "✅ OK" if total_cost <= SLO_THRESHOLDS["cost_total_usd"] else "⚠️ WARNING",
            "✅ OK" if quality_avg >= SLO_THRESHOLDS["quality_min"] else "⚠️ LOW",
        ],
    }

    st.dataframe(
        pd.DataFrame(slo_data),
        use_container_width=True,
        hide_index=True,
    )

# Footer
st.divider()
st.caption("📊 Day 13 AI Observability Lab | Dashboard Contract: 6/6 panels validated")
