"""File-based request/response queue between the web server and the agent.

The agent is a separate Claude Code session (see .claude/skills/roteboat/
SKILL.md) watching these directories -- no direct API calls from this app.

Layout (dirs created on demand, root set by config agent.queue_dir):
    queue/requests/<id>.json    written by the server when "process" clicked
    queue/responses/<id>.json   written by the agent when done
    queue/status/<id>.txt       agent's short "what I'm doing" note, freely
                                overwritten while it works; shown by the
                                spinner so the user can tell scan vs. stall

Request json:  {"id", "dossier_id", "scope", "prompt", "snippet", "context"}
-- scope "snippet" carries the full snippet dict; scope "session" (the top
box) carries snippet null. context is the agent's memory: the dossier's
conversation thread, its items, tasks, view, and (snippet scope) that
item's own thread -- see dossier.rule_request_context.
Response json: {"id", "kind", "response": "<plain text>", "found": [...]}
where found (session scope only) lists item refs the agent picked as the
dossier's items. The agent may also send "view" and "tasks" (session
scope); those go straight into the dossier, not the response file.

The <id> is timestamped and unique per server run; a response file is only
ever read after it exists in full (the agent writes via a temp-file rename,
per SKILL.md, so a half-written json is never visible)."""
import json
import os
import time
from pathlib import Path

from config import CONFIG

_counter = 0


def _queue_root():
    # Repo root / config'd dir (this file is src/agent_queue.py).
    root = Path(__file__).resolve().parent.parent / CONFIG["agent"]["queue_dir"]
    return root


def requests_dir():
    d = _queue_root() / "requests"
    d.mkdir(parents=True, exist_ok=True)
    return d


def responses_dir():
    d = _queue_root() / "responses"
    d.mkdir(parents=True, exist_ok=True)
    return d


def done_dir():
    d = requests_dir() / "done"
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_pending_requests():
    """All pending request payloads, oldest first (ids sort by time)."""
    pending = []
    for path in sorted(requests_dir().glob("*.json")):
        with open(path, "r") as f:
            pending.append(json.load(f))
    return pending


def write_status(request_id, text):
    """Server-side status write (the agent posts this via /agent/status)."""
    path = status_dir() / (request_id + ".txt")
    path.write_text(text)


def complete_request(request_id, kind, response_text, found):
    """The full completion transaction, in python instead of agent bash:
    write the response atomically (tmp + rename), archive the request to
    done/, clear the status file. Returns (error, request_payload): error
    is a string or None; request_payload is the original request dict (so
    the caller knows its dossier/scope/snippet) or None on error."""
    result = (None, None)
    request_path = requests_dir() / (request_id + ".json")
    if not request_path.is_file():
        result = ("no pending request with id " + request_id, None)
    else:
        with open(request_path, "r") as f:
            request_payload = json.load(f)
        result = (None, request_payload)
        payload = {"id": request_id, "kind": kind, "response": response_text,
                   "found": found}
        tmp_path = responses_dir() / (request_id + ".json.tmp")
        with open(tmp_path, "w") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_path, responses_dir() / (request_id + ".json"))
        os.replace(request_path, done_dir() / request_path.name)
        status_path = status_dir() / (request_id + ".txt")
        if status_path.is_file():
            status_path.unlink()
    return result


def status_dir():
    d = _queue_root() / "status"
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_status(request_id):
    """The agent's short in-progress note for one request, truncated to
    agent.status_chars; None if the agent hasn't written one (yet)."""
    result = None
    path = status_dir() / (request_id + ".txt")
    if path.is_file():
        text = path.read_text(errors="replace").strip()
        max_chars = CONFIG["agent"]["status_chars"]
        result = text[:max_chars]
    return result


def rule_request_id():
    """Request id format: local timestamp + per-run counter. Readable when
    listing the queue dir by name, and sortable in submission order."""
    global _counter
    _counter = _counter + 1
    stamp = time.strftime("%Y-%m-%dT%H-%M-%S")
    return stamp + "_" + str(_counter).zfill(3)


def write_request(dossier_id, snippet, prompt, context):
    """Drop a request file for the agent; returns the new request id."""
    request_id = rule_request_id()
    scope = "snippet"
    if snippet is None:
        scope = "session"
    payload = {"id": request_id, "dossier_id": dossier_id, "scope": scope,
               "prompt": prompt, "snippet": snippet, "context": context}
    path = requests_dir() / (request_id + ".json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return request_id


def read_response(request_id):
    """The agent's full response payload dict, or None while still pending.
    Payload carries "response" text and an optional "kind": "answer"
    (default) | "error" | "needs_human"."""
    result = None
    path = responses_dir() / (request_id + ".json")
    if path.is_file():
        with open(path, "r") as f:
            result = json.load(f)
    return result


def read_activity_age(request_id):
    """Seconds since the agent last touched this request: the status file's
    mtime, falling back to the request file's own write time. None if
    neither file exists (unknown id, or archived mid-flight)."""
    result = None
    status_path = status_dir() / (request_id + ".txt")
    request_path = requests_dir() / (request_id + ".json")
    stamp = None
    if status_path.is_file():
        stamp = status_path.stat().st_mtime
    elif request_path.is_file():
        stamp = request_path.stat().st_mtime
    if stamp is not None:
        result = time.time() - stamp
    return result
