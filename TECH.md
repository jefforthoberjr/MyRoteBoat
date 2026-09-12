
# TECH STACK and DEV OPS
We are using python3.

We are using the "C" version of python (i.e. not Java or .Net)

I am editing in vscode, with minimal plugins

We are using venv and pip to manage libs/dependencies.
Example commands:
`python3.12 -m venv venv`

`source venv/bin/activate`
`pip install -r requirements.txt`
`pipreqs ./src`

We are keeping the set of local build commands very simple. We are only doing local development, with minimum distributed components.

`python ./src/main.py`

I am storing everything in a git repo. DO NOT add/commit with git. I am in charge of adding and commiting. I will be committing often.

I have unit tests.
`pytest`
`pytest tests/test_main.py`


# WEB STACK
We are using Flask (decided 2026-09-12) as the local web server: minimal,
stable, boring — fits the "changes infrequently" core value. Localhost only,
single user, no auth.

Frontend is plain HTML/CSS/JS served by Flask. No frontend framework unless we
later decide otherwise (each new library requires discussion first, per
agents.md).

Flask routes are registered with `app.add_url_rule(...)` instead of the
`@app.route` decorator, to honor the "avoid decorators" python style rule below.


# PYTHON STYLE
Avoid python decorators. No need for the syntax sugar.

Avoid multiple return statements in a function. This will make embedding wrappers more easily during future refactors.

Prefer clear multiline loops over "list comprehension"

Avoid "//" operator, use math.floor instead

Avoid formal polymorphism typing; just use duck typing

Avoid raw pixel math; instead things should be relative to screen size.


# CONFIG REFERENCE
src/assets/config.yaml is the single edit point for tuning, kept scannable: a
flat wall of keys, the commented-out toggle alternatives, and a terse one-line
label per knob. The FULL prose for every knob lives in CONFIG_REFERENCE.md,
keyed by the same dotted name — search that file for a key to get the details.

When you add or change a rule: put the short label in config.yaml and the
explanation in CONFIG_REFERENCE.md under a matching heading. Do NOT grow
multi-paragraph comments back into config.yaml.


# TECH DECISIONS LOG
A running list of decisions as we make them, newest last. One line each; the
prose (if needed) goes in the relevant section above.

- 2026-09-12: Flask chosen as web server (over stdlib http.server).
- 2026-09-12: Claude Code session (subscription) is the LLM agent; no direct
  pay-per-token API calls. Requests flow through a file queue — see
  .claude/skills/roteboat/SKILL.md.
