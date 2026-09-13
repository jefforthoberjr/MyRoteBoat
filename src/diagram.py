"""Item diagram -- the Mermaid flowchart drawn between the dossier prompt
and the two columns: one node per left-column item. The server writes the
Mermaid source text; the browser (vendored src/static/mermaid.min.js,
pinned 11.4.1) renders it.

Node ids are item<index> matching the row/chat ids in the page, so a click
on a node scrolls to its row. Arrows show email chains; which chain rule
applies is config diagram.chain."""
from config import CONFIG


# --- rules -------------------------------------------------------------------

def rule_diagram_source(snippets, view):
    """The whole Mermaid text for a dossier's items: direction per view
    (config diagram.direction / diagram.mapping_direction), one labeled
    node per item, click hooks, then edges."""
    direction = CONFIG["diagram"]["direction"]
    if view == "mapping":
        direction = CONFIG["diagram"]["mapping_direction"]
    lines = ["flowchart " + direction]
    for index, snippet in enumerate(snippets):
        node = "item" + str(index)
        lines.append(node + "[\"" + rule_node_label(snippet) + "\"]")
        lines.append("click " + node + " call diagramClick(\"" + str(index) + "\")")
        if snippet["kind"] in CONFIG["diagram"]["kinds"]:
            lines.append("class " + node + " " + snippet["kind"])
    for edge in rule_diagram_edges(snippets):
        lines.append(edge)
    for line in _class_defs():
        lines.append(line)
    return "\n".join(lines)


def rule_tasks_source(tasks):
    """The mapping view's right-hand diagram: goal boxes with their tasks
    hanging below (edge goal --> task by goal label); tasks with no or an
    unknown goal float free. Empty list -> a diagram with no nodes."""
    lines = ["flowchart TB"]
    goal_node = {}
    for index, task in enumerate(tasks):
        if task["kind"] == "goal":
            goal_node[task["label"]] = "t" + str(index)
    for index, task in enumerate(tasks):
        node = "t" + str(index)
        lines.append(node + "[\"" + _escape_label(task["label"]) + "\"]")
        lines.append("class " + node + " " + task["kind"])
        if task["kind"] == "task" and task["goal"] in goal_node:
            lines.append(goal_node[task["goal"]] + " --> " + node)
    for line in _class_defs():
        lines.append(line)
    return "\n".join(lines)


def rule_legend_source():
    """The legend drawn above the item diagram: one box per configured
    kind, in config order, colored exactly like the items of that kind.
    TB, because mermaid lays unconnected nodes out as a row in TB (and as
    a column in LR)."""
    lines = ["flowchart TB"]
    for kind in CONFIG["diagram"]["kinds"]:
        label = CONFIG["diagram"]["kinds"][kind]["label"]
        lines.append("legend_" + kind + "[\"" + _escape_label(label) + "\"]")
        lines.append("class legend_" + kind + " " + kind)
    for line in _class_defs():
        lines.append(line)
    return "\n".join(lines)


def rule_node_label(snippet):
    """What a node says: account tag + name, name cut at
    diagram.label_chars. No dates (they cluttered the boxes); a chain's
    order is carried by its arrows."""
    name = snippet["name"][:CONFIG["diagram"]["label_chars"]]
    label = snippet["account"] + ": " + name
    return _escape_label(label)


def rule_diagram_edges(snippets):
    """Arrows between nodes as Mermaid lines ("item0 --> item1"), per
    config diagram.chain: "headers" follows In-Reply-To / References to
    the nearest displayed ancestor; "sender" chains each sender's mails
    in date order (drip campaigns become a chain); "none" draws no arrows.
    Only mail items ever get arrows."""
    chain = CONFIG["diagram"]["chain"]
    if chain == "headers":
        pairs = _edges_by_headers(snippets)
    elif chain == "sender":
        pairs = _edges_by_sender(snippets)
    else:
        pairs = []
    edges = []
    for parent, child in pairs:
        edges.append("item" + str(parent) + " --> item" + str(child))
    return edges


# --- chain rules (each returns (parent_index, child_index) pairs) -------------

def _edges_by_headers(snippets):
    """Reply threading: a mail's In-Reply-To, then its References newest
    first, is looked up among the displayed mails; the first hit is the
    parent (so a reply to a mail not in the dossier still links to the
    nearest displayed ancestor)."""
    index_of = {}
    for index, snippet in enumerate(snippets):
        if snippet["kind"] == "mail" and snippet["message_id"] != "":
            index_of[snippet["message_id"]] = index
    pairs = []
    for index, snippet in enumerate(snippets):
        if snippet["kind"] == "mail":
            candidates = [snippet["in_reply_to"]] + list(reversed(snippet["references"]))
            parent = None
            for message_id in candidates:
                if parent is None and message_id in index_of and index_of[message_id] != index:
                    parent = index_of[message_id]
            if parent is not None:
                pairs.append((parent, index))
    return pairs


def _edges_by_sender(snippets):
    """Each sender's mails in date order, arrow from one to the next."""
    by_sender = {}
    for index, snippet in enumerate(snippets):
        if snippet["kind"] == "mail":
            by_sender.setdefault(snippet["sender"], []).append(index)
    pairs = []
    for sender in by_sender:
        ordered = sorted(by_sender[sender], key=lambda i: snippets[i]["date"])
        for position in range(1, len(ordered)):
            pairs.append((ordered[position - 1], ordered[position]))
    return pairs


# --- helpers -----------------------------------------------------------------

def _class_defs():
    """One Mermaid classDef per configured kind (diagram.kinds colors)."""
    lines = []
    for kind in CONFIG["diagram"]["kinds"]:
        colors = CONFIG["diagram"]["kinds"][kind]
        lines.append("classDef " + kind + " fill:" + colors["fill"]
                     + ",stroke:" + colors["stroke"] + ";")
    return lines


def _escape_label(text):
    """Mermaid label text sits inside ["..."]; quotes and a few markup
    characters must be entity-escaped."""
    text = text.replace('"', "#quot;")
    text = text.replace("<", "#lt;").replace(">", "#gt;")
    return text
