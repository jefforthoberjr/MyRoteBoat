"""Session logger -- captures one server run under sessions/ for later
replay/analysis (agents.md SESSIONS AND REPLAY FEATURE).

One file per server run: sessions/<timestamp>_<seed>.log -- the "lobby"
log, for everything before a dossier is opened (landing page, creation).
Loading a dossier switches the log to that dossier's own file
(dossiers/<id>/session.log, appended across loads) so every dossier carries
its complete debug/replay history. Elapsed times restart at each switch.
Line format (same shape as wordtetris, so tooling habits carry over):

    [NNNNN] 12.345 | human readable sentence | k=v k=v

Log codes (append-only, never reuse a number):
    00001  session started
    00002  log switched to a dossier's own file
    10001  index page rendered
    10003  landing page rendered
    10004  dossier created
    10005  dossier loaded
    10006  dossier item removed (X clicked)
    10007  full item loaded (truncation skipped on request)
    10008  diagram source built (nodes/edges counts)
    10009  diagram refreshed (button or after an item removal)
    40001  browser ui event (posted by the page: diagram node clicked, ...)
    10002  snippet refreshed (left column re-read from disk)
    20001  process clicked (request received from browser)
    20002  request file written to queue
    20003  response delivered to browser
    30001  agent fetched pending requests (non-empty fetches only)
    30002  agent status update posted
    30003  agent responded (completion transaction ran)
    30004  dossier updated from a response (found paths merged / answer saved)
    30005  agent found paths dropped (not files inside the stash)

Gated by config logging.enabled; when off every emit() is a safe no-op so
call sites never guard."""
import random
import time
from pathlib import Path

from config import CONFIG

_SESSIONS_DIR = Path(__file__).resolve().parent.parent / "sessions"

_file = None
_start = None


def open_session():
    global _file, _start
    if CONFIG["logging"]["enabled"]:
        _SESSIONS_DIR.mkdir(exist_ok=True)
        stamp = time.strftime("%Y-%m-%dT%H-%M-%S")
        seed = format(random.randrange(16 ** 4), "04x")
        path = _SESSIONS_DIR / (stamp + "_" + seed + ".log")
        _file = open(path, "a")
        _start = time.monotonic()
        emit("00001", "session started", "")


def switch_to(path, dossier_id):
    """Redirect logging to a dossier's own file (append). Closes the
    current file first; no-op when logging is off."""
    global _file, _start
    if _file is not None:
        _file.close()
        _file = open(path, "a")
        _start = time.monotonic()
        emit("00002", "log switched to dossier", "id=" + dossier_id)


def emit(code, human, fields):
    """Append one log line; no-op when logging is off / no session open."""
    if _file is not None:
        elapsed = time.monotonic() - _start
        line = "[" + code + "] " + format(elapsed, ".3f")
        line = line + " | " + human + " | " + fields
        _file.write(line + "\n")
        _file.flush()
