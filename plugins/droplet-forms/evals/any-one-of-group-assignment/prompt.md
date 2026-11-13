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

Thistle Bend SD wants a staff absence request. Employee name and email, building (Thistle Bend High, Heather Glen Middle, Moorside Elementary), position, absence start date, end date, reason (Sick, Personal, Bereavement, Professional Development, Jury Duty), whether a substitute is needed, and notes for the sub. Any one of our three HR assistants can process it, whoever picks it up first: Kira Moss (kira.moss@thistlebend.example.org), Leo Grant (leo.grant@thistlebend.example.org), and Maya Singh (maya.singh@thistlebend.example.org). They just confirm it's entered in the payroll system. Email the employee when it's processed.
