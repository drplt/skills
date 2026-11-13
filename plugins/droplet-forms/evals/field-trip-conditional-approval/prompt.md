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

Cypress Hollow USD needs a field trip request form. The teacher enters their school (Cypress Hollow Elementary, Cypress Hollow Middle, Cypress Hollow High), grade, destination, trip date, departure and return times, number of students, number of chaperones, transportation (District bus, Walking, Parent drivers), whether it's overnight, whether it's out of state, and the cost per student. Show the total trip cost (students times cost per student).

Routing: the school's principal always approves first.
- Cypress Hollow Elementary: Nora Vance, nora.vance@cypresshollow.example.org
- Cypress Hollow Middle: Victor Lam, victor.lam@cypresshollow.example.org
- Cypress Hollow High: Imani Brooks, imani.brooks@cypresshollow.example.org
If the trip is overnight or out of state, the Assistant Superintendent, Helena Price (helena.price@cypresshollow.example.org), approves next. If they're taking a district bus, Transportation (transportation@cypresshollow.example.org) schedules it last. If anyone denies it, it stops there. Email the teacher the result either way.
