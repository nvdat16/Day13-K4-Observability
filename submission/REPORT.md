# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối: `5ba6472`
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

### Load Test Results (Checkpoint 2)
- **Tổng requests thành công**: 20+ requests
- **API Status**: 200 OK (tracing enabled)
- **Error Rate**: 0%

### Metrics sau Load Test (`GET /metrics`):
```json
{
  "traffic": 20,
  "latency_p50": 373.0,
  "latency_p95": 1149.0,
  "latency_p99": 1149.0,
  "avg_cost_usd": 0.0019,
  "total_cost_usd": 0.038,
  "tokens_in_total": 660,
  "tokens_out_total": 2404,
  "error_rate_pct": 0.0,
  "quality_avg": 0.88
}
```

### Log Sample (response_sent event):
```json
{
  "service": "api",
  "event": "response_sent",
  "correlation_id": "req-d2d5ab5d",
  "latency_ms": 1050,
  "tokens_in": 36,
  "tokens_out": 118,
  "cost_usd": 0.001878,
  "quality_score": 0.9,
  "user_id_hash": "2055254ee30a",
  "session_id": "s01",
  "feature": "qa",
  "model": "claude-sonnet-4-5",
  "env": "dev"
}
```

- **Điểm `validate_logs.py`**: 30/100 (baseline)
- **Số PII leak còn lại**: 0 (PII đã được redact)
- **Link/đường dẫn dashboard**: `config/dashboard.yaml` (validated: 6/6 panel)

## 3. Logging và tracing

### Logging Infrastructure
- **Correlation ID**: Được tạo tự động trong `CorrelationIdMiddleware`, propagate qua tất cả requests
- **PII Redaction**: Email, phone, credit card được redact tự động với pattern `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`

### Trace Metadata (Langfuse)
Mỗi trace bao gồm:
- `prompt_name`: Tên prompt từ `LANGFUSE_PROMPT_NAME`
- `prompt_label`: Label từ `LANGFUSE_PROMPT_LABEL`
- `prompt_version`: Phiên bản prompt
- `prompt_source`: Nguồn prompt (`langfuse`, `local`, `local-fallback`)
- `correlation_id`: ID để link với logs
- `session_id`: Session của user
- `user_id_hash`: User ID đã hash (không lộ PII)

### Evidence Logging
- Correlation IDs: `req-d2d5ab5d`, `req-36da0334`, `req-f4b24e01`, ... (20+ unique IDs)
- PII leaks: 0 (tất cả email/phone/credit card đã redact)
- Sample trace correlation: `req-d2d5ab5d` link giữa trace và log

### Metrics → Traces → Logs Flow
1. Request đến `/chat` → middleware tạo `correlation_id`
2. Langfuse trace bắt đầu với metadata
3. Agent xử lý và ghi response_sent log với cùng correlation_id
4. Metrics được tổng hợp từ response_sent logs

## 4. Prompt versioning

### Prompt Configuration
- **Prompt name**: `day13-chat` (từ `LANGFUSE_PROMPT_NAME`)
- **Default label**: `production` (từ `LANGFUSE_PROMPT_LABEL`)

### Để hoàn thành prompt versioning:
1. Tạo prompt `day13-chat` trên Langfuse dashboard
2. Tạo **Version 1**: gắn labels `baseline` và `production`
3. Tạo **Version 2**: thay đổi nhỏ về format, gắn label `candidate`
4. Chạy request với `LANGFUSE_PROMPT_LABEL=baseline`
5. Chạy request với `LANGFUSE_PROMPT_LABEL=candidate`
6. Đổi `production` label sang Version 2
7. Rollback `production` về Version 1

### Expected Trace Metadata:
```
prompt_name: day13-chat
prompt_label: production (hoặc baseline/candidate)
prompt_version: 1 hoặc 2
prompt_source: langfuse
```

### Evidence cần nộp:
- Ảnh hai prompt version trên Langfuse
- Hai trace IDs từ hai label khác nhau
- Ảnh trước/sau khi đổi label hoặc rollback

### Note:
Langfuse SDK đang dùng fallback local do API changes. Để có traces thực, cần tạo prompt trên Langfuse dashboard và đảm bảo credentials đúng.

## 5. Dashboard, SLO và alerts

### Checkpoint 2 - Thành viên B (SRE & Alerts Engineer)

#### Kết quả `validate_dashboard.py`:
```
HỢP LỆ: 6/6 panel có trong dashboard contract.
```

#### Dashboard Configuration (`config/dashboard.yaml`):

| Panel | Title | Events | Fields | Aggregations | Threshold |
|-------|-------|--------|--------|--------------|-----------|
| latency | Latency percentiles | response_sent | latency_ms | p50, p95, p99 | P95 ≤ 3000ms |
| traffic | Request traffic | request_received | event | count, rate_per_minute | Rate ≥ 1 rpm |
| errors | Error rate and breakdown | request_received, request_failed | error_type | error_rate_pct, count_by_value | Error rate ≤ 2% |
| cost | Cost over time | response_sent | cost_usd | sum_by_minute, total | Total ≤ $2.50 |
| tokens | Input and output tokens | response_sent | tokens_in, tokens_out | sum_by_field | ≤ 50000 tokens |
| quality | Quality proxy | response_sent | quality_score | mean | Mean ≥ 0.75 |

#### SLO Configuration (`config/slo.yaml`):

| SLI | Objective | Target |
|-----|-----------|--------|
| latency_p95_ms | 3000ms | 99.5% |
| error_rate_pct | 2% | 99.0% |
| daily_cost_usd | $2.50 | 100% |
| quality_score_avg | 0.75 | 95.0% |

**Lý do chọn threshold:**
- **Latency P95 ≤ 3000ms**: Threshold này đảm bảo hầu hết người dùng có trải nghiệm tốt, chỉ 1% worst cases vượt ngưỡng.
- **Error rate ≤ 2%**: SLO 99% availability là standard cho production services.
- **Cost ≤ $2.50/day**: Dựa trên fake LLM, chi phí thực tế rất thấp nhưng đặt threshold để phát hiện anomalies.
- **Quality ≥ 0.75**: Đảm bảo response có đủ context và độ dài phù hợp.

#### Alert Rules (`config/alert_rules.yaml`):

| Alert Name | Severity | Condition | SLI | Owner |
|------------|----------|-----------|-----|-------|
| High Latency P95 | warning | P95 > 3000ms for 5 min | latency_p95_ms | sre-team |
| High Error Rate | critical | Error rate > 2% for 2 min | error_rate_pct | sre-team |
| Cost Budget Exceeded | warning | Cost > $2.50/hr for 10 min | daily_cost_usd | platform-team |
| Low Quality Score | warning | Quality < 0.75 for 5 min | quality_score_avg | ml-team |

#### Alert Runbook Summary:

- **Alert 1 (High Latency)**: Kiểm tra dashboard → Mở trace chậm → Tìm log với correlation ID → Tắt incident hoặc rollback prompt
- **Alert 2 (Error Rate)**: Kiểm tra error breakdown → Tìm log request_failed → Kiểm tra Langfuse credentials → Restart API
- **Alert 3 (Cost Spike)**: Kiểm tra cost panel → Kiểm tra tokens → Tắt cost_spike incident → Giảm rate limit
- **Alert 4 (Quality)**: Kiểm tra quality panel → Mở trace chất lượng thấp → Kiểm tra PII redaction → Rollback prompt

#### Evidence Dashboard:
- Dashboard contract validator: **PASSED (6/6 panel)**
- Full evidence trong `submission/evidence/dashboard/`

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| **Thành viên B (SRE)** | Alert Rules, SLO, Dashboard Config, Alert Runbook | Fix Langfuse SDK v3 compatibility | |

## 8. Checkpoint 2 Summary

### ✅ Đã hoàn thành (Thành viên B):
- [x] Dashboard Contract: 6/6 panel validated
- [x] SLO Configuration: 4 SLIs với measurement methods
- [x] Alert Rules: 4 alerts (Latency, Error, Cost, Quality)
- [x] Alert Runbook: Chi tiết với 3 bước kiểm tra và mitigation
- [x] Metrics: 20+ requests thành công, error_rate: 0%
- [x] Traces: Langfuse tracing enabled, metadata captured
- [x] Logs: Correlation ID propagation, PII redaction working

### ⚠️ Cần hoàn thành:
- [ ] Prompt versioning trên Langfuse dashboard (v1, v2, labels)
- [ ] Rollback evidence screenshots
- [ ] Dashboard runtime screenshots
- [ ] Trace screenshots với prompt metadata

### Files đã tạo/sửa:
- `config/alert_rules.yaml` - 4 alert rules
- `config/slo.yaml` - SLO chi tiết với measurement methods
- `docs/alerts.md` - Alert runbook đầy đủ
- `app/agent.py` - Fix Langfuse SDK v3 compatibility
- `submission/REPORT.md` - Cập nhật evidence
