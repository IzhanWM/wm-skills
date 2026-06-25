#!/usr/bin/env python3
"""
wmtrace — pull full WaveMaker AI agent trace output for debugging.

Design rule (important): trace/session responses are HUGE (a single session can
be ~1MB / 14k lines, a single trace 150+ observations). This tool NEVER prints
the full payload. It fetches once, caches the raw JSON to disk, and every command
emits only a small slice (a table, an index, or a head preview). When you want the
full text of one observation, `dump` writes it to a file and prints the path — read
that file with offset/limit, never paste the whole blob into context.

Stdlib only (urllib/argparse/json) — no install, runs anywhere with python3.

Auth is dynamic (JWT expires hourly). Token resolution order:
  1. --token / -k flag
  2. $WM_TRACE_TOKEN
  3. token file (default ~/.wmtrace/token), set via `wmtrace auth <token>`

Endpoints (base: $WM_TRACE_BASE_URL, default non-prod-ai-analytics.wavemakeronline.com):
  GET /api/v2/session/analyse?session_id=<id>   -> {session, traces[], summary, ...}
  GET /api/v2/trace/<trace_id>/analyse           -> single {trace, observations[], ...}
"""

import argparse
import ast
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = os.environ.get(
    "WM_TRACE_BASE_URL", "https://non-prod-ai-analytics.wavemakeronline.com"
)
HOME_DIR = os.environ.get("WM_TRACE_DIR", os.path.expanduser("~/.wmtrace"))
TOKEN_FILE = os.path.join(HOME_DIR, "token")
CACHE_DIR = os.path.join(HOME_DIR, "cache")

# Big fields on an observation worth dumping for debugging.
FULL_FIELDS = ["input_full", "output_full", "output_preview", "input_preview"]


# ----------------------------------------------------------------------------- color / output
def c(text, color):
    if not sys.stdout.isatty():
        return text
    codes = {"dim": "2", "red": "31", "grn": "32", "yel": "33", "cyn": "36", "bold": "1"}
    return f"\033[{codes.get(color, '0')}m{text}\033[0m"


def die(msg, code=1):
    print(c(f"error: {msg}", "red"), file=sys.stderr)
    sys.exit(code)


def info(msg):
    print(c(msg, "dim"), file=sys.stderr)


# ----------------------------------------------------------------------------- token handling
def decode_jwt(token):
    """Best-effort decode of the JWT payload. Returns dict or None."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return None


def token_status(token):
    """Return (ok, message). ok=False if clearly expired."""
    p = decode_jwt(token)
    if not p:
        return True, "token is not a decodable JWT (using as-is)"
    exp = p.get("exp")
    email = p.get("email", "?")
    if not exp:
        return True, f"token for {email} (no exp claim)"
    left = float(exp) - time.time()
    when = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(exp)))
    if left <= 0:
        return False, f"token for {email} EXPIRED at {when} ({int(-left/60)} min ago)"
    return True, f"token for {email} valid until {when} ({int(left/60)} min left)"


def resolve_token(args):
    if getattr(args, "token", None):
        return args.token
    if os.environ.get("WM_TRACE_TOKEN"):
        return os.environ["WM_TRACE_TOKEN"].strip()
    if os.path.exists(TOKEN_FILE):
        return open(TOKEN_FILE).read().strip()
    return None


AUTH_HELP = """
No / expired auth token. Grab a fresh one (it's a short-lived JWT):

  1. Open {base} in your browser (logged in).
  2. DevTools -> Network -> click any /api/v2/... request.
  3. Copy the FULL value of the 'Authorization: Bearer ...' request header
     (just the token after 'Bearer ', or the whole header — both work).
  4. Save it for reuse:
        wmtrace auth '<token>'
     or for one shot:
        export WM_TRACE_TOKEN='<token>'     # or pass --token '<token>'
""".strip()


def require_token(args):
    tok = resolve_token(args)
    if not tok:
        die(AUTH_HELP.format(base=args.base))
    # Strip a leading "Bearer " if the user pasted the whole header.
    tok = re.sub(r"^\s*Bearer\s+", "", tok, flags=re.I).strip()
    ok, msg = token_status(tok)
    info(msg)
    if not ok and not getattr(args, "force", False):
        die("refusing to call with an expired token (pass --force to try anyway).\n\n"
            + AUTH_HELP.format(base=args.base))
    return tok


# ----------------------------------------------------------------------------- http + cache
def http_get_json(url, token, base):
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    req.add_header("Cache-Control", "no-cache")
    # No Accept-Encoding -> server returns plain JSON (no gzip to decompress).
    req.add_header("User-Agent", "wmtrace/1.0 (+claude-code)")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            pass
        if e.code in (401, 403):
            die(f"HTTP {e.code} unauthorized.\n\n" + AUTH_HELP.format(base=base))
        die(f"HTTP {e.code} from {url}\n{body}")
    except urllib.error.URLError as e:
        die(f"network error reaching {url}: {e.reason}")


def cache_path(kind, ident):
    os.makedirs(CACHE_DIR, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", ident)
    return os.path.join(CACHE_DIR, f"{kind}_{safe}.json")


def save_cache(path, data):
    with open(path, "w") as f:
        json.dump(data, f)
    info(f"cached raw -> {path}")


def load_local_file(path):
    if not os.path.exists(path):
        die(f"file not found: {path}")
    with open(path) as f:
        return json.load(f)


def millis():
    return int(time.time() * 1000)


def fetch_session(session_id, args):
    if args.file:
        return load_local_file(args.file)
    token = require_token(args)
    q = urllib.parse.quote(session_id, safe="")
    url = f"{args.base}/api/v2/session/analyse?_t={millis()}&session_id={q}"
    info(f"GET {url}")
    data = http_get_json(url, token, args.base)
    save_cache(cache_path("session", session_id), data)
    return data


def fetch_trace(trace_id, args):
    if args.file:
        return load_local_file(args.file)
    token = require_token(args)
    url = f"{args.base}/api/v2/trace/{trace_id}/analyse?_t={millis()}"
    info(f"GET {url}")
    data = http_get_json(url, token, args.base)
    save_cache(cache_path("trace", trace_id), data)
    return data


# ----------------------------------------------------------------------------- locating a trace
def iter_session_files():
    if not os.path.isdir(CACHE_DIR):
        return
    for fn in os.listdir(CACHE_DIR):
        if fn.startswith("session_") and fn.endswith(".json"):
            yield os.path.join(CACHE_DIR, fn)


def trace_from_session_obj(obj, trace_id):
    """A session response embeds full traces. Pull one out, or None."""
    for tr in obj.get("traces", []):
        if (tr.get("trace") or {}).get("id") == trace_id:
            return tr
    return None


def resolve_trace(trace_id, args):
    """Return a single-trace object {trace, observations, timeline, ...}.

    Resolution order (avoid re-fetching big payloads):
      1. --file (trace or session response)
      2. cached trace_<id>.json
      3. any cached session_*.json that embeds this trace
      4. live trace endpoint
    """
    if args.file:
        obj = load_local_file(args.file)
        if "observations" in obj and "traces" not in obj:
            return obj
        hit = trace_from_session_obj(obj, trace_id)
        if hit:
            return hit
        die(f"trace {trace_id} not found in {args.file}")

    tp = cache_path("trace", trace_id)
    if os.path.exists(tp):
        info(f"using cached {tp}")
        return load_local_file(tp)

    for sf in iter_session_files():
        try:
            obj = json.load(open(sf))
        except Exception:
            continue
        hit = trace_from_session_obj(obj, trace_id)
        if hit:
            info(f"found trace in cached {sf}")
            return hit

    return fetch_trace(trace_id, args)


# ----------------------------------------------------------------------------- humanize
def humanize(value, depth=0):
    """Render a value with REAL newlines so prompts/messages are readable.
    JSON-encoded strings are parsed and recursed into."""
    if isinstance(value, str):
        s = value.strip()
        if s[:1] in "{[":
            # Fields arrive as either JSON or Python-repr (single-quoted dicts).
            for parse in (json.loads, ast.literal_eval):
                try:
                    return humanize(parse(s), depth)
                except Exception:
                    pass
        return value
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            out.append(c(f"===== {k} =====", "cyn") if depth == 0 else f"--- {k} ---")
            out.append(humanize(v, depth + 1))
            out.append("")
        return "\n".join(out)
    if isinstance(value, list):
        out = []
        for i, v in enumerate(value):
            out.append(f"----- [{i}] -----")
            out.append(humanize(v, depth + 1))
        return "\n".join(out)
    return json.dumps(value, ensure_ascii=False)


def trunc(s, n):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


# ----------------------------------------------------------------------------- observation helpers
def obs_is_error(o):
    return (o.get("level") or "").upper() == "ERROR" or bool(o.get("status_message"))


def select_obs(observations, sel):
    """sel: 'all', an int index, or an observation id (hex). Returns list of (idx, obs)."""
    if sel is None or sel == "all":
        return list(enumerate(observations))
    if re.fullmatch(r"\d+", sel):
        i = int(sel)
        if not (0 <= i < len(observations)):
            die(f"obs index {i} out of range (0..{len(observations)-1})")
        return [(i, observations[i])]
    for i, o in enumerate(observations):
        if o.get("id") == sel or (o.get("id") or "").startswith(sel):
            return [(i, o)]
    die(f"no observation matching '{sel}'")


# ----------------------------------------------------------------------------- commands
def cmd_auth(args):
    tok = re.sub(r"^\s*Bearer\s+", "", args.value, flags=re.I).strip()
    os.makedirs(HOME_DIR, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(tok)
    os.chmod(TOKEN_FILE, 0o600)
    ok, msg = token_status(tok)
    print(c(f"saved token -> {TOKEN_FILE}", "grn"))
    print(msg)


def cmd_whoami(args):
    tok = resolve_token(args)
    if not tok:
        die("no token configured.\n\n" + AUTH_HELP.format(base=args.base))
    tok = re.sub(r"^\s*Bearer\s+", "", tok, flags=re.I).strip()
    p = decode_jwt(tok) or {}
    _, msg = token_status(tok)
    print(json.dumps({"email": p.get("email"), "name": p.get("name")}, indent=2))
    print(msg)


def cmd_session(args):
    data = fetch_session(args.session_id, args)
    s = data.get("session", {})
    traces = data.get("traces", [])
    summ = data.get("summary", {})
    print(c(f"\nsession {s.get('id', args.session_id)}", "bold"))
    print(f"  user={s.get('user')}  env={s.get('env')}  team={s.get('team')}  traces={s.get('trace_count', len(traces))}")
    tr = s.get("time_range") or {}
    if tr:
        print(f"  time={tr.get('from')} .. {tr.get('to')}")
    if s.get("url"):
        print(c(f"  logs: {s['url']}", "dim"))

    print(c(f"\n{'#':>2}  {'trace_id':32}  {'name':16}  {'obs':>4}  {'gen':>3}  {'tool':>4}  {'err':>3}  {'tokens':>8}  {'cost':>8}  first input", "bold"))
    for i, tr in enumerate(traces):
        meta = tr.get("trace", {})
        obs = tr.get("observations", [])
        gens = sum(1 for o in obs if o.get("observation_type") == "GENERATION")
        tools = sum(len(o.get("tool_calls") or []) for o in obs)
        errs = sum(1 for o in obs if obs_is_error(o))
        tsum = tr.get("summary", {}).get("total_tokens", {})
        tok = tsum.get("formatted") if isinstance(tsum, dict) else tsum
        cost = tr.get("summary", {}).get("total_cost", {})
        cost = cost.get("formatted") if isinstance(cost, dict) else cost
        first_in = obs[0].get("input_preview") if obs else ""
        row = f"{i:>2}  {meta.get('id',''):32}  {trunc(meta.get('name',''),16):16}  {len(obs):>4}  {gens:>3}  {tools:>4}  {errs:>3}  {str(tok or ''):>8}  {str(cost or ''):>8}  {trunc(first_in, 40)}"
        print(c(row, "red") if errs else row)
    print(c(f"\nnext: wmtrace trace <trace_id>   (or: wmtrace dump <trace_id> --obs all)", "dim"))


def cmd_trace(args):
    tr = resolve_trace(args.trace_id, args)
    meta = tr.get("trace", {})
    obs = tr.get("observations", [])
    summ = tr.get("summary", {})
    print(c(f"\ntrace {meta.get('id', args.trace_id)}  ({meta.get('name','?')})", "bold"))
    print(f"  session={meta.get('session_id')}")
    print(f"  obs={len(obs)}  gens={summ.get('total_generations')}  tools={summ.get('total_tool_calls')}"
          f"  tokens={(summ.get('total_tokens') or {}).get('formatted')}  cost={(summ.get('total_cost') or {}).get('formatted')}"
          f"  latency={(summ.get('total_latency') or {}).get('formatted')}")
    if meta.get("url"):
        print(c(f"  logs: {meta['url']}", "dim"))

    print(c(f"\n{'#':>3}  {'type':10}  {'name':26}  {'model':18}  {'tok':>6}  {'err':>3}  {'id':16}  input → output", "bold"))
    limit = args.limit
    for i, o in enumerate(obs):
        if limit and i >= limit:
            print(c(f"  … {len(obs)-limit} more (use --limit 0 for all, or grep/dump)", "dim"))
            break
        io = f"{trunc(o.get('input_preview'), 28)}  →  {trunc(o.get('output_preview'), 40)}"
        row = (f"{i:>3}  {trunc(o.get('observation_type'),10):10}  {trunc(o.get('name'),26):26}  "
               f"{trunc(o.get('model'),18):18}  {str(o.get('tokens') or 0):>6}  "
               f"{'ERR' if obs_is_error(o) else '':>3}  {trunc(o.get('id'),16):16}  {io}")
        print(c(row, "red") if obs_is_error(o) else row)
    print(c(f"\nnext: wmtrace dump {args.trace_id} --obs <#|id> --field output_full", "dim"))


def cmd_dump(args):
    tr = resolve_trace(args.trace_id, args)
    obs = tr.get("observations", [])
    if not obs:
        die("no observations in this trace")
    picked = select_obs(obs, args.obs)

    out_dir = args.out or os.path.join(CACHE_DIR, f"dump_{re.sub(r'[^A-Za-z0-9]', '_', args.trace_id)[:24]}")
    os.makedirs(out_dir, exist_ok=True)

    fields = FULL_FIELDS if args.field == "all" else [args.field]
    written = []
    for idx, o in picked:
        name = re.sub(r"[^A-Za-z0-9]+", "-", o.get("name", "obs")).strip("-")[:30]
        for fld in fields:
            if fld not in o or o.get(fld) in (None, ""):
                continue
            val = o[fld]
            text = val if args.raw else humanize(val)
            # strip ANSI from file output
            text = re.sub(r"\033\[[0-9;]*m", "", text)
            fname = f"{idx:03d}_{name}_{fld}.txt"
            fpath = os.path.join(out_dir, fname)
            header = (f"# trace {args.trace_id}\n# obs[{idx}] id={o.get('id')} "
                      f"type={o.get('observation_type')} name={o.get('name')} model={o.get('model')}\n"
                      f"# field={fld}\n{'='*70}\n")
            with open(fpath, "w") as f:
                f.write(header + text + "\n")
            written.append((idx, o, fld, fpath, os.path.getsize(fpath)))

    if not written:
        die(f"nothing to write (field '{args.field}' empty on selected observations)")

    print(c(f"\nwrote {len(written)} file(s) -> {out_dir}", "grn"))
    print(c(f"{'#':>3}  {'field':14}  {'bytes':>8}  file", "bold"))
    for idx, o, fld, fpath, size in written:
        print(f"{idx:>3}  {fld:14}  {size:>8}  {fpath}")

    # Single-target dump: show a bounded head preview inline. Bulk dump: index only.
    if len(written) <= 2:
        for idx, o, fld, fpath, size in written:
            print(c(f"\n----- head of {os.path.basename(fpath)} (first {args.head} lines) -----", "cyn"))
            with open(fpath) as f:
                for n, line in enumerate(f):
                    if n >= args.head:
                        print(c(f"… (read full file: {fpath})", "dim"))
                        break
                    print(line.rstrip("\n"))
    else:
        print(c(f"\nRead any file above with offset/limit — do NOT cat the whole dir into context.", "dim"))


def cmd_grep(args):
    tr = resolve_trace(args.trace_id, args)
    obs = tr.get("observations", [])
    rx = re.compile(args.pattern, 0 if args.case else re.I)
    fields = FULL_FIELDS if args.field == "all" else [args.field]
    hits = 0
    print(c(f"\ngrep /{args.pattern}/ across {len(obs)} observations", "bold"))
    for i, o in enumerate(obs):
        for fld in fields:
            text = o.get(fld)
            if not isinstance(text, str):
                continue
            for m in rx.finditer(text):
                hits += 1
                s = max(0, m.start() - args.context)
                e = min(len(text), m.end() + args.context)
                snippet = trunc(text[s:e], 200)
                loc = c(f"obs[{i}] {o.get('name')} ({fld})", "cyn")
                print(f"  {loc}: …{snippet}…")
                break  # one snippet per field per obs is enough to locate it
    print(c(f"\n{hits} match(es). Pull full context: wmtrace dump {args.trace_id} --obs <#> --field <field>", "dim"))


# ----------------------------------------------------------------------------- argparse
def build_parser():
    # Common flags live on a parent parser with SUPPRESS defaults so they work
    # BEFORE or AFTER the subcommand without one position clobbering the other.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--base", default=argparse.SUPPRESS,
                        help=f"API base (default {DEFAULT_BASE} / $WM_TRACE_BASE_URL)")
    common.add_argument("--token", "-k", default=argparse.SUPPRESS,
                        help="Bearer token (else $WM_TRACE_TOKEN, else saved token file)")
    common.add_argument("--file", "-f", default=argparse.SUPPRESS,
                        help="Read JSON from a local session/trace file instead of the network")
    common.add_argument("--force", action="store_true", default=argparse.SUPPRESS,
                        help="Proceed even if the token looks expired")

    p = argparse.ArgumentParser(prog="wmtrace", parents=[common],
                                description="Pull WaveMaker AI trace output for debugging.")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("auth", parents=[common], help="Save a Bearer token for reuse")
    a.add_argument("value")
    a.set_defaults(func=cmd_auth)

    w = sub.add_parser("whoami", parents=[common], help="Show current token identity + expiry")
    w.set_defaults(func=cmd_whoami)

    s = sub.add_parser("session", parents=[common], aliases=["list"], help="List traces in a session")
    s.add_argument("session_id")
    s.set_defaults(func=cmd_session)

    t = sub.add_parser("trace", parents=[common], aliases=["obs"], help="List observations in a trace")
    t.add_argument("trace_id")
    t.add_argument("--limit", type=int, default=60, help="Max rows (0 = all, default 60)")
    t.set_defaults(func=cmd_trace)

    d = sub.add_parser("dump", parents=[common], help="Write full observation field(s) to file(s)")
    d.add_argument("trace_id")
    d.add_argument("--obs", default="all", help="'all', an index (#), or an observation id")
    d.add_argument("--field", default="output_full",
                   choices=["output_full", "input_full", "output_preview", "input_preview", "all"])
    d.add_argument("--out", help="Output dir (default under the cache dir)")
    d.add_argument("--raw", action="store_true", help="Write raw JSON string instead of humanized text")
    d.add_argument("--head", type=int, default=60, help="Preview lines for single-obs dump (default 60)")
    d.set_defaults(func=cmd_dump)

    g = sub.add_parser("grep", parents=[common], help="Search observation full-text in a trace")
    g.add_argument("trace_id")
    g.add_argument("pattern")
    g.add_argument("--field", default="all",
                   choices=["output_full", "input_full", "output_preview", "input_preview", "all"])
    g.add_argument("--context", type=int, default=80, help="Chars of context around each match")
    g.add_argument("--case", action="store_true", help="Case-sensitive")
    g.set_defaults(func=cmd_grep)
    return p


def main():
    args = build_parser().parse_args()
    # Apply defaults for SUPPRESS-ed common flags (unset in either position).
    args.base = getattr(args, "base", None) or DEFAULT_BASE
    args.token = getattr(args, "token", None)
    args.file = getattr(args, "file", None)
    args.force = getattr(args, "force", False)
    args.func(args)


if __name__ == "__main__":
    main()
