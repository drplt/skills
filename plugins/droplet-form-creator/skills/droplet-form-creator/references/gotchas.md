# Gotchas: import errors and silent failures

Read this before writing any file. Most items are import-time errors or silent no-ops, not runtime warnings, so the form looks fine until it does not. Every item was confirmed on real forms.

## Will not import

| Area | Trap | Do instead |
|---|---|---|
| Layout | Missing `submittedByName` or `submittedByEmail` | Add both as `<Input>` fields near the top, email with `type="email"` |
| Layout | Section inside a Section | Sections are direct children of `<Form>`; use Tiles for sub-grouping |
| Layout | Element outside any Section | Everything except `<Actions>` lives inside a Section |
| Layout | An element id that is a reserved email template key, such as `<Identifier id="formId">` | Use `referenceId`, `requestId`, or a form-specific name; keep `formName`, `submissionId`, `submissionUrl`, `assignmentUrl`, `recipientFirstName`, `initiatedByFullName`, and `_reason` out of ids too |
| Boolean | `required` prop | Use a `validate` rule to require a checked state, or a single-option `<Checkbox>` |
| TableColumn | `initialValue` prop | Use a `formula` that returns a default, or a `values` array |
| TableColumn | `align` on a plain data-entry column | `align` only works alongside `formula` or `values` |
| TableColumn | `display` condition referencing a sibling column | Reference fields outside the table, or always show the column |
| Dropdown | `hideSearch` together with `multiple` | Pick one |
| Dropdown/Radio | Options as `{ label, value }` objects | Single-pair objects: `{ stored: "Display Text" }`, static arrays only |
| Conditions | Two or more conditions without `operator` | Add `operator: "and"` or `"or"` explicitly; there is no default |
| Conditions | `includes` or `equal` against a `<Checkbox>` | Use `oneOf`, `allOf`, `noneOf`, `empty`, or `notEmpty` with an array value |
| Text styles | Anything beyond `color`, `fontSize`, `fontFamily`, `textAlign` | Component props: `marginTop`, `background`, `border` on Text, Tile, Section |
| Text styles | `color` or `fontSize` directly on `<h1>`, `<h2>`, `<h3>` | Wrap content in a `<span>` and style the span |
| Text styles | `textAlign` on a `<span>` | Put `textAlign` on the parent `<p>`, `<div>`, or heading |
| Steps | A `<Computed>` set to `"editable"` | `"readonly"`, `"hidden"`, or `"redacted"` |
| Steps | A Section, Tile, Text, Image, Spacer, or Line set to `"editable"` | Structural elements are `"readonly"` or `"hidden"`; the fields inside carry their own permissions |
| Steps | An `<Html>` or `<Actions>` id listed in permissions | Omit them entirely |
| Steps | A parallel container step with a permissions entry | Only the substeps get entries |
| Notifications | `sendToSubmitter`, `recipients`, `type`, or `if` inside `template` | They are siblings of `template`; `template` holds only `subject` and `body` |
| Notifications | `##assignmentUrl##` in a `type: "remind"` template | Reminders link with `##submissionUrl##` |
| Integrations | `"secret": ""` | Omit the `secret` key unless referencing a real named secret |
| Workflow | Substep with `onSubmit` or `onReject` | The parallel container owns routing for all substeps |
| Workflow | A transition targeting a substep | Target the parallel container |
| Html | `style="..."` string attribute | Presentational attributes (`bgcolor`, `width`, `cellpadding`) only; React error #62 otherwise |

## Imports fine, then fails or misbehaves

| Symptom | Cause | Fix |
|---|---|---|
| A field cannot be edited on a later step | Unlisted elements default to `readonly` in every step after `start` | List the field as `"editable"` in that step's overrides |
| Editable columns stay locked | The Table itself is `readonly` (or unlisted) in that step | Add the Table id as `"editable"` alongside its editable columns |
| Distance column shows no miles | Distance TableColumn is `readonly` where addresses are typed | Make `type="distance"` columns (and their Table) `"editable"` in the step where addresses are entered |
| Distance shows 0 miles from a computed address | The computed returned an address object | Return one geocodable string: `street + ', ' + city + ', ' + state + ' ' + zip` |
| Distance column ignores a formula-driven address column | Column distance only geocodes addresses typed through autocomplete | Use free-entry `type="address"` columns; form-level `<Distance>` does accept a computed string |
| Identifier or Timestamp is empty in a webhook, formula, or notification | It was never rendered (`alwaysHide` section or `hidden` permission) | Keep it visible (readonly) on the step where its value is first needed |
| Total shows `$0.000` or a threshold check misfires | `sum()` over a currency-formatted column returned a string, and `+` concatenated | `const n = v => parseFloat(String(v).replace(/[^0-9.-]/g, '')) \|\| 0;` then do the math on `n(...)` |
| A projected date keeps moving | Computed fields re-evaluate on every view, so `new Date()` drifts | Anchor on a stored Timestamp: `signedAt ? new Date(signedAt) : new Date()` |
| Submit fails with a generic error and no highlighted field | `submittedByName` computed returned an array (`getDatasetChildValues` always returns an array) | Unwrap: `Array.isArray(v) ? v[0] : v`, then `String(...)` |
| `###fieldId##` renders nothing | The parser opens on the first `##` and looks up `#fieldId` | Put a space between the literal `#` and `##fieldId##`, or drop the hash |
| Dataset filter has no effect in the tester | `filterDataset()` runs only on the published form | Publish, then test |
| Every dynamic dropdown option shows the same label | Dynamic options returned `{label, value}` objects | Return a plain array of strings |
| Same-step data from a parallel substep is not visible to the other substep | Parallel substeps are isolated until all complete | Design substeps to be independent; merge happens on completion |
| Webhook step blocks with `Missing the connectionId` | Placeholder `connectionId` | Bind the connection in the editor, export, copy the real id into every integration, re-import |
| Field shows stale value after being hidden | No `clear` prop | Add `clear` to fields that should reset when hidden by a display rule |

## Platform behaviors that shape the design

- **Send Back is native.** Approvers can return a submission from the actions menu. Do not build "Return to Employee" reject routes or reason-capture flows just for corrections. Use `onReject` only for a genuine reject-to-terminal route.
- **Data saves on step transitions only.** There is no in-place edit and save. The Save Progress button works only for the current assignee and does not advance the step.
- **Profile prefill is name and email only.** The `attributes` module can fill `submittedByName` (`fullName`) and `submittedByEmail` (`primaryEmail`). School, department, position, and role are not profile attributes; use a dataset-driven dropdown the user picks.
- **One assignee per step.** There are no group assignments or shared queues. When "either person can handle it", pick one as the assignee, copy the other in a notification, and make the choice dataset-driven so the district can change it without a form edit.
- **Timestamps stamp when rendered.** A bare `<Timestamp>` records when the form was opened. A Timestamp whose `display` waits for a Signature to be non-empty records when it was signed.
- **Identifiers claim their sequence number at render.** Gaps from abandoned drafts are normal.
- **Tables inside Tiles.** The documented rule is Tables directly inside a Section. Forms with a Table inside a Tile have imported, so treat the Section placement as the safe default rather than an absolute.
- **No dynamic-width progress bar.** Every approach fails (`<Html>` cannot interpolate; a computed HTML string is escaped by `<Text>`). Present progress numerically, for example "12 of 21 hours used".
- **No upload column.** For per-row attachments, place N `<Upload>` fields below the table, each gated by `display="tableId.length >= N"` and labeled with `##tableId.column[N-1]##`.
- **URL prefill is flat.** `?data.fieldId=value` fills top-level fields only; table rows cannot be seeded through the URL.
- **Formula runtime.** No `new Set()`. Arrays, objects, Math, String, Date, ternaries, template literals, and IIFEs all work.

## Pre-build checklist

- [ ] `submittedByName` and `submittedByEmail` present
- [ ] No element id reuses a notification template key (`formId` and its siblings)
- [ ] Every input element listed in the `start` permissions
- [ ] Computed, Section, Tile, Text never editable
- [ ] Editable columns have an editable parent Table in that step
- [ ] `align` only on formula or values columns; no `initialValue` on columns
- [ ] `operator` present on every multi-condition object
- [ ] `sendToSubmitter`, `recipients`, `type`, `if` outside `template`
- [ ] Reminders link with `##submissionUrl##`
- [ ] Parallel container has no permissions entry and no assign
- [ ] Datasets referenced by `datasetId`, `local` is `{}`, no embedded rows
- [ ] No `"secret": ""`
- [ ] Identifiers and Timestamps visible where their value is needed
- [ ] No em dashes in any copy
- [ ] `##fieldId##` references all match real ids

## Updating a form that already exists

A `.drplt` import always creates a new form with a new link. It cannot overwrite a form already in
the workspace. To change a form that is live or already imported, open it in the editor and paste
the changed `docs/*.txt` modules into the matching code views, in this order so references
resolve: `layout.txt`, `workflow.txt`, `steps.txt`, `notifications.txt`, then `datasets.txt`,
`attributes.txt`, and `tagExpressions.txt` if they changed. The form name and login settings are
edited in the form's settings, not pasted. When handing over a revision, say which modules changed
since the last hand-over so nothing is pasted twice or missed.
