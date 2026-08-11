# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: high_latency_p95
- Severity: warning
- SLI/SLO liên quan: latency_p95_ms, mục tiêu P95 <= 3000 ms
- Điều kiện và thời gian duy trì: latency_p95_ms > 3000 trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận phản hồi chậm, dễ timeout hoặc bỏ phiên chat.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard kiểm tra P50/P95/P99 trong 15 phút gần nhất để xác nhận latency tăng thật.
  2. Mở Langfuse Tracing, lọc trace chậm và xem waterfall để xác định span nào chiếm nhiều thời gian.
  3. Lấy correlation_id trong trace và grep `data/logs.jsonl` để đối chiếu request, feature, session và payload đã redact.
- Mitigation tạm thời: Giảm concurrency, tắt incident hoặc tính năng gây chậm, chuyển sang prompt/model rẻ hơn nếu latency do generation.
- Owner: on-call-engineer

## Alert 2

- Tên: elevated_error_rate
- Severity: critical
- SLI/SLO liên quan: error_rate_pct, mục tiêu error rate <= 2%
- Điều kiện và thời gian duy trì: error_rate_pct > 5 trong 3 phút
- Ảnh hưởng tới người dùng: Một phần request trả HTTP 500 hoặc không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard kiểm tra error rate và breakdown theo error_type.
  2. Mở Langfuse Tracing, lọc trace status ERROR để xem lỗi xuất hiện ở span nào.
  3. Dùng correlation_id hoặc x-request-id để tìm log `request_failed` trong `data/logs.jsonl`.
- Mitigation tạm thời: Rollback thay đổi gần nhất, tắt scenario incident, hoặc trả fallback response cho feature bị lỗi.
- Owner: on-call-engineer

## Alert 3

- Tên: cost_budget_exceeded
- Severity: warning
- SLI/SLO liên quan: daily_cost_usd, mục tiêu tổng chi phí <= 2.5 USD/ngày
- Điều kiện và thời gian duy trì: daily_cost_usd > 2.5
- Ảnh hưởng tới người dùng: Hệ thống có nguy cơ bị giới hạn ngân sách hoặc phải giảm chất lượng phục vụ.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard kiểm tra cost over time và tổng token input/output.
  2. Mở Langfuse Tracing, lọc trace cost cao để xem feature, model và prompt liên quan.
  3. Đối chiếu correlation_id với log để xác định cohort/session tạo chi phí bất thường.
- Mitigation tạm thời: Giới hạn request rate, giảm max output, chuyển prompt production về version ngắn hơn hoặc chặn input quá dài.
- Owner: team-lead
