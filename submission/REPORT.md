# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: K4 Observability — nhóm 3 thành viên
- Repository URL: `https://github.com/nvdat16/Day13-K4-Observability`
- Commit SHA cuối: nộp theo kết quả `git rev-parse HEAD` cùng repository URL trên Codelabs
- Thành viên và vai trò:
  - Thành viên A — Tech Lead/Backend Engineer: CP1 middleware, correlation ID và log enrichment.
  - Thành viên B — SRE & Alerts Engineer: CP2 Langfuse, prompt versioning, SLO, alert rules và runbook.
  - Thành viên C — QA & Chief Investigator: dashboard runtime/spec, load test, practice/challenge CP3, evidence và báo cáo.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces trên Langfuse: 211
- Tổng số log records analyzed: 96
- Records thiếu required fields: 0
- Records thiếu enrichment/context: 0
- Unique correlation IDs found: 44
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `http://127.0.0.1:8000/dashboard`; source `app/dashboard.py`

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/cp1-redacted-correlation-log.png`; `python scripts/validate_logs.py` báo `Unique correlation IDs found: 44`.
- Evidence PII redaction: `submission/evidence/cp1-redacted-correlation-log.png`; `python scripts/validate_logs.py` báo `Potential PII leaks detected: 0` và `[PASSED] PII scrubbing`.
- Evidence trace waterfall: `submission/evidence/cp2-langfuse-trace-list.png`
- Giải thích một span đáng chú ý: Trace `0eaae54da98abc948de414e3d8a796d2` có span `run` mất khoảng 2.88s, gắn session `s10`, user hash `105a9cef3903`, tags `lab`, `qa`, `claude-sonnet-4-5`, và metadata `correlation_id=req-596f27bd` để đối chiếu với log thô.

Kết quả chi tiết:

```text
--- Lab Verification Results ---
Total log records analyzed: 96
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 44
Potential PII leaks detected: 0

--- Grading Scorecard (Estimates) ---
- [PASSED] Basic JSON schema
- [PASSED] Correlation ID propagation
- [PASSED] Log enrichment
- [PASSED] PII scrubbing

Estimated Score: 100/100
```

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: v1 — `baseline`, hiện có label `production`
- Version/label candidate: v2 — `candidate`, `latest`
- Trace ID của mỗi version: v1 `291b603806d3da44581dc132d262fd16`; v2 `401ce1db601b1bd69f166a75f425aec8`
- Bằng chứng đổi label hoặc rollback: sau khi giữ v2 là `candidate`, label `production` đang trỏ lại v1. Chi tiết tại [`evidence/cp2-prompt-versioning.md`](evidence/cp2-prompt-versioning.md).

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel có trong dashboard contract.
- Evidence dashboard: [`evidence/cp2-dashboard-baseline.png`](evidence/cp2-dashboard-baseline.png), [`evidence/cp2-dashboard-incident.png`](evidence/cp2-dashboard-incident.png), [`evidence/cp2-dashboard-runtime.png`](evidence/cp2-dashboard-runtime.png) và [`evidence/cp2-dashboard-validator.png`](evidence/cp2-dashboard-validator.png).
- SLO đã chọn và lý do: P95 latency <= 3000 ms, error rate <= 2%, daily cost <= 2.5 USD và quality score trung bình >= 0.75 để theo dõi trải nghiệm người dùng, độ ổn định, chi phí và chất lượng phản hồi.
- Alert rules và runbook: `config/alert_rules.yaml`, `docs/alerts.md`

Câu hỏi phản biện CP2: Alert rules nên symptom-based vì mục tiêu của cảnh báo là phát hiện tác động mà người dùng thật sự cảm nhận được như phản hồi chậm, nhiều HTTP 500, chi phí tăng bất thường hoặc chất lượng giảm. Nếu alert dựa trên tên hàm hoặc lỗi implementation cụ thể, cảnh báo dễ bị nhiễu khi refactor hoặc đổi kiến trúc dù trải nghiệm người dùng không đổi. Symptom-based alerts ổn định hơn, ít false positive hơn và giúp on-call ưu tiên các sự cố có tác động thực tế.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1` (K4), incident `rag_slow`, affected feature `monitoring`.
- Triệu chứng từ metrics: baseline P95 `4192 ms`; practice P95 `11079 ms` (tăng khoảng 164%); lượt challenge tách biệt có P50 `3727 ms`, P95/P99 `10270 ms`, không có error. Latency là tín hiệu bất thường chính.
- Trace ID liên quan: `5e42ed7ffa6893b8bcec4d247d9ee4c6`; trace `3.765 s`, trong đó span `retrieve` chiếm `2.503 s` (~66.5%).
- Log line/correlation ID liên quan: `req-0ab75f70`, session `k4-challenge-s01`; log `response_sent.latency_ms=3764`. Trace mang cùng correlation tag.
- Root cause: khi incident `rag_slow` bật, `app/mock_rag.py::retrieve` chạy blocking `time.sleep(2.5)` trước khi truy xuất tài liệu.
- Fix action: tắt incident ngay; loại bỏ blocking delay. Với retriever thật, áp dụng timeout, bounded retry, circuit breaker và fallback an toàn.
- Preventive measure: giữ span `retrieve` và correlation tag, cảnh báo khi P95 vượt `3000 ms` trong cửa sổ bền vững, và chạy so sánh baseline/incident trong regression test. Evidence chi tiết: [`evidence/cp3-investigation.md`](evidence/cp3-investigation.md).

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nguyễn Văn Đạt - 2A202601968 | Middleware, correlation ID, enrichment, PII-safe logging | [`6e2ff5e`](https://github.com/nvdat16/Day13-K4-Observability/commit/6e2ff5e) | Correlation ID phải được bind trước log đầu tiên và PII phải scrub trước JSON renderer. |
| Mai Văn Phương - 2A202601418 | Langfuse/prompt v1-v2, SLO, alert rules, runbook | [`dda646f`](https://github.com/nvdat16/Day13-K4-Observability/commit/dda646f) | Alert nên symptom-based và trace cần metadata prompt/correlation có thể kiểm chứng. |
| Nguyễn Đặng Thành Vinh - 2A202602021 | Dashboard 6 panel, load test, practice/challenge, Metrics → Traces → Logs, evidence và report | [`9ba5845`](https://github.com/nvdat16/Day13-K4-Observability/commit/9ba5845) | P95 phản ánh tail latency tốt hơn average; chỉ kết luận root cause khi metric, span và log cùng khớp. |
