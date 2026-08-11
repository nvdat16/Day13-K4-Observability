# Alert Runbook - Day 13 Observability Lab

Mỗi alert dựa trên triệu chứng người dùng và SLO đã định nghĩa trong `config/slo.yaml`.

---

## Alert 1: High Latency P95

**#alert-1**

- **Tên:** High Latency P95
- **Severity:** warning
- **SLI/SLO liên quan:**
  - SLI: `latency_p95_ms`
  - SLO: 99.5% requests với P95 latency < 3000ms
- **Điều kiện và thời gian duy trì:** P95 latency > 3000ms trong 5 phút liên tục
- **Ảnh hưởng tới người dùng:** API phản hồi chậm, người dùng có thể timeout hoặc từ bỏ request

### Ba bước kiểm tra đầu tiên:

1. **Kiểm tra dashboard latency panel**
   - Mở dashboard, xác nhận P95 đang > 3000ms
   - So sánh với baseline: P50 và P99 để xác định extent

2. **Mở một trace chậm trong Langfuse**
   - Tìm trace có `latency_ms` cao
   - Kiểm tra thời gian từng span (RAG retrieval, LLM call)

3. **Kiểm tra log với correlation ID**
   - Tìm log line `response_sent` với cùng correlation ID
   - Xác định component nào gây chậm

### Mitigation tạm thời:

1. Kiểm tra incident đang active: `GET /incidents`
2. Nếu có `rag_slow` incident: tắt ngay
3. Nếu không có incident:
   - Rollback prompt về version ổn định
   - Giảm concurrency của load test
4. Thông báo cho người dùng về tình trạng

### Owner: sre-team

---

## Alert 2: High Error Rate

**#alert-2**

- **Tên:** High Error Rate
- **Severity:** critical
- **SLI/SLO liên quan:**
  - SLI: `error_rate_pct`
  - SLO: 99.0% requests thành công
- **Điều kiện và thời gian duy trì:** Error rate > 2% trong 2 phút liên tục
- **Ảnh hưởng tới người dùng:** Người dùng nhận được HTTP 500 hoặc error response

### Ba bước kiểm tra đầu tiên:

1. **Kiểm tra dashboard error panel**
   - Xác nhận error rate > 2%
   - Kiểm tra breakdown theo `error_type` để xác định loại lỗi

2. **Kiểm tra log request_failed**
   - Tìm các log line với `event: request_failed`
   - Đọc `payload.detail` và `error_type` để xác định nguyên nhân

3. **Mở trace của request thất bại**
   - Tìm trace với metadata chứa error
   - Kiểm tra stack trace trong log cùng correlation ID

### Mitigation tạm thời:

1. Kiểm tra `tool_fail` incident: `POST /incidents/tool_fail/disable`
2. Kiểm tra Langfuse availability và credentials
3. Restart API nếu cần thiết
4. Escalate lên backend team nếu error không liên quan đến incident

### Owner: sre-team

---

## Alert 3: Cost Budget Exceeded

**#alert-3**

- **Tên:** Cost Budget Exceeded
- **Severity:** warning
- **SLI/SLO liên quan:**
  - SLI: `daily_cost_usd`
  - SLO: Under $2.50 per day
- **Điều kiện và thời gian duy trì:** Cost > $2.50/giờ trong 10 phút liên tục
- **Ảnh hưởng tới người dùng:** Chi phí vượt ngân sách, có thể cần tạm dừng service

### Ba bước kiểm tra đầu tiên:

1. **Kiểm tra dashboard cost panel**
   - Xác nhận cost trending cao hơn threshold
   - Kiểm tra cost theo từng request/response

2. **Kiểm tra tokens panel**
   - Xem `tokens_in` và `tokens_out` có bất thường không
   - Kiểm tra xem có request nào với số tokens quá lớn không

3. **Kiểm tra incident `cost_spike`**
   - Tìm xem có scenario nào đang chạy không

### Mitigation tạm thời:

1. Tắt `cost_spike` incident nếu đang active
2. Giảm rate limit cho requests
3. Review xem có request nào anomalous
4. Consider tạm dừng non-critical features

### Owner: platform-team

---

## Alert 4: Low Quality Score

**#alert-4**

- **Tên:** Low Quality Score
- **Severity:** warning
- **SLI/SLO liên quan:**
  - SLI: `quality_score_avg`
  - SLO: 95% requests với quality >= 0.75
- **Điều kiện và thời gian duy trì:** Quality score avg < 0.75 trong 5 phút liên tục
- **Ảnh hưởng tới người dùng:** Response không đạt chất lượng kỳ vọng

### Ba bước kiểm tra đầu tiên:

1. **Kiểm tra dashboard quality panel**
   - Xác nhận quality score avg < 0.75
   - So sánh với baseline

2. **Mở trace với quality thấp**
   - Kiểm tra metadata của trace
   - Xem response có chứa `[REDACTED` không (sẽ làm giảm score)

3. **Kiểm tra RAG retrieval**
   - Xem docs được retrieve có liên quan không
   - Kiểm tra mock_rag đang return đúng docs không

### Mitigation tạm thời:

1. Kiểm tra PII redaction không hoạt động quá mức
2. Rollback prompt về version ổn định
3. Verify RAG retrieval đang hoạt động đúng
4. Review mock_llm response

### Owner: ml-team
