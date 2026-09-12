"""Session logger -- captures one server run under sessions/ for later
replay/analysis (agents.md SESSIONS AND REPLAY FEATURE).

One file per server run: sessions/<timestamp>_<seed>.log
Line format (same shape as wordtetris, so tooling habits carry over):

    [NNNNN] 12.345 | human readable sentence | k=v k=v

Log codes (append-only, never reuse a number):
    00001  session started
    10001  index page rendered
    10002  snippet refreshed (left column re-read from disk)
    20001  process clicked (request received from browser)
    20002  request file written to queue
    20003  response delivered to browser

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


def emit(code, human, fields):
    """Append one log line; no-op when logging is off / no session open."""
    if _file is not None:
        elapsed = time.monotonic() - _start
        line = "[" + code + "] " + format(elapsed, ".3f")
        line = line + " | " + human + " | " + fields
        _file.write(line + "\n")
        _file.flush()
