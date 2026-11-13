---
type: llm
focus: { source: file, path: out/form/docs/layout.txt }
---
This is a Droplet form layout for a purchase request with a line items table. PASS only if each row's line total is a formula column (quantity times unit price) and the grand total is a computed field built from the rows (a sum of the line totals or of quantity times unit price), not a typed input. FAIL otherwise.
