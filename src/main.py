"""MyRoteBoat entry point -- the local Flask server behind the dossier UI.

Run:  python src/main.py
Then open http://127.0.0.1:8474/

Routes are registered via app.add_url_rule (no decorators, per TECH.md)."""
from flask import Flask, jsonify, redirect, render_template, request

import agent_queue
import diagram
import dossier as dossier_store
import session_log
from config import CONFIG, stash_dir
from snippets import gather_dossier_snippets, gather_snippets, load_item


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


def rule_page_snippets(dossier):
    """Where a dossier page's left column comes from, per config
    snippets.source: "dossier" = its saved items; "recent" = the v0
    recency stand-in (ignores the dossier)."""
    source = CONFIG["snippets"]["source"]
    if source == "recent":
        snippets = gather_snippets()
    else:
        snippets = gather_dossier_snippets(dossier)
    return snippets


def rule_stalled(request_id):
    """When a pending request counts as stalled (UI shows "see CLI" hint).
    Current rule: no agent activity (status/request file touch) for
    agent.stall_seconds, or no trace of the request at all."""
    age = agent_queue.read_activity_age(request_id)
    stalled = True
    if age is not None and age <= CONFIG["agent"]["stall_seconds"]:
        stalled = False
    return stalled


# --- route handlers ----------------------------------------------------------

def handle_landing():
    """UI: the first screen -- pick a saved dossier or start a new one.
    ---
    get:
      tags: [ui]
      summary: Render the landing page (dossier list + new-dossier form).
      responses:
        200:
          description: HTML page.
    """
    rows = dossier_store.list_dossiers()
    session_log.emit("10003", "landing page rendered",
                     "dossiers=" + str(len(rows)))
    page = render_template(
        "landing.html",
        title=CONFIG["ui"]["title"],
        stash=rule_stash_status(),
        dossiers=rows,
        initial_prompt=CONFIG["ui"]["initial_prompt"],
        heartbeat_ms=CONFIG["ui_heartbeat"]["interval_ms"],
    )
    return page


def handle_new_dossier():
    """Landing form submit: create a dossier from the typed prompt, then
    open it.
    ---
    post:
      tags: [ui]
      summary: Create a new dossier from a kickoff prompt; redirects to it.
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              properties:
                prompt: {type: string}
      responses:
        302:
          description: Redirect to /dossier/<id>.
    """
    prompt = request.form.get("prompt", "")
    dossier = dossier_store.create_dossier(prompt)
    session_log.emit("10004", "dossier created",
                     "id=" + dossier["id"]
                     + " prompt_chars=" + str(len(prompt)))
    return redirect("/dossier/" + dossier["id"])


def handle_dossier(dossier_id):
    """UI: the 2-column page for one dossier. Loading it also switches the
    session log to that dossier's own log file.
    ---
    get:
      tags: [ui]
      summary: Render the 2-column dossier page (HTML) for one saved dossier.
      parameters:
        - in: path
          name: dossier_id
          required: true
          schema: {type: string}
      responses:
        200:
          description: HTML page.
        404:
          description: No such dossier.
    """
    dossier = dossier_store.load_dossier(dossier_id)
    if dossier is None:
        page = ("no such dossier: " + dossier_id, 404)
    else:
        session_log.switch_to(dossier_store.dossier_log_path(dossier_id),
                              dossier_id)
        snippets = rule_page_snippets(dossier)
        session_log.emit("10005", "dossier loaded",
                         "id=" + dossier_id + " items="
                         + str(len(dossier["items"]))
                         + " snippets=" + str(len(snippets)))
        diagram_source = diagram.rule_diagram_source(snippets, dossier["view"])
        session_log.emit("10008", "diagram source built",
                         "nodes=" + str(len(snippets)) + " edges="
                         + str(len(diagram.rule_diagram_edges(snippets))))
        diagram_refs = []
        for snippet in snippets:
            diagram_refs.append(snippet["ref"])
        page = render_template(
            "index.html",
            title=CONFIG["ui"]["title"],
            stash=rule_stash_status(),
            dossier=dossier,
            snippets=snippets,
            diagram_source=diagram_source,
            diagram_refs=diagram_refs,
            legend_source=diagram.rule_legend_source(),
            tasks_source=diagram.rule_tasks_source(dossier["tasks"]),
            poll_ms=CONFIG["agent"]["poll_ms"],
            heartbeat_ms=CONFIG["ui_heartbeat"]["interval_ms"],
        )
    return page


def handle_process():
    """Browser clicked "process": queue the request for the agent. Two
    scopes: a snippet-scoped request carries its snippet; a session-scoped
    one (the top box, ref null) carries snippet=None and may affect the
    whole dossier.
    ---
    post:
      tags: [ui]
      summary: Queue a process request (snippet- or session-scoped).
      requestBody:
        content:
          application/json:
            schema:
              properties:
                dossier_id: {type: string}
                ref: {type: string, nullable: true, description: item ref (stash-relative path or mail:<acct>:<idx>), null for session scope}
                prompt: {type: string}
      responses:
        200:
          description: '{"request_id": "..."}'
    """
    body = request.get_json()
    dossier_id = body["dossier_id"]
    ref = body["ref"]
    prompt = body["prompt"]
    snippet = None
    log_path = "SESSION"
    if ref is not None:
        snippet = load_item(ref)
        log_path = ref
    else:
        # The top box's text is the dossier's prompt; keep edits.
        dossier = dossier_store.load_dossier(dossier_id)
        if dossier is not None:
            dossier["prompt"] = prompt
            dossier_store.save_dossier(dossier)
    session_log.emit("20001", "process clicked",
                     "dossier=" + dossier_id + " path=" + log_path
                     + " prompt_chars=" + str(len(prompt)))
    request_id = agent_queue.write_request(dossier_id, snippet, prompt)
    session_log.emit("20002", "request file written", "id=" + request_id)
    return jsonify({"request_id": request_id})


def handle_diagram(dossier_id):
    """Rebuild the item diagram text from the dossier as saved now (the
    "refresh diagram" button, and after an item removal).
    ---
    get:
      tags: [ui]
      summary: Current Mermaid source for a dossier's items (plus ref per node), its goals/tasks diagram, and the saved view.
      parameters:
        - in: path
          name: dossier_id
          required: true
          schema: {type: string}
      responses:
        200:
          description: '{"source": "<items mermaid>", "refs": [ref per node index], "tasks_source": "<tasks mermaid>", "task_count": N, "view": "explore|mapping"}'
        404:
          description: No such dossier.
    """
    dossier = dossier_store.load_dossier(dossier_id)
    if dossier is None:
        result = ("no such dossier: " + dossier_id, 404)
    else:
        snippets = rule_page_snippets(dossier)
        refs = []
        for snippet in snippets:
            refs.append(snippet["ref"])
        session_log.emit("10009", "diagram refreshed",
                         "dossier=" + dossier_id + " nodes=" + str(len(refs))
                         + " edges="
                         + str(len(diagram.rule_diagram_edges(snippets))))
        result = jsonify({"source": diagram.rule_diagram_source(snippets, dossier["view"]),
                          "refs": refs,
                          "tasks_source": diagram.rule_tasks_source(dossier["tasks"]),
                          "task_count": len(dossier["tasks"]),
                          "view": dossier["view"]})
    return result


def handle_set_view(dossier_id):
    """The explore/mapping buttons: save the user's view choice.
    ---
    post:
      tags: [ui]
      summary: Save the dossier's diagram view (explore | mapping).
      parameters:
        - in: path
          name: dossier_id
          required: true
          schema: {type: string}
      requestBody:
        content:
          application/json:
            schema:
              properties:
                view: {type: string, enum: [explore, mapping]}
      responses:
        200:
          description: '{"ok": true|false}'
    """
    view = request.get_json()["view"]
    ok = dossier_store.set_view(dossier_id, view)
    if ok:
        session_log.emit("10010", "view toggled",
                         "dossier=" + dossier_id + " view=" + view)
    return jsonify({"ok": ok})


def handle_remove_item(dossier_id):
    """Browser clicked an item's X: drop it (and its chat) from the dossier.
    ---
    post:
      tags: [ui]
      summary: Remove one item from a dossier by ref.
      parameters:
        - in: path
          name: dossier_id
          required: true
          schema: {type: string}
      requestBody:
        content:
          application/json:
            schema:
              properties:
                ref: {type: string}
      responses:
        200:
          description: '{"ok": true, "item_count": N} or {"ok": false}'
    """
    ref = request.get_json()["ref"]
    count = dossier_store.remove_item(dossier_id, ref)
    result = {"ok": False}
    if count is not None:
        result = {"ok": True, "item_count": count}
        session_log.emit("10006", "dossier item removed",
                         "dossier=" + dossier_id + " ref=" + ref
                         + " items=" + str(count))
    return jsonify(result)


def handle_poll(request_id):
    """Browser polling for the agent's answer to one request.
    ---
    get:
      tags: [ui]
      summary: Poll one request for completion, status text, and stall flag.
      parameters:
        - in: path
          name: request_id
          required: true
          schema: {type: string}
      responses:
        200:
          description: 'Pending: {done: false, status, stalled}. Done: {done: true, kind, response, finished}.'
    """
    payload = agent_queue.read_response(request_id)
    if payload is None:
        result = {"done": False,
                  "status": agent_queue.read_status(request_id),
                  "stalled": rule_stalled(request_id)}
    else:
        kind = payload.get("kind", "answer")
        result = {"done": True, "kind": kind,
                  "response": payload["response"],
                  "finished": dossier_store.rule_finished_stamp()}
        session_log.emit("20003", "response delivered",
                         "id=" + request_id + " kind=" + kind
                         + " chars=" + str(len(payload["response"])))
    return jsonify(result)


def handle_snippet():
    """Re-read one item (left-column refresh after a response, or the
    "load whole file" button with full=1).
    ---
    get:
      tags: [ui]
      summary: Reload one item (verbatim content + provenance) by ref.
      parameters:
        - in: query
          name: ref
          required: true
          schema: {type: string, description: stash-relative path or mail:<acct>:<idx>}
        - in: query
          name: full
          required: false
          schema: {type: string, description: pass 1 to skip snippets.max_chars truncation}
      responses:
        200:
          description: Snippet dict (kind, ref, content, truncated, account, folder, name).
    """
    ref = request.args["ref"]
    full = request.args.get("full") == "1"
    snippet = load_item(ref, full)
    if full:
        session_log.emit("10007", "full item loaded",
                         "ref=" + ref + " chars=" + str(len(snippet["content"])))
    else:
        session_log.emit("10002", "snippet refreshed", "ref=" + ref)
    return jsonify(snippet)


def handle_agent_requests():
    """Agent API: all pending requests. The agent's poll loop entry point.
    ---
    get:
      tags: [agent]
      summary: List pending request payloads, oldest first.
      responses:
        200:
          description: '{"requests": [{id, scope, prompt, snippet}, ...]}'
    """
    pending = agent_queue.list_pending_requests()
    if len(pending) > 0:
        # Only log non-empty fetches; the agent polls this endlessly.
        session_log.emit("30001", "agent fetched pending requests",
                         "count=" + str(len(pending)))
    return jsonify({"requests": pending})


def handle_agent_status():
    """Agent API: post a short in-progress note for one request.
    ---
    post:
      tags: [agent]
      summary: Update the status line shown beside the request's spinner.
      requestBody:
        content:
          application/json:
            schema:
              properties:
                id: {type: string}
                status: {type: string, description: short present-tense note}
      responses:
        200:
          description: '{"ok": true}'
    """
    body = request.get_json()
    agent_queue.write_status(body["id"], body["status"])
    session_log.emit("30002", "agent status update",
                     "id=" + body["id"] + " status=" + body["status"])
    return jsonify({"ok": True})


def handle_agent_respond():
    """Agent API: deliver the final response for one request. The server
    does the whole completion transaction (atomic write, archive, clear
    status) and saves the outcome into the request's dossier -- the agent
    does no file maintenance itself.
    ---
    post:
      tags: [agent]
      summary: Complete a request (write response, archive, save to dossier).
      requestBody:
        content:
          application/json:
            schema:
              properties:
                id: {type: string}
                kind: {type: string, enum: [answer, error, needs_human]}
                response: {type: string, description: plain text for the UI}
                found:
                  type: array
                  items: {type: string}
                  description: session scope only -- item refs found (stash-relative file path, or mail:<acct>:<idx> from the mail index); they become the dossier's items (left column). Refs that do not resolve are dropped.
                view:
                  type: string
                  enum: [explore, mapping]
                  description: session scope only, optional -- the agent's judgement of the diagram view (explore = retrieval-only prompt, mapping = the prompt states goals/tasks). Omit to leave the saved view alone.
                tasks:
                  type: array
                  description: session scope only, optional -- goals and tasks stated by the prompt, for the mapping view. Replaces the saved list; omit to leave it alone.
                  items:
                    type: object
                    properties:
                      label: {type: string}
                      kind: {type: string, enum: [goal, task], default: task}
                      goal: {type: string, description: label of the goal this task hangs under; empty for none}
      responses:
        200:
          description: '{"ok": true, "dropped": [...]} or {"ok": false, "error": "..."}'
    """
    body = request.get_json()
    kind = body.get("kind", "answer")
    found, dropped = dossier_store.valid_found_paths(body.get("found", []))
    view = body.get("view")
    tasks = dossier_store.valid_tasks(body.get("tasks"))
    if kind not in ("answer", "error", "needs_human"):
        error = "unknown kind: " + kind
        request_payload = None
    else:
        error, request_payload = agent_queue.complete_request(
            body["id"], kind, body["response"], found)
    result = {"ok": True, "dropped": dropped}
    if error is not None:
        result = {"ok": False, "error": error}
    else:
        session_log.emit("30003", "agent responded",
                         "id=" + body["id"] + " kind=" + kind
                         + " chars=" + str(len(body["response"]))
                         + " found=" + str(len(found)))
        if len(dropped) > 0:
            session_log.emit("30005", "agent found paths dropped",
                             "id=" + body["id"] + " paths=" + str(dropped))
        dossier = dossier_store.apply_response(request_payload, kind,
                                               body["response"], found,
                                               view, tasks)
        if dossier is not None:
            session_log.emit("30004", "dossier updated from response",
                             "dossier=" + dossier["id"] + " scope="
                             + request_payload["scope"] + " items="
                             + str(len(dossier["items"])) + " view="
                             + dossier["view"] + " tasks="
                             + str(len(dossier["tasks"])))
    return jsonify(result)


def handle_ui_event():
    """Browser-side replay hook: the page posts UI events that never hit
    another route (diagram node clicks, ...) so they land in the session log.
    ---
    post:
      tags: [ui]
      summary: Log a browser UI event into the session log (code 40001).
      requestBody:
        content:
          application/json:
            schema:
              properties:
                event: {type: string, description: short event name}
                fields: {type: string, description: k=v pairs for the log line}
      responses:
        200:
          description: '{"ok": true}'
    """
    body = request.get_json()
    session_log.emit("40001", "browser ui event",
                     "event=" + body["event"] + " " + body.get("fields", ""))
    return jsonify({"ok": True})


def handle_heartbeat():
    """Frontend liveness ping; existing = healthy. Not logged (too chatty).
    ---
    get:
      tags: [ui]
      summary: Liveness ping for the header heartbeat dot.
      responses:
        200:
          description: '{"ok": true}'
    """
    return jsonify({"ok": True})


# --- app setup ---------------------------------------------------------------

def create_app():
    app = Flask(__name__)
    app.add_url_rule("/", "landing", handle_landing)
    app.add_url_rule("/dossier/new", "new_dossier", handle_new_dossier,
                     methods=["POST"])
    app.add_url_rule("/dossier/<dossier_id>", "dossier", handle_dossier)
    app.add_url_rule("/dossier/<dossier_id>/remove", "remove_item",
                     handle_remove_item, methods=["POST"])
    app.add_url_rule("/dossier/<dossier_id>/diagram", "diagram",
                     handle_diagram)
    app.add_url_rule("/dossier/<dossier_id>/view", "set_view",
                     handle_set_view, methods=["POST"])
    app.add_url_rule("/process", "process", handle_process, methods=["POST"])
    app.add_url_rule("/poll/<request_id>", "poll", handle_poll)
    app.add_url_rule("/snippet", "snippet", handle_snippet)
    app.add_url_rule("/heartbeat", "heartbeat", handle_heartbeat)
    app.add_url_rule("/ui-event", "ui_event", handle_ui_event,
                     methods=["POST"])
    # Agent API: localhost calls from the runtime assistant, not the browser.
    app.add_url_rule("/agent/requests", "agent_requests",
                     handle_agent_requests)
    app.add_url_rule("/agent/status", "agent_status",
                     handle_agent_status, methods=["POST"])
    app.add_url_rule("/agent/respond", "agent_respond",
                     handle_agent_respond, methods=["POST"])
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
