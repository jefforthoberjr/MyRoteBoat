# CONFIG REFERENCE

Full prose for every knob in src/assets/config.yaml, keyed by dotted name.
config.yaml keeps the one-line label; this file keeps the explanation.

## server.host
Bind address for the Flask server. Stays 127.0.0.1 — this app is single-user,
laptop-only, no auth. Never bind 0.0.0.0.

## server.port
Port for the web UI. 8474 chosen arbitrarily (unlikely to collide with common
dev servers on 5000/8000/8080).

## server.debug
Flask debug mode: auto-reloads on code edits and shows tracebacks in the
browser. Fine for this local single-user app; would be a security hole on
anything network-facing.

## data.stash_dir
Root of the read-only local file stash (Google Takeout exports of gmail +
drive). `~` is expanded at load time. The app must NEVER write into, move, or
delete anything under this directory. Future: swap for live gmail/drive
connectors.

## agent.queue_dir
Root (repo-relative) of the file queue between the web server and the
Claude-session agent: requests/ and responses/ subdirs, one json file per
request. Format documented in src/agent_queue.py and SKILL.md. Gitignored.

## agent.poll_ms
How often (ms) the browser polls /poll/<id> while a process request is
pending. 1000 is plenty; the agent takes seconds-to-minutes anyway.

## logging.enabled
Master toggle for session logs (sessions/<timestamp>_<seed>.log). Codes and
line format documented in src/session_log.py.

## snippets.count
How many snippets the left column shows. The current pick rule
(rule_pick_snippets, v0) takes the N most recently modified .txt files under
work/text/ — a stand-in until chat-driven retrieval exists.

## snippets.max_chars
Snippet content longer than this is truncated for display (a "truncated" note
appears under the card). The full file always remains untouched on disk.

## ui.title
Browser tab / page heading title.
