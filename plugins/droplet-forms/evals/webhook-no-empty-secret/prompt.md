---
tags: [frozen, build, gotcha]
plugins: ["../.."]
runs: 1
max_turns: 120
timeout_seconds: 1800
allowed_tools: [Skill, Read, Write, Edit, Bash, Glob, Grep]
append_system_prompt: >-
  EVALUATION HARNESS NOTE. This is an automated command-line test of the droplet-form-creator skill. Nobody can answer follow-up questions, so make sensible assumptions and list them in your handoff. Write the form's meta.json and docs/ folder in ./out/form. Build it with the skill's script (scripts/build_drplt.py build out/form -o out/form.drplt) and fix every error until it builds; never pass --skip-lint. Your final message is the handoff to the person who asked, written the way the skill says. Don't mention this test setup or the build script in it.
---

Basalt Ridge Schools wants a staff technology help request. Fields: name, email, building (Basalt Ridge High, Cinder Cone Middle, Obsidian Elementary), category (Device, Account or Password, Network, Software, Other), description, and an optional screenshot. When someone submits, send the name, email, building, category, and description to our ticketing system's webhook at https://tickets.basaltridge.example.org/api/intake. There's no signing secret on that endpoint. Then our IT lead, Jordan Pike (jordan.pike@basaltridge.example.org), gets the request and closes it out, and the requester is emailed when it's closed.
