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

Cobalt Creek USD needs a transcript request form for former students: name at graduation, current name, date of birth, graduation year, school (Cobalt Creek High School or Ridgeline Continuation High School), where to send it (email or mailing address), and how many copies. Any one of our nine registrars can process a request, whoever gets to it first:
- Ana Ruiz, ana.ruiz@cobaltcreek.example.org
- Ben Carter, ben.carter@cobaltcreek.example.org
- Chloe Park, chloe.park@cobaltcreek.example.org
- David Osei, david.osei@cobaltcreek.example.org
- Elena Novak, elena.novak@cobaltcreek.example.org
- Farah Haddad, farah.haddad@cobaltcreek.example.org
- Grant Tully, grant.tully@cobaltcreek.example.org
- Hana Mori, hana.mori@cobaltcreek.example.org
- Isaac Brandt, isaac.brandt@cobaltcreek.example.org
Once it's processed, email the requester that it was sent.
