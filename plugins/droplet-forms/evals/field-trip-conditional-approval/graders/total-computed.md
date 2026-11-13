---
type: llm
focus: { source: file, path: out/form/docs/layout.txt }
---
This is a Droplet form layout for a field trip request. PASS only if the total trip cost is a <Computed> field whose formula multiplies the number of students by the cost per student (converting to numbers if the inputs could be text), and the overnight and out-of-state answers are captured as fields. FAIL if the total is a typed input.
