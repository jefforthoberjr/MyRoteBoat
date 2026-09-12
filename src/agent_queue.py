"""File-based request/response queue between the web server and the agent.

The agent is a separate Claude Code session (see .claude/skills/roteboat/
SKILL.md) watching these directories -- no direct API calls from this app.

Layout (dirs created on demand, root set by config agent.queue_dir):
    queue/requests/<id>.json    written by the server when "process" clicked
    queue/responses/<id>.json   written by the agent when done

Request json:  {"id", "prompt", "snippet": {<full snippet dict>}}
Response json: {"id", "response": "<plain text for the UI text box>"}

The <id> is timestamped and unique per server run; a response file is only
ever read after it exists in full (the agent writes via a temp-file rename,
per SKILL.md, so a half-written json is never visible)."""
import json
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


def rule_request_id():
    """Request id format: local timestamp + per-run counter. Readable when
    listing the queue dir by name, and sortable in submission order."""
    global _counter
    _counter = _counter + 1
    stamp = time.strftime("%Y-%m-%dT%H-%M-%S")
    return stamp + "_" + str(_counter).zfill(3)


def write_request(snippet, prompt):
    """Drop a request file for the agent; returns the new request id."""
    request_id = rule_request_id()
    payload = {"id": request_id, "prompt": prompt, "snippet": snippet}
    path = requests_dir() / (request_id + ".json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return request_id


def read_response(request_id):
    """The agent's answer text, or None while still pending."""
    result = None
    path = responses_dir() / (request_id + ".json")
    if path.is_file():
        with open(path, "r") as f:
            payload = json.load(f)
        result = payload["response"]
    return result
