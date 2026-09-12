"""MyRoteBoat entry point -- the local Flask server behind the dossier UI.

Run:  python src/main.py
Then open http://127.0.0.1:8474/

Routes are registered via app.add_url_rule (no decorators, per TECH.md)."""
from flask import Flask, jsonify, render_template, request

import agent_queue
import session_log
from config import CONFIG, stash_dir
from snippets import gather_snippets, load_snippet


# --- rules (swappable behavior lives up here, per agents.md) -----------------

def rule_stash_status():
    """How the landing page summarizes the data stash. Current rule: report
    whether the configured stash_dir exists and how many top-level entries it
    holds. Future rules could report per-subtree counts, freshness, etc."""
    root = stash_dir()
    status = {"path": str(root), "exists": root.is_dir(), "entry_count": 0}
    if status["exists"]:
        count = 0
        for _entry in root.iterdir():
            count = count + 1
        status["entry_count"] = count
    return status


# --- route handlers ----------------------------------------------------------

def handle_index():
    snippets = gather_snippets()
    session_log.emit("10001", "index page rendered",
                     "snippets=" + str(len(snippets)))
    page = render_template(
        "index.html",
        title=CONFIG["ui"]["title"],
        stash=rule_stash_status(),
        snippets=snippets,
        poll_ms=CONFIG["agent"]["poll_ms"],
    )
    return page


def handle_process():
    """Browser clicked "process": queue the request for the agent."""
    body = request.get_json()
    disk_path = body["disk_path"]
    prompt = body["prompt"]
    session_log.emit("20001", "process clicked",
                     "path=" + disk_path + " prompt_chars=" + str(len(prompt)))
    snippet = load_snippet(_resolve_stash_path(disk_path))
    request_id = agent_queue.write_request(snippet, prompt)
    session_log.emit("20002", "request file written", "id=" + request_id)
    return jsonify({"request_id": request_id})


def handle_poll(request_id):
    """Browser polling for the agent's answer to one request."""
    response_text = agent_queue.read_response(request_id)
    result = {"done": False}
    if response_text is not None:
        result = {"done": True, "response": response_text}
        session_log.emit("20003", "response delivered",
                         "id=" + request_id
                         + " chars=" + str(len(response_text)))
    return jsonify(result)


def handle_snippet():
    """Re-read one snippet from disk (left-column refresh after a response)."""
    disk_path = request.args["path"]
    snippet = load_snippet(_resolve_stash_path(disk_path))
    session_log.emit("10002", "snippet refreshed", "path=" + disk_path)
    return jsonify(snippet)


def _resolve_stash_path(disk_path):
    """A browser-supplied relative path, pinned inside the stash root."""
    full = (stash_dir() / disk_path).resolve()
    if not str(full).startswith(str(stash_dir().resolve())):
        raise ValueError("path escapes stash: " + disk_path)
    return full


# --- app setup ---------------------------------------------------------------

def create_app():
    app = Flask(__name__)
    app.add_url_rule("/", "index", handle_index)
    app.add_url_rule("/process", "process", handle_process, methods=["POST"])
    app.add_url_rule("/poll/<request_id>", "poll", handle_poll)
    app.add_url_rule("/snippet", "snippet", handle_snippet)
    return app


# MAIN
if __name__ == "__main__":
    # Flask's debug reloader runs this file twice (watcher parent + serving
    # child); only the child sets WERKZEUG_RUN_MAIN... except on the very
    # first launch, where the parent imports us before spawning. Opening the
    # session lazily on first request would fix that but complicate emit();
    # instead: open in the child when reloading, or straight away when the
    # reloader is off. The one stray empty log on a debug first-launch parent
    # is avoided because the parent never serves a request -- open_session
    # only when this process will serve.
    import os
    if CONFIG["server"]["debug"] is False or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        session_log.open_session()
    roteboat_app = create_app()
    roteboat_app.run(
        host=CONFIG["server"]["host"],
        port=CONFIG["server"]["port"],
        debug=CONFIG["server"]["debug"],
    )
