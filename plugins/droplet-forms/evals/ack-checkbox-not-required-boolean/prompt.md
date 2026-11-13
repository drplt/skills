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

Willow Ridge Schools wants every staff member to sign the technology acceptable use agreement each fall. Fields: name, email, building (Willow Ridge High, Birchwood Middle, Fern Hollow Elementary), role (Teacher, Support Staff, Administrator, Substitute). Show a short paragraph summarizing the policy, then they have to tick a box that says "I have read and agree to the Acceptable Use Policy" and they can't submit without ticking it. Then a signature and the date. No approval needed: it just completes and emails them a copy.
