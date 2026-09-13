"""Mail snippets -- one email out of a Takeout mbox, addressed by the stash's
own mail index (work/<account>_mail_index.tsv, built by the stash's
index_mbox.py: idx, byte_start, byte_end, date, from, to, cc, subject,
labels). The mbox itself is never loaded whole: seek to the row's byte
range, parse that one message with the stdlib email package.

Ref format (what the agent sends in `found` and what items store):
    mail:<account>:<idx>        e.g. mail:nz:619

Per-account mbox + index paths (stash-relative) live in config mail.*.
"""
import email
import email.policy
import html
import re
from pathlib import Path

from config import CONFIG, stash_dir

_index_cache = {}   # account -> {idx: (start, end, date, sender, subject, labels)}


# --- rules -------------------------------------------------------------------

def rule_mail_body(message):
    """Which part of a message becomes the snippet text: the first
    text/plain part; failing that, the first text/html part with tags
    stripped. Attachments are listed, not inlined."""
    body = None
    for part in message.walk():
        if not part.is_multipart() and part.get_filename() is None:
            if part.get_content_type() == "text/plain" and body is None:
                body = part.get_content()
    if body is None:
        for part in message.walk():
            if part.get_content_type() == "text/html" and body is None:
                body = _strip_html(part.get_content())
    if body is None:
        body = ""
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body


def rule_mail_content(message, body):
    """How an email renders in the left column: a short header block (the
    fields a person scans first), attachment names, then the body."""
    lines = []
    for header in ("Date", "From", "To", "Cc", "Subject"):
        if message.get(header):
            lines.append(header + ": " + str(message.get(header)))
    attachments = []
    for part in message.walk():
        if part.get_filename() is not None:
            attachments.append(part.get_filename())
    if len(attachments) > 0:
        lines.append("Attachments: " + ", ".join(attachments))
    return "\n".join(lines) + "\n\n" + body


# --- index -------------------------------------------------------------------

def parse_ref(ref):
    """'mail:nz:619' -> ('nz', '619'); None if not a mail ref."""
    result = None
    pieces = ref.split(":")
    if len(pieces) == 3 and pieces[0] == "mail":
        result = (pieces[1], pieces[2])
    return result


def _account_paths(account):
    entry = CONFIG["mail"][account]
    return stash_dir() / entry["mbox"], stash_dir() / entry["index"]


def _index_for(account):
    """The account's index rows keyed by idx, read once per process."""
    if account not in _index_cache:
        rows = {}
        _mbox_path, index_path = _account_paths(account)
        with open(index_path, "r", encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 9:
                    rows[p[0]] = (int(p[1]), int(p[2]), p[3], p[4], p[7], p[8])
        _index_cache[account] = rows
    return _index_cache[account]


def ref_exists(ref):
    """True if the ref names a known account and an idx in its index."""
    result = False
    parsed = parse_ref(ref)
    if parsed is not None and parsed[0] in CONFIG["mail"]:
        result = parsed[1] in _index_for(parsed[0])
    return result


# --- loading -----------------------------------------------------------------

def load_mail_snippet(ref):
    """Read one email into a snippet dict (same contract as a file snippet:
    kind, ref, account, folder, name, content, truncated)."""
    account, idx = parse_ref(ref)
    start, end, date, sender, subject, labels = _index_for(account)[idx]
    mbox_path, _index_path = _account_paths(account)
    with open(mbox_path, "rb") as f:
        f.seek(start)
        raw = f.read(end - start)
    raw = raw.split(b"\n", 1)[1]   # drop the mbox "From " separator line
    message = email.message_from_bytes(raw, policy=email.policy.default)
    content = rule_mail_content(message, rule_mail_body(message))
    max_chars = CONFIG["snippets"]["max_chars"]
    truncated = False
    if len(content) > max_chars:
        content = content[:max_chars]
        truncated = True
    snippet = {
        "kind": "mail",
        "ref": ref,
        "account": account,
        "folder": date[:10] + " — " + sender + " — " + labels,
        "name": subject,
        "content": content,
        "truncated": truncated,
    }
    return snippet


def _strip_html(text):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text,
                  flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)
