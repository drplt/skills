---
type: regex
target: last_message
pattern: 'build_drplt|\bpython3?\b|\blint(?:er|ed|ing)?\b|--skip-lint|\bsandbox|harness|\beval(?:uation)?\b|nameElementId|emailElementId|\bonEnter\b|\bonSubmit\b|\bonReject\b'
flags: i
match: not_contains
---
