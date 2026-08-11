# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối: `5ba6472`
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số log records analyzed: 43
- Records thiếu required fields: 0
- Records thiếu enrichment/context: 0
- Unique correlation IDs found: 20
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: Chưa cung cấp

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/cp1-redacted-correlation-log.png`; `python scripts/validate_logs.py` báo `Unique correlation IDs found: 20`.
- Evidence PII redaction: `submission/evidence/cp1-redacted-correlation-log.png`; `python scripts/validate_logs.py` báo `Potential PII leaks detected: 0` và `[PASSED] PII scrubbing`.
- Evidence trace waterfall: `submission/evidence/cp2-langfuse-waterfall.png`
- Giải thích một span đáng chú ý: Trace `0eaae54da98abc948de414e3d8a796d2` có span `run` mất khoảng 2.88s, gắn session `s10`, user hash `105a9cef3903`, tags `lab`, `qa`, `claude-sonnet-4-5`, và metadata `correlation_id=req-596f27bd` để đối chiếu với log thô.

Kết quả chi tiết:

```text
--- Lab Verification Results ---
Total log records analyzed: 43
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 20
Potential PII leaks detected: 0

--- Grading Scorecard (Estimates) ---
- [PASSED] Basic JSON schema
- [PASSED] Correlation ID propagation
- [PASSED] Log enrichment
- [PASSED] PII scrubbing

Estimated Score: 100/100
```

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel có trong dashboard contract.
- Evidence dashboard: `submission/evidence/cp2-langfuse-trace-list.png`, `submission/evidence/cp2-langfuse-waterfall.png`
- SLO đã chọn và lý do: P95 latency <= 3000 ms, error rate <= 2%, daily cost <= 2.5 USD và quality score trung bình >= 0.75 để theo dõi trải nghiệm người dùng, độ ổn định, chi phí và chất lượng phản hồi.
- Alert rules và runbook: `config/alert_rules.yaml`, `docs/alerts.md`

Câu hỏi phản biện CP2: Alert rules nên symptom-based vì mục tiêu của cảnh báo là phát hiện tác động mà người dùng thật sự cảm nhận được như phản hồi chậm, nhiều HTTP 500, chi phí tăng bất thường hoặc chất lượng giảm. Nếu alert dựa trên tên hàm hoặc lỗi implementation cụ thể, cảnh báo dễ bị nhiễu khi refactor hoặc đổi kiến trúc dù trải nghiệm người dùng không đổi. Symptom-based alerts ổn định hơn, ít false positive hơn và giúp on-call ưu tiên các sự cố có tác động thực tế.

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
| | | | |
