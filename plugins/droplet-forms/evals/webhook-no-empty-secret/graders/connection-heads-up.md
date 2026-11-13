---
type: llm
focus: last_message
---
This is the handoff for a help request form that sends data to a webhook. The webhook's connection only exists in the customer's Droplet workspace, so a generated form carries a placeholder connection, and the step that sends the data will fail until someone picks or creates the real connection in the Droplet editor. PASS only if the message tells the user, in plain words, that they must set up or select the webhook connection in Droplet before the form goes live. FAIL if it implies the webhook will work as soon as the form is imported.
