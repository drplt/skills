# Workflow and permissions

`docs/workflow.txt` defines the steps a submission moves through. `docs/steps.txt` defines what each step can see and edit.

## Workflow structure

```json
{
  "test": {},
  "steps": {
    "start": { ... },
    "principalApproval": { ... },
    "completed": { ... },
    "rejected": { ... }
  }
}
```

Reserved step ids:

- `start`: where the form is first filled out. No `status` property.
- `completed`: terminal success. `{ "status": "completed", "position": [...] }`.
- `rejected`: terminal rejection. Include it only when a route targets it.

Custom step ids are descriptive camelCase: `supervisorApproval`, `businessOfficeReview`, `parentSignature`.

## Step properties

```json
"principalApproval": {
  "status": "pending",
  "label": "Principal Approval",
  "position": [560, 80],
  "onEnter": { ... },
  "onSubmit": [ ... ],
  "onReject": [ ... ]
}
```

- `status`: `pending` for working steps, `completed` or `rejected` for terminal steps.
- `label`: shown in the workflow editor and to users.
- `position`: `[x, y]` in the visual editor. Space steps about 400 px apart horizontally.

## onEnter

### Return to the submitter

```json
"onEnter": { "sendToSubmitter": true }
```

### Dynamic assignee (preferred)

Two `<Computed>` fields per role, one returning the name string and one the email string. The visual editor renders this pair as a labeled Name and Email on the step card, so a builder can see who the step routes to without reading formulas.

```json
"onEnter": {
  "assign": { "nameElementId": "principalName", "emailElementId": "principalEmail" }
}
```

```jsx
<Computed id="principalName" label="Principal Name" columns={3}
  formula="(()=>{ if (!school) return ''; const r = schools[school]; return r && r['principal'] ? r['principal']['name'] : ''; })()" />
<Computed id="principalEmail" label="Principal Email" columns={3}
  formula="(()=>{ if (!school) return ''; const r = schools[school]; return r && r['principal'] ? r['principal']['email'] : ''; })()" />
```

Both computeds are `readonly` in `steps.txt`. Name the pair after the role, not the routing. The email computed also drops straight into notifications as `"recipients": "[principalEmail]"`.

### Static assignee

```json
"onEnter": { "assign": { "name": "Transportation Office", "email": "transportation@district.org" } }
```

For a fixed person or shared mailbox that never varies by submission.

### Legacy single computed returning `{ name, email }`

```json
"onEnter": { "assign": "approverAssignment" }
"onEnter": { "assign": "buildings[building].facilityContact" }
```

The string is a field id or an expression that returns `{ name, email }`. Still valid but renders poorly in the editor. Do not use for new forms; migrate when editing old ones.

### Conditional entry (skip the step)

```json
"onEnter": {
  "assign": { "nameElementId": "grantApproverName", "emailElementId": "grantApproverEmail" },
  "if": { "conditions": [{ "elementId": "fundingSource", "comparator": "equal", "value": "Grant" }], "action": "run" }
}
```

Or a string: `"if": "fundingSource === 'Grant'"`. When false, the step is skipped and routing continues through its `onSubmit`.

### Scheduled reminders

```json
"onEnter": {
  "assign": { "nameElementId": "customerName", "emailElementId": "customerEmail" },
  "scheduledActions": [
    { "type": "remind", "when": { "interval": 72, "unit": "hour" }, "notificationTemplateId": "customerReminder" }
  ]
}
```

`notificationTemplateId` points at a notification on the same step with `"type": "remind"` and a matching `"id"`. `when` can also be a date field: `{ "interval": "dueDate", "unit": "date" }`. Reminder templates link with `##submissionUrl##`.

## onSubmit and onReject

Arrays of routing rules evaluated in order; the first rule whose `if` is true (or that has no `if`) wins.

```json
"onSubmit": [
  { "target": "rejected", "if": "approvalDecision === 'Deny'" },
  { "target": "businessOfficeReview", "if": { "conditions": [{ "elementId": "totalCost", "comparator": "notEmpty" }], "action": "run" } },
  { "target": "completed" }
]
```

`onReject` fires from the Reject button and uses the same shape. Send Back is a native platform feature available to every assignee, so do not build reject routes whose only purpose is returning a submission for corrections. Use `onReject` for a real rejection that ends the process:

```json
"onReject": [{ "target": "rejected" }]
```

## Common patterns

Submit and done:
```
start -> completed
```

One approver:
```
start -> principalApproval -> completed
                           -> rejected
```

Multi-level with a conditional middle step:
```
start -> supervisorApproval -> grantApproval (skipped unless grant) -> businessOffice -> completed
```

External party:
```
start -> internalReview -> customerReview -> authorizedSigner (skipped unless a different signer) -> completed
```

Parallel:
```
start -> parallelReview -> finalApproval -> completed
           |- hrReview
           |- financeReview (conditional)
```

## Parallel steps

A parallel container activates several substeps at once and advances only when all are completed or skipped.

```json
"parallelReview": {
  "type": "parallel",
  "substeps": ["hrReview", "financeReview"],
  "onSubmit": [{ "target": "finalApproval" }],
  "onReject": [{ "target": "rejected" }],
  "position": [540, 80]
},
"hrReview": {
  "status": "pending",
  "label": "HR Review",
  "onEnter": { "assign": { "nameElementId": "hrManagerName", "emailElementId": "hrManagerEmail" } },
  "position": [24, 88]
},
"financeReview": {
  "status": "pending",
  "label": "Finance Review",
  "onEnter": {
    "if": "isGreaterThan(totalCost, 1000)",
    "assign": { "nameElementId": "financeManagerName", "emailElementId": "financeManagerEmail" }
  },
  "position": [24, 266]
}
```

| Capability | Container | Substep |
|---|---|---|
| `type: "parallel"` and `substeps` | Required | Not allowed |
| `onEnter.assign` or `sendToSubmitter` | Not allowed | Required |
| `onEnter.if` | Allowed (skips the whole group) | Allowed (skips that substep) |
| `onSubmit` / `onReject` | Required | Not allowed |
| `status` | None | `"pending"` |
| Permissions entry in steps.txt | None | Yes, like any step |
| Notifications | Allowed | Allowed |

Rules: substeps are top-level steps referenced from `substeps`; a substep belongs to one container; no transition may target a substep; no nested parallels; `start`, `completed`, and `rejected` cannot be substeps. A reject from any substep triggers the container's `onReject` immediately and interrupts the others. Re-entering a container resets every substep. Substeps cannot see each other's data until all complete (last write wins on merge). `currentStep()` returns the substep id. Control buttons per substep with `display` on `<Actions>`, not with `_actions` permissions.

## Permissions (steps.txt)

```json
{
  "start": {
    "permissions": {
      "sectionRequester": "readonly",
      "submittedByName": "editable",
      "submittedByEmail": "editable",
      "sectionComputed": "hidden",
      "principalName": "readonly",
      "principalEmail": "readonly",
      "sectionApproval": "hidden",
      "approvalDecision": "hidden",
      "approverSignature": "hidden",
      "expenses": "editable",
      "expenseDate": "editable",
      "amount": "editable",
      "lineTotal": "readonly"
    }
  },
  "principalApproval": {
    "permissions": {
      "sectionApproval": "readonly",
      "approvalDecision": "editable",
      "approverSignature": "editable"
    },
    "actions": {}
  },
  "completed": { "permissions": { "_actions": "hidden" } },
  "rejected": { "permissions": { "_actions": "hidden" }, "actions": {} }
}
```

Values: `editable`, `readonly`, `hidden`, `redacted`.

Rules:

1. `start` lists every element explicitly. Later steps list only overrides; anything unlisted defaults to `readonly`.
2. `_actions` controls the submit and reject bar. Terminal steps set it `hidden`.
3. Non-start, non-terminal steps carry an empty `"actions": {}`.
4. Sections, Tiles, Text, Image, Spacer, and Line are structural: `readonly`, `hidden`, or `redacted`, never `editable`. The fields inside carry their own permissions.
5. `<Computed>` is never `editable`. Identifiers and Timestamps are normally `readonly`.
6. A Table and each of its columns get separate entries. Formula and `values` columns are `readonly`; data-entry columns are `editable`.
7. If any column is `editable` in a step, the Table must be `editable` in that step too. On later steps the Table defaults to `readonly`, so add it explicitly alongside the columns.
8. Distance columns (`type="distance"`) must be `editable` where their address columns are entered, or the lookup never runs.
9. Hidden helper sections stay `hidden` on every step.
10. Parallel containers get no entry; each substep gets its own, with `"actions": {}`.
11. `<Html>` and `<Actions>` ids never appear.
12. `redacted` hides a field from every viewer of that step, including staff in the dashboard. To keep an internal note readable by staff but hidden from external recipients, set it `readonly` and list it in the notification's `hidden` array instead.

## Platform notes

- One assignee per step. No group queues. When two people could handle a step, assign one, notify the other, and drive the choice from a dataset so the district can change it later.
- Data saves only on step transitions. Save Progress exists for the current assignee but does not advance the step.
- Attributes (profile prefill) cover name and email only.
