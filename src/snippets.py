"""Snippet model -- picks files from the stash and packages each as a snippet
dict for the left column: verbatim content plus full provenance (account,
original folder path, file name, and the real on-disk path).

Snippet dict shape (the template's contract, shared with mail.py):
    kind       "file" | "mail"
    ref        the item reference: a stash-relative path, or mail:<acct>:<idx>
    content    verbatim file text (possibly truncated, flag set if so)
    truncated  True if content was cut at snippets.max_chars
    account    which account/subtree it came from (e.g. "usa", "nz", "work")
    folder     the ORIGINAL folder path (decoded from __ separators)
    name       the display file name (last path piece, extraction suffix kept)
    disk_path  actual path on disk, relative to the stash root (files only)
"""
import mail
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
    snippet["kind"] = "file"
    snippet["content"] = text
    snippet["truncated"] = truncated
    snippet["disk_path"] = str(path.relative_to(stash_dir()))
    snippet["ref"] = snippet["disk_path"]
    return snippet


def resolve_stash_path(disk_path):
    """A relative path pinned inside the stash root (raises if it escapes)."""
    full = (stash_dir() / disk_path).resolve()
    if not str(full).startswith(str(stash_dir().resolve())):
        raise ValueError("path escapes stash: " + disk_path)
    return full


def ref_exists(ref):
    """True if a ref names a real stash file or a known mail index row."""
    result = False
    if mail.parse_ref(ref) is not None:
        result = mail.ref_exists(ref)
    else:
        try:
            result = resolve_stash_path(ref).is_file()
        except ValueError:
            result = False
    return result


def load_item(ref):
    """Load any item ref into a snippet dict: mail refs via mail.py,
    everything else as a stash file."""
    if mail.parse_ref(ref) is not None:
        snippet = mail.load_mail_snippet(ref)
    else:
        snippet = load_snippet(resolve_stash_path(ref))
    return snippet


def gather_snippets():
    """The v0 left column: pick files per the recency rule, load each."""
    snippets = []
    for path in rule_pick_snippets():
        snippets.append(load_snippet(path))
    return snippets


def gather_dossier_snippets(dossier):
    """The left column for a saved dossier: one snippet per item, in saved
    order, carrying the item's saved chat_response. Items whose ref no
    longer resolves are skipped rather than crashing the page."""
    snippets = []
    for item in dossier["items"]:
        if ref_exists(item["ref"]):
            snippet = load_item(item["ref"])
            snippet["chat_response"] = item.get("chat_response", "")
            snippet["finished"] = item.get("finished", "")
            snippets.append(snippet)
    return snippets
