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

Alder Springs SD needs a new student enrollment form for parents. Student name, date of birth, parent or guardian name, phone, email, home address, and the grade they're enrolling in. The grade dropdown should show "Transitional Kindergarten", "Kindergarten", "Grade 1" through "Grade 12", but it has to save the short codes TK, K, and 1 through 12, because our student information system import only takes codes. If the grade is TK or Kindergarten, also show a few kindergarten readiness questions (attended preschool yes/no, any speech or language concerns, notes). The registrar, Mei Lin (mei.lin@aldersprings.example.org), reviews it, and the parent gets an email when it's accepted.
