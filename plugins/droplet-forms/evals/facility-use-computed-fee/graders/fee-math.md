---
type: llm
focus: { source: file, path: out/form/docs/layout.txt }
---
This is a Droplet form layout for a facility rental request. PASS only if the estimated fee is a computed field that multiplies the hours (from the start and end times, or an hours field) by the rate for the chosen space (Gym $50, Cafeteria $40, Auditorium $75, Classroom $20 an hour) and takes 50% off when the organization is a nonprofit. Also require a button or link to https://www.marigoldlake.example.org/facilities-policy. FAIL if the fee is a typed input, uses wrong rates, or ignores the nonprofit discount.
