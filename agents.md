# WHO I AM
I am a software developer with over 15 years experience. Most of my experience on the backend and infrastructure. I have less experience in frontend technologies.
I am the driver of requirements.

# WHO YOU ARE
You are my coding assistant. At times I will be asking for your opinion on tech decisions. At times you will be focused on coding.

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

## NOTES
The notes folder is just for my personal notes. Do not refer to this at all. This is just brainstormed ideas that may contradict/get stale from what is being developed.
