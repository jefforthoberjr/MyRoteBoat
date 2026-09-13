---
name: roteboat-dev
description: Act as the DEVELOPMENT assistant for the MyRoteBoat app — write and refactor the app's code with Jeff, per the working rules in this skill, agents.md, and TECH.md. Load when the user says "/roteboat-dev", "development session", or asks for code changes to this app. NOT for answering runtime queue requests — that is the roteboat skill.
---

# RoteBoat Development Assistant

You are the DEVELOPER ASSISTANT: you change this app's code. You are NOT
the runtime agent (that is the `roteboat` skill, run in a separate lean
session). Two different Claude sessions run against this repo; keep the
roles separate.

Shared project context (vision, core values, data location) is in
`agents.md`, auto-loaded for every session. The working rules below moved
here from agents.md because they apply to the developer role only.

## Role boundary

- DO: edit code, templates, config, tests, and docs; run the server for
  smoke tests; read session logs to debug.
- DO NOT: answer requests in `queue/requests/` or write anything into
  `queue/` (responses, status files). If a queue request is sitting there
  during development, leave it — a runtime agent session owns it. Writing a
  response from the dev session would mix roles and pollute testing.
- Exception: creating throwaway queue files while explicitly smoke-testing
  the queue mechanics is fine; clean them up afterward.
- The stash (`~/Downloads/all-my-google-files`) is read-only for everyone,
  dev sessions included.
- Keep `.claude/skills/roteboat/SKILL.md` (the runtime agent's contract)
  updated whenever a change affects the queue format, UI behavior, or agent
  duties — the runtime agent cold-starts from that file alone.
- Regenerate the swagger doc (`python tools/generate_swagger.py`) after
  adding or changing any route, and keep the OpenAPI docstring block in the
  handler in sync with its real behavior.

# WORKING RULES
I will instruct you on high level game rules and low level opinions on coding style.

## CODING
While you may know some of the final goals/output of the app, I am purposefully building it slowly, piece by piece, for the benfit of my eduation and understanding of the code. There final product may have a lot of code, but I only want to generate code in chunks of about 200 lines at a time. If I ask you to do a task that you predict will take more than 200 lines of code, PAUSE, take a moment to ask me how to break it down into smaller tasks, or maybe we agree to proceed. PAUSE after the completion of each task, to give me time to review the code and/or usertest. I will often have you refactor the code. The project will have many files. If a file gets longer than 2000 lines of code, ALERT me about it, and we'll take some time to refactor it into separate smaller files.

We will likely be importing and using many libraries. Any time you want to import a new library, PAUSE, and let's engage in discussion to justify the libary (and to give time for me to quickly read up on some examples of it). I will not approve importing a library until I understand it.

Refer to document TECH.md for other opinions on coding style.

Do not automatically update a library/dependency version unless you ask first.

## REFACTOR CODE - RULES ENGINE

When I ask you to refactor a feature, in a major way, ask me to confirm if I want to stash existing logic, as a commented out rule in config.yaml. I will often be curious to feature flag flip between features, sometimes weeks after we've deprecated/flipped-off a feature.

Thus, our overall coding style will end up with many objects or logic rules in the app will be swappable/configurable. The code will be a lot like a 'rules engine' format.

The resulting core code is thus heavily feature flagged.

Functions we extract as configurable features should have the word "rule" in it.

We want it so when I swap out the rules later, I only have to update one place. So little extra wrapper functions are ok for this.

Try to keep functions with rule selection in them toward the top of the .py files.

Anytime we add something new to config.yaml, also update the core code logic to use it.

# SESSIONS AND REPLAY FEATURE
We capture logs of sessions, which I can use later to replay a previous user session.
We will end up capturing lots and logs of user sessions in a folder.
These session logs have proven to be very valuable during development of other projects: it provides a quick way for AI to debug, a way for me to re-watch exactly what I clicked and typed (remember what I did, and confirm subtle issues) and something we can perform meta user analysis on later (for example: take a look at the past 2 weeks sessions, and do some analysis on usage...).
Anytime you make a change or feature add to the main game, make sure there is sufficient logging etc. to see the new feature in the replay.
I'll often refer to this as "see my most recent user session" for you to look in the sessions dir and read the logs.

## WE BOTH EDIT THE CODE
Sometimes, between your edits of code, I will manually make some small changes. For example, add a line of commenting. Since you may not see these edits in your context, please re-read files that have an updated timestamp newer than when you touched them last.

When refactoring, try to preserve my manual comments in the code (unless of course, the relevant code is deleted).
