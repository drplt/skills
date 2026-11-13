---
type: regex
target: { source: file, path: out/form/docs/layout.txt }
pattern: '<Distance\b(?:(?!/>)[\s\S])*?(?:alwaysHide|display\s*=\s*"false")'
match: not_contains
---
