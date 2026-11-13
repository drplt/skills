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

Larkspur Valley SD needs a form for teachers to request an individual student support plan review. The teacher enters the student's name, student ID, grade, school (Larkspur Elementary, Valley Oak Middle, Larkspur Valley High), the concern, and any attachments. Three people must each sign off separately, and they can all work on it at the same time: the school nurse, Priya Natarajan (priya.natarajan@larkspurvalley.example.org), the counselor, Owen Hale (owen.hale@larkspurvalley.example.org), and the assistant principal, Rosa Delgado (rosa.delgado@larkspurvalley.example.org). Each one adds their own notes and signature. Once all three are done, email the teacher.
