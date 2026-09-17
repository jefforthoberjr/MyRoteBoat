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

## mail.<account>.mbox / mail.<account>.index
One entry per mail account. `mbox` is the Google Takeout mailbox export
(stash-relative); `index` is the tab-separated index the stash's own
index_mbox.py built from it (idx, byte_start, byte_end, date, from, to, cc,
subject, labels). An email item is addressed as `mail:<account>:<idx>`; the
server seeks to the row's byte range and parses just that one message, so
the multi-hundred-MB mbox is never read whole. Adding an account = adding
an entry here (plus running index_mbox.py in the stash).

## agent.queue_dir
Root (repo-relative) of the file queue between the web server and the
Claude-session agent: requests/ and responses/ subdirs, one json file per
request. Format documented in src/agent_queue.py and SKILL.md. Gitignored.

## agent.poll_ms
How often (ms) the browser polls /poll/<id> while a process request is
pending. 1000 is plenty; the agent takes seconds-to-minutes anyway.

## agent.status_chars
Max characters of agent status text displayed beside a pending spinner. The
agent overwrites queue/status/<id>.txt with a short note as it works
("scanning stash 120/900"); the server truncates to this length. Keeps the
user informed that a long scan is genuinely progressing vs. stalled.

## agent.stall_seconds
A pending request whose status file (or request file, if no status yet) has
not been touched for this many seconds is flagged stalled: the UI swaps the
status text for an amber "input needed? see CLI" hint. Covers the cases the
agent CANNOT report itself — waiting on a CLI permission prompt, agent
crashed, or no agent session running at all. Clears itself if activity
resumes. Tune upward if legitimate long single steps trip it.

## ui_heartbeat.interval_ms
How often (ms) the browser pings GET /heartbeat. The dot in the top-right
header shows green while pings succeed, red once one fails (server killed,
crashed, etc.). Purely frontend-to-server liveness — says nothing about the
agent session.

## logging.enabled
Master toggle for session logs (sessions/<timestamp>_<seed>.log). Codes and
line format documented in src/session_log.py.

## dossiers.dir
Root (repo-relative) of saved dossiers. Each dossier is a folder named by
its id (timestamp + seed) holding dossier.json (state: prompt, answers,
found items -- shape in src/dossier.py) and session.log (that dossier's own
debug/replay log, appended every time it is loaded). Gitignored.

## dossiers.title_chars
The landing page labels each dossier with the first line of its kickoff
prompt, cut to this many characters.

## dossiers.default_view
Which diagram view a dossier opens in before anyone has chosen: `explore`
(one wide diagram of the items, for retrieval-only prompts) or `mapping`
(items diagram on the left, goals/tasks diagram on the right, for prompts
that state goals). The runtime agent sets the view on its session-scope
answer when it can judge; the two view buttons on the page override it and
the choice is saved in the dossier.

## dossiers.context_turns
Every request carries the agent's memory: the dossier's conversation
thread (every top-box prompt with its answer) and, for a per-item request,
that item's own thread. This caps how many of the most recent turns go
along, so a long-running dossier does not bloat every request. Threads are
stored in full in dossier.json regardless.

## dossiers.found_merge
What happens to a dossier's items when the agent answers the top (session
scope) prompt with a `found` list. `replace`: the agent's list becomes the
items, in the agent's order; a path that was already an item keeps its saved
chat_response, everything else is dropped. Good for "refine the search"
re-processing. `append`: existing items stay, unseen paths are added after
them -- nothing found is ever lost, at the cost of a growing column.

## snippets.source
Where the left column's items come from when a dossier page renders.
`dossier`: the dossier's saved items list (empty for a brand new dossier
until the agent answers the kickoff prompt). `recent`: the v0 stand-in rule,
the N most recently modified work/text files regardless of dossier -- kept
as a toggle for testing the layout without an agent running.

## snippets.count
How many snippets the left column shows. The current pick rule
(rule_pick_snippets, v0) takes the N most recently modified .txt files under
work/text/ — a stand-in until chat-driven retrieval exists.

## snippets.max_chars
Snippet content longer than this is truncated for display (a "truncated" note
appears under the card). The full file always remains untouched on disk.

## diagram.direction
Layout direction of the item diagram (Mermaid flowchart) drawn between the
dossier prompt and the two columns. Counter-intuitively, `TB` (top-to-
bottom) lays UNCONNECTED items out as one horizontal row, with reply chains
hanging down from their first mail -- compact in the 40vh box. `LR` stacks
unconnected items into a tall column instead. Mermaid also accepts RL/BT.

## diagram.mapping_direction
Same knob for the items diagram when the mapping view shows it at half
width. `LR` there stacks unconnected items into a tall narrow column with
reply chains running sideways, spending height instead of shrinking the
boxes to fit. Set it to `TB` to keep the explore layout (scaled down).

## diagram.label_chars
Each diagram node shows the item's account and name; the name is cut at
this many characters so a long Drive path doesn't blow the box wide.

## diagram.kinds
One entry per node kind: item kinds (`file`, `mail`; more as new sources
arrive) and the mapping view's `goal` and `task`. Each gives the legend
label and the box fill/stroke colors. Both the legend and
the item diagram build their Mermaid classDef lines from here, so a color
tweak changes both in one place. An item whose kind is missing here falls
back to Mermaid's default box.

## diagram.chain
Which rule draws arrows between mail items in the diagram (file items never
get arrows). `headers`: real reply threading -- a mail's In-Reply-To, then
its References newest-first, is matched against the displayed mails and the
first hit becomes the parent, so a reply to a mail that is not in the
dossier still links to its nearest displayed ancestor. `sender`: every
sender's mails are chained in date order, which turns an automated drip
campaign (no reply headers) into a visible sequence. `none`: boxes only.

## ui.title
Browser tab / page heading title.

## ui.initial_prompt
The session-kickoff prompt pre-filled into the top box (above both columns).
Currently a hardcoded example; later this becomes whatever the user actually
typed to start the session (and this knob becomes just a dev default).
