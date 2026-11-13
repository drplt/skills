---
type: llm
focus: last_message
---
This is the handoff after changing a form that is already live in Droplet. A Droplet import always creates a brand new form with a new link and cannot overwrite the live one, so the right way to apply changes is to open the existing form in the Droplet editor and paste each changed module (layout, workflow, steps, notifications, in that order) into its matching code view. PASS only if the message (1) tells the user to update the existing form by pasting the changed modules into its editor, (2) lists which modules changed, and (3) does not tell them to import the new file to update or replace the live form. Mentioning that the rebuilt file is only for a fresh copy is fine. FAIL if it tells them to import or re-import to apply the changes, or gives no module list.
