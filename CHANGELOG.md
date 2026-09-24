# Changelog

## [1.0.2] - 2026-09-24
- A .drplt import cannot overwrite an existing form. Revisions to a form already in Droplet are pasted module by module into the editor (layout, workflow, steps, notifications), and the handoff now lists which modules changed.

## [1.0.1] - 2026-09-16
- Element ids cannot be reserved email template keys. An Identifier named formId fails import; use referenceId or requestId. The linter now errors on formId and warns on other template variable names.

## [1.0.0] - 2026-09-14
- First public release: SKILL.md with the build process and hard rules, six references, eight exemplar forms, and the build, lint, and extract script.
