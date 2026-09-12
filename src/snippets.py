"""Snippet model -- picks files from the stash and packages each as a snippet
dict for the left column: verbatim content plus full provenance (account,
original folder path, file name, and the real on-disk path).

Snippet dict shape (the template's contract):
    content    verbatim file text (possibly truncated, flag set if so)
    truncated  True if content was cut at snippets.max_chars
    account    which account/subtree it came from (e.g. "usa", "nz", "work")
    folder     the ORIGINAL folder path (decoded from __ separators)
    name       the display file name (last path piece, extraction suffix kept)
    disk_path  actual path on disk, relative to the stash root
"""
from config import CONFIG, stash_dir


# --- rules (swappable behavior toward the top, per agents.md) ----------------

def rule_pick_snippets():
    """Which stash files land in the left column. v0 rule (no chat yet):
    the N most recently modified .txt files under work/text/, so the page
    always shows something real. Replaced later by chat-driven retrieval."""
    text_root = stash_dir() / "work" / "text"
    candidates = []
    if text_root.is_dir():
        for path in text_root.rglob("*.txt"):
            candidates.append(path)
    candidates.sort(key=_mtime_of, reverse=True)
    count = CONFIG["snippets"]["count"]
    return candidates[:count]


def rule_snippet_provenance(path):
    """How a stash path maps to (account, folder, name). The extracted-text
    trees (work/text/<account>/) flatten the original Drive folder path into
    the file name with "__" separators -- decode that back out. Anything else
    falls back to its literal relative dir path, account = first path piece."""
    relative = path.relative_to(stash_dir())
    pieces = relative.parts
    account = pieces[0]
    folder = str(relative.parent)
    name = relative.name
    if len(pieces) >= 3 and pieces[0] == "work" and pieces[1] == "text":
        account = pieces[2]
        segments = relative.name.split("__")
        name = segments[-1]
        folder = " / ".join(segments[:-1])
    return {"account": account, "folder": folder, "name": name}


# --- loading -----------------------------------------------------------------

def _mtime_of(path):
    return path.stat().st_mtime


def load_snippet(path):
    """Read one stash file into a snippet dict (see module docstring)."""
    max_chars = CONFIG["snippets"]["max_chars"]
    text = path.read_text(errors="replace")
    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars]
        truncated = True
    snippet = rule_snippet_provenance(path)
    snippet["content"] = text
    snippet["truncated"] = truncated
    snippet["disk_path"] = str(path.relative_to(stash_dir()))
    return snippet


def gather_snippets():
    """The left column's data: pick files per the rule, load each one."""
    snippets = []
    for path in rule_pick_snippets():
        snippets.append(load_snippet(path))
    return snippets
