---
name: droplet-form-creator
description: Build and edit Droplet Forms and Workflows .drplt files (layout, workflow, permissions, notifications, datasets) from a plain-language request. Use for any Droplet form or .drplt task.
---

# Droplet Form Creator

This skill turns a description of a form and its approval process into a complete `.drplt` file that imports into Droplet (Forms and Workflows). It also edits, reviews, and explains existing `.drplt` files.

## When to use

- The user wants a new Droplet form, approval workflow, notification set, or dataset-driven dropdown.
- The user hands you a `.drplt` file to change, check, or explain.
- The user asks how a Droplet layout, workflow, permissions, notification, dataset, or integration module works.

## What a .drplt is

A `.drplt` is a zip archive. You author `meta.json` plus nine text files under `docs/`. The bundled script derives the `import/` half (the same data wrapped as JavaScript modules) and zips everything.

| You write | Contains |
|---|---|
| `meta.json` | `{ "version": 1, "form": { "name", "description", "loginRequired", "submitAsLoggedIn" } }` |
| `docs/layout.txt` | The form layout in JSX-like markup, from `<Form>` to `</Form>` |
| `docs/workflow.txt` | Workflow steps, assignments, and routing (JSON) |
| `docs/steps.txt` | Per-step field permissions: editable, readonly, hidden, redacted (JSON) |
| `docs/notifications.txt` | Email templates per step (JSON) |
| `docs/datasets.txt` | References to lookup datasets (JSON) |
| `docs/attributes.txt` | Profile auto-fill mappings (JSON, often only name and email) |
| `docs/tagExpressions.txt` | Submission tags (JSON, often `{}`) |
| `docs/translations.txt` | Translations (JSON, `{}`) |
| `docs/integrations.txt` | Outbound webhooks and sheet integrations (JSON, often `{}`) |

The script generates `import/layout.jsx`, `import/<module>.js` for every JSON module, `import/metadata.js`, and `import/package.json`. If you cannot run scripts, build them by hand using Appendix A.

## Process

1. **Read before writing.** Always read `references/gotchas.md`. Then read the reference for each module you will touch (see the reference map below). Open the exemplar in `references/exemplars/` closest in complexity to the request and study its `docs/layout.txt`, `docs/workflow.txt`, and `docs/steps.txt`.
2. **Decide the shape.** List the sections and fields, the workflow steps and who is assigned at each, which notifications fire, and which dropdowns need a dataset. Ask the user only when different readings would produce materially different forms. Otherwise choose sensible defaults, build, and state your assumptions in the handoff.
3. **Write the files** in a working folder named after the form: `meta.json` and the nine `docs/*.txt` files. Write every file, including the empty modules (`{}`).
4. **Lint and build.**
   ```
   python3 scripts/build_drplt.py build "<Form Name>"
   ```
   Fix every ERROR and read every warning. The script writes `<Form Name>/<Form Name>.drplt`. Use `-o` to choose another path.
5. **Hand over.** Give the user the `.drplt` path, the list of placeholders to replace (dataset IDs, approver names and emails, logo URL, webhook connection IDs), the import steps (Droplet: Forms, then Import), and what to test in the workflow tester.

To edit an existing form: `python3 scripts/build_drplt.py extract "Existing.drplt"` unpacks `meta.json` and `docs/` into a folder. Edit the text files, then build. Never hand-edit the `import/` files separately; they are regenerated.

## Hard rules

These break the import or fail silently at runtime. Check every one before building.

1. **Required system fields.** Every form has `<Input id="submittedByName">` and `<Input id="submittedByEmail" type="email">`. The form will not import without them. Put them near the top.
2. **Structure.** Every element except `<Actions>` sits inside a `<Section>`. Sections are direct children of `<Form>` and never nest. Tiles nest freely inside Sections. Tables go directly inside a Section. `<Actions>` is a direct child of `<Form>`.
3. **Ids.** Field, section, tile, and step ids are unique, descriptive, and camelCased (`travelStartDate`, `principalApproval`, not `input1`, `step2`). `start` and `completed` are reserved step ids. Include `rejected` only when a route actually targets it. An element id can never be one of the notification template keys: `formId` fails import (`element has an id that is a reserved email template key`), and `formName`, `submissionId`, `submissionUrl`, `assignmentUrl`, `recipientFirstName`, `initiatedByFullName`, and `_reason` are the same family. Name an Identifier `referenceId` or `requestId`, never `formId`.
4. **Component props.** `<Boolean>` has no `required` prop (use `validate`). `<TableColumn>` has no `initialValue`. `align` on a TableColumn needs `formula` or `values`. `hideSearch` and `multiple` cannot both be on a `<Dropdown>`. There is no upload column type.
5. **Options.** Static option objects are single-pair, `{ storedValue: "Display Text" }`. `{ label, value }` objects are rejected. Dynamic option expressions return a plain array of strings.
6. **Conditions.** A conditions object with two or more conditions must set `operator: "and"` or `"or"`. Conditions that target a `<Checkbox>` use `oneOf`, `allOf`, `noneOf`, `empty`, or `notEmpty` with an array `value`; `includes` and `equal` are rejected there.
7. **Text styling.** Inside `<Text>`, `style={{ }}` accepts only `color`, `fontSize`, `fontFamily`, `textAlign`. Headings cannot take color or fontSize directly; wrap the heading content in a `<span>` and style the span. A `<span>` cannot take `textAlign`. No margin, padding, background, or border in styles; use component props (`marginTop`, `background`, `border`) instead.
8. **Html blocks are static.** No `style="..."` strings (they crash the form) and no `##field##` interpolation (it renders empty). `<Html>` and `<Actions>` ids never appear in `steps.txt`.
9. **Permissions.** The `start` step lists every input element. Unlisted elements default to readonly, which silently locks a field on later steps. `<Computed>` is never editable (import error). Sections, Tiles, Text, and other structural elements are never editable. A Table and each of its columns get separate entries, and an editable column requires its Table to be editable in that same step. Parallel container steps get no permissions entry; their substeps do. Terminal steps set `"_actions": "hidden"`.
10. **Assignment.** Dynamic assignees use `"assign": { "nameElementId": "<role>Name", "emailElementId": "<role>Email" }` pointing at two `<Computed>` fields that return strings. Static assignees use `"assign": { "name", "email" }`. One person per step; Droplet has no group assignment.
11. **Notifications.** `template` contains only `subject` and `body`. `type`, `recipients`, `sendToSubmitter`, `if`, `attachSubmissionPdf`, and `hidden` are siblings of `template`, never inside it. A `type: "remind"` template links with `##submissionUrl##`, never `##assignmentUrl##`.
12. **Datasets.** Keep `"local": {}`. Reference each dataset under `global` by its Droplet `datasetId`. Do not embed rows. Deliver each dataset as its own JSON file for the user to upload, and use `"datasetId": "REPLACE_ME"` until they give you the real id.
13. **Integrations.** Never write `"secret": ""`; omit the key. A placeholder `connectionId` imports but blocks the step at runtime; tell the user to bind the connection in the editor and re-export to learn the real id.
14. **Identifiers and Timestamps stamp on render.** They must be visible (not `alwaysHide`, not `hidden`) on the step where their value is first needed, or they stay empty forever.
15. **Formulas.** `new Set()` is unavailable. `sum()` over a formatted currency column can return a string, so coerce with `parseFloat` before arithmetic. Anchor date projections on a stored Timestamp, not on `new Date()` alone, because computed fields re-evaluate on every view.
16. **Interpolation.** `##fieldId##` inserts a value in Text and notifications. Never write `###fieldId##` to get a literal hash; the parser swallows it and renders nothing.
17. **Copy style.** No em dashes or en dashes anywhere in labels, hints, options, text blocks, notifications, or formula strings. Use a comma, period, or parentheses.
18. **docs/ and import/ hold identical data.** The build script guarantees this. If you hand-build, keep them in sync.

## Naming and copy

- Field ids describe the data: `employeeName`, `tripDate`, `totalReimbursement`.
- Step ids describe the role or action: `supervisorApproval`, `businessOfficeReview`, `parentSignature`.
- Section and Tile ids start with the container type: `sectionTripDetails`, `tileCostSummary`.
- Assignee computeds come in pairs named for the role: `principalName` and `principalEmail`, each with a human label, because the label is what the visual workflow editor shows on the step card.
- Labels are short and sentence case. Hints explain format or policy. Tooltips hold the long explanation.
- Do not gate every section on the previous answer. Show every section that every submission fills out; use `display` only for genuinely conditional content.

## Module skeletons

Minimal valid content for each file. Expand from these.

`meta.json`
```json
{ "version": 1, "form": { "name": "Field Trip Request", "description": "field trip, transportation, approval", "loginRequired": true, "submitAsLoggedIn": true } }
```

`docs/layout.txt`
```jsx
<Form color="#203E7C">
  <Section id="sectionRequester">
    <Input id="submittedByName" label="Your Name" columns={6} />
    <Input id="submittedByEmail" label="Your Email" type="email" columns={6} />
    <Dropdown id="school" label="School" columns={6} options="Object.keys(schools).sort()" />
  </Section>
  <Section id="sectionApproval" display="currentStep() !== 'start'">
    <Radio id="approvalDecision" label="Decision" horizontal options={["Approve", "Deny"]} columns={6} />
    <Signature id="approverSignature" label="Approver Signature" columns={6} />
  </Section>
  <Section id="sectionRouting" display={{ action: "alwaysHide" }}>
    <Computed id="principalName" label="Principal Name" columns={6} formula="school ? schools[school]['principal']['name'] : ''" />
    <Computed id="principalEmail" label="Principal Email" columns={6} formula="school ? schools[school]['principal']['email'] : ''" />
  </Section>
  <Actions submitText="Submit" enableReject={false} />
</Form>
```

`docs/workflow.txt`
```json
{
  "test": {},
  "steps": {
    "start": { "onSubmit": [{ "target": "principalApproval" }], "position": [160, 80] },
    "principalApproval": {
      "status": "pending", "label": "Principal Approval",
      "onEnter": { "assign": { "nameElementId": "principalName", "emailElementId": "principalEmail" } },
      "onSubmit": [{ "target": "rejected", "if": "approvalDecision === 'Deny'" }, { "target": "completed" }],
      "position": [560, 80]
    },
    "completed": { "status": "completed", "position": [960, 80] },
    "rejected": { "status": "rejected", "position": [960, 300] }
  }
}
```

`docs/steps.txt`
```json
{
  "start": { "permissions": { "sectionRequester": "readonly", "submittedByName": "editable", "submittedByEmail": "editable", "school": "editable", "sectionRouting": "hidden", "sectionApproval": "hidden", "approvalDecision": "hidden", "approverSignature": "hidden", "principalName": "readonly", "principalEmail": "readonly" } },
  "principalApproval": { "permissions": { "sectionApproval": "readonly", "approvalDecision": "editable", "approverSignature": "editable" }, "actions": {} },
  "completed": { "permissions": { "_actions": "hidden" } },
  "rejected": { "permissions": { "_actions": "hidden" }, "actions": {} }
}
```

`docs/notifications.txt`
```json
{
  "principalApproval": { "onEnter": { "type": "assignment", "template": { "subject": "Field trip request from ##submittedByName##", "body": "<p>Hi ##recipientFirstName##, a request needs your approval.</p><p><a href='##assignmentUrl##'>Review the request</a></p>" } } },
  "completed": { "onEnter": { "template": { "subject": "Your field trip request was approved", "body": "<p><a href='##submissionUrl##'>View the request</a></p>" }, "sendToSubmitter": true } }
}
```

`docs/datasets.txt`
```json
{ "local": {}, "global": { "schools": { "datasetId": "REPLACE_ME" } } }
```

`docs/attributes.txt`
```json
{ "start": { "submittedByName": "fullName", "submittedByEmail": "primaryEmail" } }
```

`docs/tagExpressions.txt`, `docs/translations.txt`, `docs/integrations.txt`
```json
{}
```

## Reference map

| Read this | When |
|---|---|
| `references/gotchas.md` | Always, before writing anything |
| `references/layout-components.md` | Writing or editing `layout.txt`: every component and its props, tables, text styling, print views |
| `references/logic-display-formulas-validation.md` | Any `display`, `validate`, `formula`, `options` expression, or `##interpolation##` |
| `references/workflow-and-permissions.md` | `workflow.txt` and `steps.txt`: assignment, routing, parallel steps, reminders, permissions |
| `references/notifications.md` | `notifications.txt`: schema, recipients, template variables, email HTML |
| `references/datasets-attributes-integrations.md` | `datasets.txt`, `attributes.txt`, `tagExpressions.txt`, `integrations.txt`, URL prefill |
| `references/exemplars/README.md` | Choosing which example form to study |

## Appendix A: building the archive without the script

Each `import/<module>.js` wraps the exact JSON from `docs/<module>.txt`:

```js
const workflow = { ...same JSON... };

// -------
// Exports
// -------

export { workflow };
```

`import/layout.jsx` wraps `docs/layout.txt`, indenting the first line by two spaces and every other line by four:

```jsx
const layout = () => (
  <Form color="#203E7C">
      <Section id="sectionRequester">
        ...
      </Section>
    </Form>
);

// -------
// Exports
// -------

export { layout };
```

`import/metadata.js`:

```js
const metadata = {
  "name": "Field Trip Request",
  "description": "field trip, transportation, approval",
  "version": "draft-1700000000000",
  "loginRequired": true,
  "submitAsLoggedIn": true,
  "published": false,
  "archived": false
};

// -------
// Exports
// -------

export { metadata };
```

`import/package.json`: `{ "name": "@drplt/form-<any 64-hex sha256>", "type": "module" }`.

Zip `meta.json`, `docs/`, and `import/` at the root of the archive (not inside a parent folder) and name the file `<Form Name>.drplt`.

## Appendix B: handoff checklist

Tell the user, in this order:

1. Where the `.drplt` is and what the form does in two or three sentences.
2. Every placeholder to replace, with the file and key: dataset IDs, static approver names and emails, logo image URL, webhook `connectionId`.
3. Any dataset JSON files you produced and that each must be uploaded as a global dataset in Droplet before the dropdowns populate.
4. Import steps: Droplet, Forms, Import, choose the file. Then open the workflow tester and walk one submission through every step.
5. Assumptions you made where the request was ambiguous.
