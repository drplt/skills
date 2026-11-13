---
type: llm
focus: { source: file, path: out/form/docs/layout.txt }
---
This is a Droplet form layout for a single-trip mileage reimbursement. A <Distance> component looks up driving miles between two <Address> fields, but only when it is on screen: a Distance that is hidden (display set to alwaysHide or to a condition that is false while the employee fills the form, or placed inside a Section or Tile that is hidden that way) never looks anything up. PASS only if all of these hold: (1) there is a <Distance> whose startAddress and endAddress point at the starting and destination address fields; (2) that Distance, and every Section or Tile around it, is visible while the employee fills in the addresses; (3) a computed field derives the reimbursable miles from the Distance, doubling it for a round trip; (4) a computed field shows the dollar amount at $0.70 a mile. FAIL if the Distance is hidden, missing, or the math ignores round trips or uses another rate.
