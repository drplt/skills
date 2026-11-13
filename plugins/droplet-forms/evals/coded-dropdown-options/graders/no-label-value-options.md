---
type: regex
target: { source: file, path: out/form/docs/layout.txt }
pattern: '\{\s*["'']?label["'']?\s*:'
match: not_contains
---
