---
name: roteboat
description: Run the MyRoteBoat app agent loop — serve the dossier web UI, watch for "process" requests fired from the browser, answer them using the local file stash, and write responses back for the UI to display. Load this skill when the user says to "run roteboat", "start the app agent", or similar.
---

# RoteBoat Agent Skill

## What this app is

MyRoteBoat is a personal, single-user, laptop-only web app. It is a wrapper UI
over Jeff's existing stash of exported Gmail/Drive files, used to assemble a
"dossier" of information needed before performing a real-life task (financial,
jobs, etc.). The goal is to minimize time spent inside email clients and
websites: gather everything first, snapshot it, do the task, then report back
notes for future retrieval.

Read `agents.md` at the repo root before doing anything — it holds the core
values and working rules (200-line code chunks, rules-engine style, session
logging, pause before new libraries).

## Data source

Local snapshot only (for now): `~/Downloads/all-my-google-files/`
(subtrees: `all-my-nz-google-files/`, `all-my-usa-google-files/`, `work/`,
`extracted/` — Google Takeout exports). Read-only: never modify, move, or
delete files in the stash. Live Gmail/Drive integration may come later.

## User session shape

1. Jeff types a chat request; 3–4 rounds of follow-up questions refine it.
2. The UI shows a 2-column layout, split down the middle. ONE scrollbar
   drives both columns: each snippet and its chat box form an aligned row
   (tops flush), with blank space padding the shorter side.
   - LEFT: retrieved snippets/documents, shown verbatim as stored. Every
     snippet displays its provenance: file name, original/effective dir path,
     and which account it came from.
   - RIGHT: one free-text box per left-side item (8 snippets → 8 text boxes),
     each with a "process" button and a loading spinner while a request runs.
3. "Process" fires a request scoped to that one left-side item. The response
   text REPLACES the user's text in that box, and the related left-side item
   refreshes.
4. When the dossier is complete, it is snapshotted. Jeff performs the real
   task offline (browser, phone call, etc.).
5. Post-task: Jeff reports back what transpired; notes are stored for future
   use, and the agent may suggest refinements to how notes/information are
   organized.

## Architecture: Claude Code session as the agent

No direct Anthropic API calls. All LLM token usage flows through a Claude Code
session (Jeff's subscription). The mechanism:

1. Jeff starts a Claude Code session in this repo and loads this skill.
2. The local web server (Python) serves the UI and, when a "process" button is
   clicked, writes a request file into a queue directory (path set in
   `src/assets/config.yaml`) and shows the spinner.
3. This Claude session is the standby/polling/callback element: it watches the
   queue, picks up each request, does the retrieval/summarization work against
   the local stash, and writes a response file.
4. The web server sees the response file and pushes the result to the browser:
   spinner off, text box replaced with the response, left column refreshed.

### Queue format (implemented in src/agent_queue.py)

Queue root: `queue/` at the repo root (config `agent.queue_dir`).

- `queue/requests/<id>.json` — written by the server. Payload:
  `{"id": ..., "prompt": "<the user's text box content>", "snippet": {...}}`
  where snippet carries `content` (possibly truncated), `truncated`,
  `account`, `folder`, `name`, `disk_path` (relative to the stash root).
- `queue/responses/<id>.json` — written by YOU (the agent). Payload:
  `{"id": "<same id>", "response": "<plain text answer>"}`

Write responses atomically: write to a temp file in `queue/responses/`
(e.g. `<id>.json.tmp`), then rename to `<id>.json`. The server treats the
file's existence as "done", so it must never see a half-written json.

After answering, move the request file into `queue/requests/done/` so the
pending set stays clean and nothing is answered twice.

### Agent loop

While acting as the agent, loop: list `queue/requests/*.json`; for each
pending request, read it, do the work, write the response, archive the
request. If the snippet was truncated, read the full file from the stash at
`<stash_dir>/<disk_path>` before answering. When the queue is empty, wait
briefly (a few seconds) and check again.

## Agent behavior rules

- Responses go verbatim into a UI text box — plain text, concise, no markdown
  headers or decoration.
- Left-column content is Jeff's stored information shown VERBATIM; never
  paraphrase it. Summarizing/answering happens only in the right-column
  response.
- Requests are scoped to the single left-side item they were fired from.
- Follow the config.yaml rules-engine conventions when behavior is
  configurable; rule functions carry "rule" in their name.

## Status

v1 — server, 2-column UI, queue, and session logging exist. Retrieval is
still the v0 stand-in rule (most recent work/text files), not chat-driven.
This skill is a living document; update it as pieces are built.
