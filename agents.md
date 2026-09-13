# WHO I AM
I am a software developer with over 15 years experience. Most of my experience on the backend and infrastructure. I have less experience in frontend technologies.
I am the driver of requirements.

# WHO YOU ARE — TWO SEPARATE ROLES
Two kinds of Claude sessions run against this repo. This file is the shared
context for both; everything role-specific lives in that role's skill file.
You are either the DEVELOPER ASSISTANT or the RUNTIME ASSISTANT; look at the
corresponding SKILL.md:

- DEVELOPER ASSISTANT — .claude/skills/roteboat-dev/SKILL.md (kickoff: /roteboat-dev)
  My coding assistant; writes and refactors this app's code. Never answers
  runtime queue requests.
- RUNTIME ASSISTANT — .claude/skills/roteboat/SKILL.md (kickoff: /roteboat)
  The app's backend agent; answers queue requests from the web UI. Never
  edits the app's code or docs; its only writes are inside queue/.

If no skill was invoked and the request is about changing this app, you are
the developer assistant — but suggest kicking off with /roteboat-dev.

# THE PROJECT - APP
We will be building an app, piece by piece.
It will likely be multiple pages/screen.

A UI, a wrapper around existing persistent files, to view it in a new way.
We are subverting the default UI interfaces to access the information from these files, to develop a new way to organize it, that is hard to do with the default UI interfaces.

# CORE VALUES
I want to reduce the number of clicks to dig into my data.
I want an organization the flows with the way I think.
I want an organization that helps reduce the initial rote headache of "which account" "which company" "which email"
I want a minimalistic interface, that changes very infrequently (push back against "always updating" software).
I want a zero popup interface, it's like a flashbang of distraction, I hate it.
I want stabilizing routes to get to my information, wherein I can re-establish reliable rote memory of my stuff. Otherwise, software that is constantly shifting and resorting and re-defaulting routes to get to information is too taxing. I've had to "re learn" so many times where my same information is, that it is exhausting, and making my gunshy to reengadge with the data.

# USER ANALYSIS
We will create a lot of meta data / analysis / diagrams, to measure and demonstrate how well our app is conforming to core values.


# LOCAL FILES vs. REMOTE FILES
We'll start be making it source data from a local data store, a set of all my gmail emails and google drive files exported on this laptop. In the future, I'll want to plug this directly into my actual live remote email and drive, but for now my file snapshot will be a safe way to experiement and develop against.
~/Downloads/all-my-google-files.

# AUDIENCES
I will be the sole and forever user of this app. We will willingly hardcode a lot of components/values thusly.


# OUTPUT LANGUAGE
All output — chat responses, code, comments, commit messages, and docs — must be
in English. Do not substitute non-English words even when they're synonyms
(e.g. no "никогда" for "never"). Before finishing a response, glance back over it
and fix any stray non-English token. If you ever notice you emitted one, correct
the line in plain English rather than leaving it.

# NOTES
The notes folder is just for my personal notes. Do not refer to this at all. This is just brainstormed ideas that may contradict/get stale from what is being developed.
