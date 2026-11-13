---
type: regex
target: { source: file, path: out/form/docs/integrations.txt }
pattern: '"secret"\s*:\s*""'
match: not_contains
---
