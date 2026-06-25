# WaveMaker AI Analytics API — shape reference

Base: `https://non-prod-ai-analytics.wavemakeronline.com` (override `WM_TRACE_BASE_URL`).
Auth: `Authorization: Bearer <JWT>` (short-lived; payload has `email`, `iat`, `exp`).
A `_t=<epoch_ms>` cache-buster query param is added on every request.

## Endpoints

| Endpoint | Returns |
|---|---|
| `GET /api/v2/session/analyse?session_id=<id>` | `{ session, traces[], summary, flow, comment_counts, version }` — **embeds full traces** |
| `GET /api/v2/trace/<trace_id>/analyse` | one trace: `{ trace, observations[], timeline[], summary, flow, iterations, ... }` |

`session_id` contains a `/` and MUST be URL-encoded (`%2F`). Because the session
response embeds every trace in full, you usually don't need the trace endpoint
once a session is cached — `wmtrace` pulls the trace out of the cached session.

## `session` object
`id`, `user`, `user_id`, `env`, `team`, `trace_count`, `time_range{from,to}`, `url`.

## A trace (in `traces[]`, or the top level of the trace endpoint)
- `trace`: `{ id, name, session_id, env, team, user, user_id, timestamp, tags[], url, graph_url, media[] }`
- `observations[]`: the timeline of steps (see below)
- `timeline[]`: same steps with `depth`, `parent_observation_id`, `duration_ms`, `is_error`, `rolled_up_cost`
- `summary`: `agent_count`, `models[]`, `total_tokens{raw,formatted}`, `total_cost{...}`,
  `total_latency{...}`, `total_generations`, `total_tool_calls`, `time_breakdown{...}`
- `flow`: `{ nodes[], edges[], mermaid }` (often empty)

## Observation fields
`id`, `name`, `observation_type` (`AGENT` | `GENERATION` | `TOOL`), `invocation_type`,
`agent`, `agent_id`, `model`, `level` (`DEFAULT`/`ERROR`), `status_message`,
`start_time`, `end_time`, `tokens`, `prompt_tokens`, `completion_tokens`,
`cache_read_tokens`, `ctx_delta`, `cost`, `cost_fmt`, `tool_calls[]`,
`mermaid_node_id`, `media[]`, and the big text fields:

| field | content |
|---|---|
| `input_full` / `input_preview` | step input — for `GENERATION` the user/human content; for `AGENT` middleware steps a JSON state blob; for `TOOL` the call args (often Python-repr) |
| `output_full` / `output_preview` | step output — model text, tool result JSON, or `{"resolved_system_prompt": "..."}` for system-prompt middleware |

`*_full` is the field to dump for debugging. Note: very long `resolved_system_prompt`
values are truncated server-side (trailing `....`) even in `output_full`.

Error observations: `level == "ERROR"` or non-empty `status_message` (and
`timeline[].is_error`). `wmtrace` flags these in red and counts them per trace.
