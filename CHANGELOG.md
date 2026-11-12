# Changelog

## [1.0.4] - 2026-11-12
- Group assignment: a step's assign can be a list of up to 8 people, rules, or expressions, and the first to act completes the step. Use a parallel step when everyone must act. The linter checks each entry and errors past 8 assignees.

## [1.0.3] - 2026-11-11
- A hidden Distance never looks up miles. Keep every Distance visible and editable where addresses are entered, and show round trip or reimbursable miles in Computeds beside it. The linter now errors on an always-hidden Distance or one hidden on start.

## [1.0.2] - 2026-09-24
- A .drplt import cannot overwrite an existing form. Revisions to a form already in Droplet are pasted module by module into the editor (layout, workflow, steps, notifications), and the handoff now lists which modules changed.

## [1.0.1] - 2026-09-16
- Element ids cannot be reserved email template keys. An Identifier named formId fails import; use referenceId or requestId. The linter now errors on formId and warns on other template variable names.

## [1.0.0] - 2026-09-14
- First public release: SKILL.md with the build process and hard rules, six references, eight exemplar forms, and the build, lint, and extract script.
