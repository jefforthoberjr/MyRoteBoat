
# TECH STACK and DEV OPS
We are using python3.

We are using the "C" version of python (i.e. not Java or .Net)

I am editing in vscode, with minimal plugins

We are using venv and pip to manage libs/dependencies.
Example commands:
`python3.12 -m venv venv`

`source venv/bin/activate`
`pip install -r requirements.txt`
`pipreqs ./src`

We are keeping the set of local build commands very simple. We are only doing local development, with minimum distributed components.

`python ./src/main.py`

I am storing everything in a git repo. DO NOT add/commit with git. I am in charge of adding and commiting. I will be committing often.

I have unit tests.
`pytest`
`pytest tests/test_main.py`


# WEB STACK
We are using Flask (decided 2026-09-12) as the local web server: minimal,
stable, boring — fits the "changes infrequently" core value. Localhost only,
single user, no auth.

Frontend is plain HTML/CSS/JS served by Flask. No frontend framework unless we
later decide otherwise (each new library requires discussion first, per
agents.md).

Flask routes are registered with `app.add_url_rule(...)` instead of the
`@app.route` decorator, to honor the "avoid decorators" python style rule below.


# PYTHON STYLE
Avoid python decorators. No need for the syntax sugar.

Avoid multiple return statements in a function. This will make embedding wrappers more easily during future refactors.

Prefer clear multiline loops over "list comprehension"

Avoid "//" operator, use math.floor instead

Avoid formal polymorphism typing; just use duck typing

Avoid raw pixel math; instead things should be relative to screen size.


# RUN APP

Two processes, two terminals, both from the repo root:

Terminal 1 — the web server (then open http://127.0.0.1:8474/):

    source venv/bin/activate
    python src/main.py

Terminal 2 — the RUNTIME ASSISTANT (a lean Claude Code session on the
subscription; this is the ONLY thing that answers "process" requests —
without it the spinner spins forever). It answers queue requests and never
edits code:

    claude --settings tools/runtime_settings.json "/roteboat"

The --settings file locks the session to its role at the permission level:
Edit/Write denied, Read of repo code and docs denied (it needs only its
skill file), git and rm denied, and the harness's file-changed-on-disk
notices suppressed via CLAUDE_CODE_FILE_WATCHER_SUPPRESS_NOTIFICATIONS so
the dev session's edits are never echoed at the runtime terminal. Dev sessions do NOT pass it (they use the repo defaults). Launching
without it still works — the role rules in the skill/agents.md are then merely
advisory.

Or start interactively and type the skill invocation yourself:

    claude --settings tools/runtime_settings.json
    > /roteboat

Useful variants (compose with --settings as above):

    claude --effort low "/roteboat"     # cheaper/faster per step; fine for
                                        # simple lookup/summarize requests
    claude --continue                   # resume the previous agent session

The agent loops: watch queue/requests/, write status to queue/status/,
answer into queue/responses/, archive to queue/requests/done/. Full contract
in .claude/skills/roteboat/SKILL.md. Stop it with Ctrl+C (in-flight browser
requests keep polling and pick up seamlessly when a new agent starts).

Separate from both: the DEVELOPER ASSISTANT session, where the app's code
gets written. Kick one off with:

    claude "/roteboat-dev"

Role rules (also in agents.md): the runtime assistant never edits code/docs
(writes only under queue/); the developer assistant never answers queue
requests. One session, one role — don't mix them.


# API DOC (SWAGGER)

openapi.yaml at the repo root documents both API surfaces: tag "ui"
(browser-facing) and tag "agent" (the runtime assistant's localhost API).
It is GENERATED from the route docstrings in src/main.py (the OpenAPI block
after the "---" line in each handler), via apispec + apispec-webframeworks.

Regenerate manually anytime (venv active, from the repo root):

    python tools/generate_swagger.py

The developer assistant regenerates it agentically after any route change.
Local document only — the app does not serve it (may change later). The
runtime agent has read access to it.


# CONFIG REFERENCE
src/assets/config.yaml is the single edit point for tuning, kept scannable: a
flat wall of keys, the commented-out toggle alternatives, and a terse one-line
label per knob. The FULL prose for every knob lives in CONFIG_REFERENCE.md,
keyed by the same dotted name — search that file for a key to get the details.

When you add or change a rule: put the short label in config.yaml and the
explanation in CONFIG_REFERENCE.md under a matching heading. Do NOT grow
multi-paragraph comments back into config.yaml.


# TECH DECISIONS LOG
A running list of decisions as we make them, newest last. One line each; the
prose (if needed) goes in the relevant section above.

- 2026-09-12: Flask chosen as web server (over stdlib http.server).
- 2026-09-12: Claude Code session (subscription) is the LLM agent; no direct
  pay-per-token API calls. Requests flow through a file queue — see
  .claude/skills/roteboat/SKILL.md.
- 2026-09-13: Two explicit roles/skills: developer assistant (/roteboat-dev)
  vs runtime assistant (/roteboat). Dev-only working rules moved from
  agents.md into the dev skill; runtime launches with
  tools/runtime_settings.json to enforce its write boundary.
- 2026-09-13: Queue maintenance moved from agentic bash into python: the
  runtime agent talks only to the /agent/* HTTP endpoints (fetch/status/
  respond); the server owns all queue file I/O. Runtime agent now writes
  no files at all.
- 2026-09-13: apispec + apispec-webframeworks generate openapi.yaml from
  route docstrings (tools/generate_swagger.py). UI API vs agent API split
  expressed as swagger tags.
