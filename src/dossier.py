"""Dossier store -- one saved user "session" of the app: the kickoff prompt,
its answer, and the found items (left column) with their per-item answers.

Layout (root set by config dossiers.dir, repo-relative):
    dossiers/<id>/dossier.json   the dossier state, rewritten whole on save
    dossiers/<id>/session.log    that dossier's own debug/replay log; opened
                                 (append) every time the dossier is loaded,
                                 see session_log.switch_to

dossier.json shape (the template's contract):
    id               folder name, timestamp + seed
    created          human timestamp
    title            short label for the landing list (prompt's first line)
    prompt           the top-box text as last submitted
    prompt_response  the agent's answer to the top box ("" until answered)
    prompt_finished  when that answer landed ("" until answered)
    view             "explore" (one wide item diagram) | "mapping" (items
                     left, goals/tasks right); the agent's call, user-toggled
    tasks            [{"label", "kind": "goal"|"task", "goal": <goal label or ""}]
                     the mapping view's right-hand diagram; [] until the
                     agent sends some
    items            [{"ref": <stash path or mail:<acct>:<idx>>,
                       "chat_response": "", "finished": ""}]
                     (older files used "disk_path"; load_dossier migrates)
"""
import json
import random
import time
from pathlib import Path

import snippets
from config import CONFIG


# --- rules -------------------------------------------------------------------

def rule_dossier_id():
    """Folder name for a new dossier: local timestamp + 4 hex seed. Sorts
    by creation time when listing the dir by name; seed avoids same-second
    clashes."""
    stamp = time.strftime("%Y-%m-%dT%H-%M-%S")
    seed = format(random.randrange(16 ** 4), "04x")
    return stamp + "_" + seed


def rule_dossier_title(prompt):
    """Landing-list label: the prompt's first line, cut at
    dossiers.title_chars."""
    first_line = prompt.strip().split("\n")[0]
    max_chars = CONFIG["dossiers"]["title_chars"]
    title = first_line[:max_chars]
    if title == "":
        title = "(untitled)"
    return title


def rule_finished_stamp():
    """The "finished" text shown under a box once its answer lands: local
    wall-clock time to the second."""
    return "finished " + time.strftime("%Y-%m-%d %H:%M:%S")


def rule_merge_found(items, found_paths):
    """How a session-scope answer's found list becomes the dossier's items,
    per config dossiers.found_merge. "replace": the new list IS the dossier
    (order from the agent), but an item that survives keeps its saved
    chat_response. "append": keep existing items, add unseen paths after."""
    by_ref = {}
    for item in items:
        by_ref[item["ref"]] = item
    merged = []
    if CONFIG["dossiers"]["found_merge"] == "append":
        merged = list(items)
    seen = set()
    for item in merged:
        seen.add(item["ref"])
    for ref in found_paths:
        if ref not in seen:
            seen.add(ref)
            if ref in by_ref:
                merged.append(by_ref[ref])
            else:
                merged.append({"ref": ref, "chat_response": "",
                               "finished": ""})
    return merged


# --- paths -------------------------------------------------------------------

def _dossiers_root():
    root = Path(__file__).resolve().parent.parent / CONFIG["dossiers"]["dir"]
    root.mkdir(parents=True, exist_ok=True)
    return root


def dossier_dir(dossier_id):
    return _dossiers_root() / dossier_id


def dossier_log_path(dossier_id):
    return dossier_dir(dossier_id) / "session.log"


def _json_path(dossier_id):
    return dossier_dir(dossier_id) / "dossier.json"


# --- store -------------------------------------------------------------------

def create_dossier(prompt):
    """New dossier folder + json with no items yet; returns the dict."""
    dossier = {
        "id": rule_dossier_id(),
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "title": rule_dossier_title(prompt),
        "prompt": prompt,
        "prompt_response": "",
        "prompt_finished": "",
        "view": CONFIG["dossiers"]["default_view"],
        "tasks": [],
        "items": [],
    }
    dossier_dir(dossier["id"]).mkdir(parents=True, exist_ok=True)
    save_dossier(dossier)
    return dossier


def save_dossier(dossier):
    """Rewrite the whole json (tmp + rename so a reader never sees a half
    file)."""
    path = _json_path(dossier["id"])
    tmp_path = path.with_suffix(".json.tmp")
    with open(tmp_path, "w") as f:
        json.dump(dossier, f, indent=2)
    tmp_path.replace(path)


def load_dossier(dossier_id):
    """The dossier dict, or None if there is no such folder/json."""
    result = None
    path = _json_path(dossier_id)
    if path.is_file():
        with open(path, "r") as f:
            result = json.load(f)
        for item in result["items"]:
            if "ref" not in item:   # pre-mail dossiers stored disk_path
                item["ref"] = item.pop("disk_path")
        if "view" not in result:    # pre-mapping dossiers
            result["view"] = CONFIG["dossiers"]["default_view"]
            result["tasks"] = []
    return result


def list_dossiers():
    """Landing-page rows, newest first: id, created, title, item_count."""
    rows = []
    for folder in sorted(_dossiers_root().iterdir(), reverse=True):
        dossier = load_dossier(folder.name)
        if dossier is not None:
            rows.append({
                "id": dossier["id"],
                "created": dossier["created"],
                "title": dossier["title"],
                "item_count": len(dossier["items"]),
            })
    return rows


# --- applying agent responses ------------------------------------------------

def valid_found_paths(found_paths):
    """Filter an agent's found list to refs that resolve: a real file
    inside the stash, or a mail ref present in that account's index;
    returns (kept, dropped)."""
    kept = []
    dropped = []
    for ref in found_paths:
        if snippets.ref_exists(ref):
            kept.append(ref)
        else:
            dropped.append(ref)
    return kept, dropped


def valid_tasks(raw_tasks):
    """Normalize an agent's goals/tasks list: each entry needs a non-empty
    label; kind defaults to "task" (only "goal"/"task" allowed); goal is
    the label of the goal a task hangs under ("" = none). Junk entries are
    dropped. None in -> None out (meaning: leave the saved list alone)."""
    result = None
    if raw_tasks is not None:
        result = []
        for raw in raw_tasks:
            label = str(raw.get("label", "")).strip()
            kind = raw.get("kind", "task")
            if label != "" and kind in ("goal", "task"):
                result.append({"label": label, "kind": kind,
                               "goal": str(raw.get("goal", "")).strip()})
    return result


def apply_response(request_payload, kind, response_text, found_paths,
                   view, tasks):
    """Save a completed request's outcome into its dossier: an "answer" to
    the session scope sets prompt_response, merges found_paths into items,
    and -- when the agent sent them -- sets the view and replaces the
    goals/tasks list; an answer to a snippet scope sets that item's
    chat_response. Non-answer kinds save nothing (the UI keeps the prompt
    for a retry). Returns the dossier dict, or None if it no longer exists."""
    dossier = load_dossier(request_payload["dossier_id"])
    if dossier is not None and kind == "answer":
        stamp = rule_finished_stamp()
        if request_payload["scope"] == "session":
            dossier["prompt_response"] = response_text
            dossier["prompt_finished"] = stamp
            dossier["items"] = rule_merge_found(dossier["items"], found_paths)
            if view in ("explore", "mapping"):
                dossier["view"] = view
            if tasks is not None:
                dossier["tasks"] = tasks
        else:
            target = request_payload["snippet"]["ref"]
            for item in dossier["items"]:
                if item["ref"] == target:
                    item["chat_response"] = response_text
                    item["finished"] = stamp
        save_dossier(dossier)
    return dossier


def set_view(dossier_id, view):
    """The user's explore/mapping toggle, saved so a reload keeps it.
    Returns True if saved, False for an unknown dossier or view."""
    result = False
    dossier = load_dossier(dossier_id)
    if dossier is not None and view in ("explore", "mapping"):
        dossier["view"] = view
        save_dossier(dossier)
        result = True
    return result


def remove_item(dossier_id, ref):
    """Drop one item (by ref) from a dossier. Returns the new item count,
    or None if the dossier does not exist."""
    result = None
    dossier = load_dossier(dossier_id)
    if dossier is not None:
        kept = []
        for item in dossier["items"]:
            if item["ref"] != ref:
                kept.append(item)
        dossier["items"] = kept
        save_dossier(dossier)
        result = len(kept)
    return result
