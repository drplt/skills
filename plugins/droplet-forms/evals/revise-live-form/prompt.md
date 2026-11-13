---
tags: [frozen, build, regression, revision]
plugins: ["../.."]
runs: 1
max_turns: 120
timeout_seconds: 1800
allowed_tools: [Skill, Read, Write, Edit, Bash, Glob, Grep]
append_system_prompt: >-
  EVALUATION HARNESS NOTE. This is an automated command-line test of the droplet-form-creator skill. Nobody can answer follow-up questions, so make sensible assumptions and list them in your handoff. Extract the exported form into ./out/form (meta.json and docs/ directly inside it) and make the changes there. Build it with the skill's script (scripts/build_drplt.py build out/form -o out/form.drplt) and fix every error until it builds; never pass --skip-lint. Your final message is the handoff to the person who asked, written the way the skill says. Don't mention this test setup or the build script in it.
---

Our Field Trip Request is already live in Droplet and teachers are using it. I exported it for you: inbox/Field Trip Request.drplt. Two changes please:
1. Add a required "Number of chaperones" field next to the number of students.
2. When "Bus needed" is Yes, send it to our Transportation Coordinator, Luis Ferreira (luis.ferreira@harborpoint.example.org), after the principal approves, so he can book the bus. When it's No, it should finish after the principal like it does now.
