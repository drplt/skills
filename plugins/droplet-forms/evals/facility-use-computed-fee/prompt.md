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

Marigold Lake SD rents out school spaces after hours. We need a facility use request: organization name, contact name, email, and phone, whether they're a nonprofit (Yes/No), building (Marigold Lake High School or Lakeview Middle School), space (Gym $50 an hour, Cafeteria $40 an hour, Auditorium $75 an hour, Classroom $20 an hour), event date, start time, end time, and expected attendance. Show an estimated fee: hours times the hourly rate, with nonprofits getting 50% off. Put a button near the top that opens our facility use policy at https://www.marigoldlake.example.org/facilities-policy.

The building principal approves first (Marigold Lake High: Ruth Okafor, ruth.okafor@marigoldlake.example.org; Lakeview Middle: Paul Jensen, paul.jensen@marigoldlake.example.org), then the Facilities Director, Sam Ito (sam.ito@marigoldlake.example.org), gives final approval. A denial ends it. Email the requester the decision.
