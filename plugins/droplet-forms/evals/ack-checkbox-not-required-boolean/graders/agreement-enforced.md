---
type: llm
focus: { source: file, path: out/form/docs/layout.txt }
---
This is a Droplet form layout for an acceptable use agreement. Droplet's <Boolean> toggle does not accept a "required" prop; a Boolean is made mandatory with a validate rule that only passes when it is checked. A <Checkbox> with one option is required by default unless it says required={false}. PASS only if the "I have read and agree" box blocks submission until it is ticked, using either a Boolean with such a validate rule or a single-option Checkbox that is required. FAIL if the box can be left unticked, or if a Boolean carries a required prop.
