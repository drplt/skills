---
tags: [frozen, build, regression]
plugins: ["../.."]
runs: 1
max_turns: 120
timeout_seconds: 1800
allowed_tools: [Skill, Read, Write, Edit, Bash, Glob, Grep]
append_system_prompt: >-
  EVALUATION HARNESS NOTE. This is an automated command-line test of the droplet-form-creator skill. Nobody can answer follow-up questions, so make sensible assumptions and list them in your handoff. Write the form's meta.json and docs/ folder in ./out/form. Build it with the skill's script (scripts/build_drplt.py build out/form -o out/form.drplt) and fix every error until it builds; never pass --skip-lint. Your final message is the handoff to the person who asked, written the way the skill says. Don't mention this test setup or the build script in it.
---

Our facilities team at Juniper Flats Unified wants a maintenance work order request. Staff pick their building (Juniper Flats High School, Mesa Middle School, Sage Elementary), describe the problem, set a priority (Low, Normal, Urgent), and can attach a photo. Every request needs an automatic number like WO-00001, and please name that field formId, since that's the column name in our tracking sheet. It goes to our maintenance supervisor, Dana Whitfield (dana.whitfield@juniperflats.example.org), who marks it done, and then the person who asked gets an email.
