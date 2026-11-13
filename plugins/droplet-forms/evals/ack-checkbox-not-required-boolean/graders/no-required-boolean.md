---
type: regex
target: { source: file, path: out/form/docs/layout.txt }
pattern: '<Boolean\b(?:(?!/>)[\s\S])*?\brequired\b'
match: not_contains
---
