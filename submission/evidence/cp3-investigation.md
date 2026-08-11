# CP3 Incident Investigation Evidence

Generated on 2026-08-11 (Asia/Ho_Chi_Minh). No API key or raw PII is included.

## Challenge

- Cohort: `K4`
- Challenge ID: `day13-k4-observability-v1`
- Released incident: `rag_slow`
- Affected feature: `monitoring`
- Challenge threshold: `2000 ms`
- Commands:

  ```bash
  python scripts/inject_incident.py
  python scripts/load_test.py --challenge --concurrency 5
  python scripts/inject_incident.py --disable
  ```

## Metrics evidence

- Baseline, 10 requests: P50 `1302 ms`, P95 `4192 ms`, P99 `4192 ms`, no errors.
- Practice after enabling `rag_slow`: P50 `4192 ms`, P95 `11079 ms`, P99 `11079 ms`, no errors.
- Practice P95 increase: approximately `164%` compared with baseline.
- Isolated official challenge run, 5 requests: P50 `3727 ms`, P95 `10270 ms`, P99 `10270 ms`, no errors.
- All latency measurements breached the challenge threshold of `2000 ms`. Cost, token, error, and quality signals did not indicate the primary failure mode.

## Trace evidence

- Selected trace ID: `5e42ed7ffa6893b8bcec4d247d9ee4c6`
- Session ID: `k4-challenge-s01`
- Correlation tag: `req-0ab75f70`
- Total trace latency: `3.765 s`
- Abnormal child span: `retrieve` (`SPAN`), latency `2.503 s`
- The retrieval span accounts for approximately `66.5%` of the trace duration.

Other successfully ingested challenge traces with the retrieval span:

| Session | Correlation ID | Trace ID | Trace latency | Retrieve latency |
|---|---|---|---:|---:|
| `k4-challenge-s02` | `req-027687bf` | `d3062008d2ea5c051db22f277465cb3e` | 3.728 s | 2.505 s |
| `k4-challenge-s03` | `req-a382abab` | `df41d58428f680c5c3784b7d6451e9c6` | 3.606 s | 2.505 s |
| `k4-challenge-s05` | `req-4f23223d` | `0b3c9232b3c011de356d12d8b84cacc4` | 3.548 s | 2.505 s |

## Log evidence

The selected trace correlation tag maps to `data/logs.jsonl`:

```json
{"event":"request_received","session_id":"k4-challenge-s01","correlation_id":"req-0ab75f70","feature":"monitoring"}
{"event":"response_sent","session_id":"k4-challenge-s01","correlation_id":"req-0ab75f70","feature":"monitoring","latency_ms":3764}
```

Final log validation:

```text
Basic JSON schema: PASSED
Correlation ID propagation: PASSED
Log enrichment: PASSED
PII scrubbing: PASSED
Estimated Score: 100/100
```

## Root cause and actions

- Root cause: when `rag_slow` is enabled, `app/mock_rag.py::retrieve` performs a blocking `time.sleep(2.5)` before retrieval. Metrics show tail-latency growth, the trace localizes most time to `retrieve`, and the correlated response log confirms the request duration.
- Immediate mitigation: disable `rag_slow` and verify `/health` reports all incidents as `false`.
- Fix action: remove the blocking delay in the retrieval path; for a real external retriever, configure a timeout, bounded retry, and circuit breaker, with a safe fallback.
- Preventive measure: retain the retrieval child span and correlation tag, alert on sustained P95 latency above 3000 ms, and run the baseline/practice comparison in regression testing.

## Known external dependency finding

The configured Langfuse project returned `Prompt not found` for `day13-chat` with label `production`, so these traces used `prompt_source=local-fallback`. This does not change the incident root cause, but the prompt owner must create/label the managed prompt before final CP2 evidence is captured.
