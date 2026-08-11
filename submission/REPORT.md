# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối: `5ba6472`
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 30/100
- Tổng số log records analyzed: 21
- Records thiếu required fields: 20
- Records thiếu enrichment/context: 20
- Unique correlation IDs found: 0
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: Chưa cung cấp

## 3. Logging và tracing

- Evidence correlation ID: `python scripts/validate_logs.py` báo `Unique correlation IDs found: 0`, chưa đạt yêu cầu propagation.
- Evidence PII redaction: `python scripts/validate_logs.py` báo `Potential PII leaks detected: 0` và `[PASSED] PII scrubbing`.
- Evidence trace waterfall: Chưa cung cấp.
- Giải thích một span đáng chú ý: Chưa cung cấp trace/span cụ thể.

Kết quả chi tiết:

```text
--- Lab Verification Results ---
Total log records analyzed: 21
Records with missing required fields: 20
Records with missing enrichment (context): 20
Unique correlation IDs found: 0
Potential PII leaks detected: 0

--- Grading Scorecard (Estimates) ---
- [FAILED] Missing required fields (ts, level, etc.)
- [FAILED] Correlation ID propagation (less than 2 unique IDs)
- [FAILED] Log enrichment (missing user_id_hash, etc.)
- [PASSED] PII scrubbing

Estimated Score: 30/100
```

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

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
