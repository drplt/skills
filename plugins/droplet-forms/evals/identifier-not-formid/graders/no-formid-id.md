---
type: regex
target: { source: file, path: out/form/docs/layout.txt }
pattern: '\bid\s*=\s*\{?\s*["'']formId["'']'
match: not_contains
---
