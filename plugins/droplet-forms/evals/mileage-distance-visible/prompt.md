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

Osprey Bay Schools needs a mileage reimbursement form, one trip per request. The employee enters the date, the purpose, a starting address, and a destination address, and says whether it was a round trip. Droplet should work out the miles from the addresses (double them for a round trip) and pay $0.70 a mile, so they see the dollar amount before they submit. Their supervisor approves (the employee types the supervisor's name and email), then Payroll at payroll@ospreybay.example.org processes it. Tell the employee when it's paid or if it's denied.
