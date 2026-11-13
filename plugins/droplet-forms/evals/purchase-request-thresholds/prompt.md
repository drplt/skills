---
tags: [frozen, build, everyday]
plugins: ["../.."]
runs: 1
max_turns: 120
timeout_seconds: 1800
allowed_tools: [Skill, Read, Write, Edit, Bash, Glob, Grep]
append_system_prompt: >-
  EVALUATION HARNESS NOTE. This is an automated command-line test of the droplet-form-creator skill. Nobody can answer follow-up questions, so make sensible assumptions and list them in your handoff. Write the form's meta.json and docs/ folder in ./out/form. Build it with the skill's script (scripts/build_drplt.py build out/form -o out/form.drplt) and fix every error until it builds; never pass --skip-lint. Your final message is the handoff to the person who asked, written the way the skill says. Don't mention this test setup or the build script in it.
---

Granite Pass SD needs a purchase request. Requester name and email, department (Curriculum, Technology, Facilities, Athletics, Special Education), vendor name, and a line items table with description, quantity, unit price, and line total. Show a grand total at the bottom.

Approvals: the Business Office, Theo Marsh (theo.marsh@granitepass.example.org), reviews every request. Over $5,000, the Assistant Superintendent of Business, Carla Nunez (carla.nunez@granitepass.example.org), approves next. Over $25,000, the Superintendent, Dr. Alan Reyes (alan.reyes@granitepass.example.org), approves after her. A denial anywhere ends it. Email the requester when it's approved or denied.
