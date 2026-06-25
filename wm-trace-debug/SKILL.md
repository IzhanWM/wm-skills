---
name: wm-trace-debug
description: >-
  Pull and inspect full WaveMaker AI agent trace/observation output for
  debugging, given a session_id or trace_id. Use when debugging a WM agent run,
  analyzing a trace, inspecting an agent's resolved system prompt / model
  input-output / tool calls, or when given a non-prod-ai-analytics session or
  trace URL. Fetches from the trace API (auth is a dynamic, short-lived Bearer
  token), caches raw JSON to disk, and extracts only targeted slices — it NEVER
  loads the giant (~1MB / 14k-line) payload into context.
---

# WaveMaker Trace Debugging

Debug WaveMaker AI agent runs by pulling trace data from the analytics API and
extracting only the slice you need.

## The one rule

**Never read a whole trace/session payload into context.** A single session is
~1 MB / 14k lines; one trace can hold 150+ observations. Always go through
`scripts/wmtrace.py`, which fetches once, caches the raw JSON to disk, and prints
only a small table, index, or head preview. When you need the full text of an
observation, `dump` writes it to a file and prints the path — then `Read` that
file with `offset`/`limit`. Do not `cat` cached JSON or dumped dirs into context.

## Setup (auth is dynamic)

The API auth is a short-lived JWT (≈24h). Resolution order: `--token` →
`$WM_TRACE_TOKEN` → saved token file (`~/.wmtrace/token`).

To get/refresh a token: open the analytics site logged in → DevTools → Network →
any `/api/v2/...` request → copy the `Authorization: Bearer …` header value, then:

```bash
python3 scripts/wmtrace.py auth '<token>'      # save it (works with or without the "Bearer " prefix)
python3 scripts/wmtrace.py whoami              # check who/expiry
```

The script warns before any call if the token is expired and refuses to send it
(use `--force` to try anyway). On `401/403` it prints exactly how to refresh.

## Workflow

Start from whatever the user gives you (a session id, a trace id, or an
analytics URL — the `session_id=` / `trace/<id>` part is what you need).

```bash
cd <this skill>/scripts

# 1. Session → list its traces (obs/gen/tool/ERROR counts + first input per trace)
python3 wmtrace.py session 'WMPRJ.../<rest>'

# 2. Trace → list its observations (type, name, model, tokens, ERROR, id, in→out)
python3 wmtrace.py trace <trace_id>            # add --limit 0 for all rows

# 3. Find where something happens without dumping everything
python3 wmtrace.py grep <trace_id> 'error|exception|tool_name'

# 4. Pull FULL output of an observation to a file, then Read that file
python3 wmtrace.py dump <trace_id> --obs 4 --field output_full   # one obs, with head preview
python3 wmtrace.py dump <trace_id> --obs all --field all         # writes per-obs files, prints index only
```

`--field`: `output_full` (default), `input_full`, `output_preview`, `input_preview`, `all`.
`--obs`: `all` (default), an index (`4`), or an observation id. Dumped files land
under `~/.wmtrace/cache/dump_<trace>/`; pretty-printed with real newlines so system
prompts and message lists are readable (`--raw` keeps the original JSON string).

## Notes

- **Offline / no auth:** pass `--file <path>` (a saved session or trace JSON, e.g.
  the sample) to any of `session`/`trace`/`dump`/`grep`. Same extraction, no network.
- **No re-fetch:** `dump`/`grep`/`trace` reuse a cached trace file, or pull the
  trace out of any cached session file, before hitting the network.
- **Server-side truncation:** the analytics API truncates very long
  `resolved_system_prompt` values (ends in `....`) even in `*_full` fields — that's
  the API, not this tool. Model input/output text and tool I/O come through whole.
- **Env overrides:** `WM_TRACE_BASE_URL` (default `https://non-prod-ai-analytics.wavemakeronline.com`),
  `WM_TRACE_DIR` (default `~/.wmtrace`, holds the token + cache).

See `references/api.md` for the exact endpoint shapes and observation fields.
