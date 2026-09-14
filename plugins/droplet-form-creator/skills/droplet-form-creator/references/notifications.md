# Notifications

`docs/notifications.txt` maps step ids to the emails sent when a submission enters (or leaves) that step.

## Structure

```json
{
  "principalApproval": {
    "onEnter": { ...one notification... }
  },
  "completed": {
    "onEnter": [ ...several notifications... ]
  },
  "start": {
    "onExit": { ...sent when the submitter submits... }
  }
}
```

Events: `onEnter` (most common) and `onExit`. Each holds one notification object or an array of them.

## Notification object

```json
{
  "type": "assignment",
  "template": { "subject": "...", "body": "<p>...</p>" },
  "recipients": [ ... ],
  "sendToSubmitter": true,
  "if": "expression or conditions object",
  "attachSubmissionPdf": true,
  "hidden": ["internalNotes", "sectionReviewerOnly"],
  "id": "customerReminder"
}
```

`template` contains only `subject` and `body`. Everything else sits beside it. Putting `sendToSubmitter` inside `template` fails import with `unrecognized key`.

### Types

- `"type": "assignment"`: goes to the person assigned at this step. Link with `##assignmentUrl##`.
- `"type": "remind"`: a scheduled reminder referenced from the step's `scheduledActions` by `id`. Goes to the assignee. Link with `##submissionUrl##` (the validator rejects `##assignmentUrl##` here).
- No `type`: an informational email to `recipients` and/or the submitter. Link with `##submissionUrl##`.

### Recipients shapes

```json
"recipients": [{ "type": "static", "name": "Business Office", "email": "business@district.org" }]
"recipients": ["business@district.org", "payroll@district.org"]
"recipients": [{ "nameElementId": "customerName", "emailElementId": "customerEmail" }]
"recipients": "[principalEmail]"
"recipients": "[principalEmail, secretaryEmail].filter(Boolean)"
```

The expression string form resolves field ids to email strings, so a dedicated `<role>Email` computed drops straight in. Do not build `{ name, email }` object literals inside an expression.

### Submitter

```json
{ "template": { ... }, "sendToSubmitter": true }
{ "template": { ... }, "sendToSubmitter": true, "recipients": ["cc@district.org"] }
```

### Conditional

```json
{ "template": { ... }, "recipients": [ ... ], "if": "isGreaterThan(parseFloat(totalCost), 5000)" }
{ "template": { ... }, "sendToSubmitter": true, "if": "isBlank(_reason)" }
```

### Several on one step

```json
"onEnter": [
  { "template": { ... }, "recipients": [{ "type": "static", "name": "Director", "email": "director@district.org" }], "if": "isGreaterThan(parseFloat(totalCost), 5000)" },
  { "type": "assignment", "template": { ... } }
]
```

### Attachments and hidden fields

`"attachSubmissionPdf": true` attaches the submission PDF. `"hidden": [...]` lists element ids (fields and sections) that the view reached through this notification's link will not show. Use it to keep internal notes away from external recipients while staff can still read them in the dashboard.

## Template variables

| Variable | Value |
|---|---|
| `##recipientFirstName##` | Recipient's first name |
| `##initiatedByFullName##` | Person who started the submission |
| `##submittedByName##` | The submitter name field |
| `##submissionUrl##` | Read-only link to the submission |
| `##assignmentUrl##` | Link to act on the assignment (assignment emails only) |
| `##_reason##` | The reject or send-back reason |
| `##fieldId##` | Any field value; `##table.0.column##` for a cell |

Never `###fieldId##`.

## Email HTML

Bodies are single-line HTML strings inside JSON, so use single quotes for HTML attributes. Table-based markup renders consistently across mail clients:

```html
<table width='100%' border='0' cellspacing='0' cellpadding='0' align='center' style='max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px;'><tr><td align='center' style='padding-bottom: 20px;'><img src='LOGO_URL' alt='Logo' style='display: block; min-width: 200px; max-width: 40%; height: auto;'></td></tr><tr><td align='center' style='padding-bottom: 20px;'><h1 style='font-size: 26px; color: #203E7C; font-weight: bold; margin: 0; font-family: sans-serif;'>Field Trip Request</h1></td></tr><tr><td align='center' style='padding-bottom: 20px;'><table width='100%' border='0' cellspacing='0' cellpadding='20' style='border: 1px solid #e0e0e0; border-radius: 10px; background-color: #f9f9f9;'><tr><td align='left'><p style='font-size: 16px; color: #555555; line-height: 1.5; margin: 0; font-family: sans-serif;'>Hi ##recipientFirstName##, ##submittedByName## submitted a field trip request for ##tripDate##.<br /><br /><b>School:</b> ##school##<br /><b>Destination:</b> ##destination##<br /><b>Students:</b> ##studentCount##</p></td></tr></table></td></tr><tr><td align='center'><a href='##assignmentUrl##' style='display: inline-block; padding: 10px 20px; font-size: 16px; color: #ffffff; background-color: #203E7C; border-radius: 5px; text-decoration: none; font-family: sans-serif;'>Review Request</a></td></tr></table>
```

Inline styles are fine in email HTML (this is not a `<Text>` component). Keep the logo as a placeholder URL for the customer to replace.

## Typical set for an approval form

| Step | Event | Who | Purpose |
|---|---|---|---|
| `start` | `onExit` | submitter | "We received your request" (guard with `"if": "isBlank(_reason)"` so re-submits after send-back do not repeat it) |
| each approval step | `onEnter` | assignment | "A request needs your approval" with `##assignmentUrl##` |
| `completed` | `onEnter` | submitter plus any office that acts on the result | "Approved" with `##submissionUrl##`, often `attachSubmissionPdf` |
| `rejected` | `onEnter` | submitter | "Not approved" with `##_reason##` |
