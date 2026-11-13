---
type: llm
focus: { source: file, path: out/form/docs/layout.txt }
---
This is a Droplet form layout. In Droplet, a static options array can hold single-pair objects such as { TK: "Transitional Kindergarten" }, where the key is the stored value and the text is what the parent sees. Objects shaped { label, value } are rejected on import. PASS only if: (1) the grade field stores TK, K, and 1 through 12 while showing Transitional Kindergarten, Kindergarten, and Grade 1 through Grade 12, using single-pair objects (not { label, value }); and (2) the kindergarten readiness questions show only when the stored grade is TK or K. A conditions object with two or more conditions must also set operator ("and" or "or"); a missing operator is a FAIL. FAIL if the dropdown stores the long names, or the readiness questions show for every grade.
