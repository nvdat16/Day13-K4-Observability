# CP2 Prompt Versioning Evidence

Verified from the configured Langfuse project on 2026-08-11. No API key or prompt content is included.

## Managed prompt state

| Prompt | Version | Labels |
|---|---:|---|
| `day13-chat` | 1 | `production`, `baseline` |
| `day13-chat` | 2 | `candidate`, `latest` |

The current `production` label points to version 1 after version 2 was retained as the candidate. This is the submitted rollback evidence.

## Same-input traces

Input used for both versions: `Explain the Metrics to Traces to Logs investigation workflow.`

| Version/label | Session | Trace ID | Correlation ID | Source |
|---|---|---|---|---|
| v1 / `production` | `c-prompt-v1` | `291b603806d3da44581dc132d262fd16` | `req-0494f055` | `langfuse` |
| v2 / `candidate` | `c-prompt-v2` | `401ce1db601b1bd69f166a75f425aec8` | `req-bf3109af` | `langfuse` |

Both trace records were read back through the Langfuse API and reported the expected `prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`, and correlation ID metadata.
