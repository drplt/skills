# Datasets, attributes, tags, integrations, and URL prefill

## Datasets (`docs/datasets.txt`)

Datasets are lookup tables (schools, departments, budget codes, staff, rates) that live in the Droplet workspace and feed dropdowns, lookups, and assignments.

### Reference global datasets by id

```json
{
  "local": {},
  "global": {
    "schools": { "datasetId": "REPLACE_ME" },
    "budgetCodes": { "datasetId": "REPLACE_ME" }
  }
}
```

- `local` stays `{}`. Do not scope datasets to one form.
- Each key under `global` is the variable name formulas use. `datasetId` is the workspace dataset it resolves to at runtime.
- Do not embed rows. Deliver each dataset as its own JSON file (`datasets/schools.json`) for the user to upload as a global dataset, then they paste the id in.
- Exported forms contain a `resolved` block with a snapshot of rows. That is Droplet's export artifact; omit it in files you write.

### Dataset shape

A keyed object. The key is what a dropdown shows and stores; the record holds the lookup fields.

```json
{
  "Lincoln Elementary": {
    "Type": "Site",
    "Address": "100 Main St, Springfield, IL 62701",
    "principal": { "name": "Avery Whitfield", "email": "avery.whitfield@example.org" }
  },
  "Transportation": {
    "Type": "Department",
    "director": { "name": "Jordan Okafor", "email": "jordan.okafor@example.org" }
  }
}
```

Store addresses as single strings when a `<Distance>` will consume them.

### Using datasets in formulas

```js
options="Object.keys(schools).sort()"
options="Object.keys(schools).filter(k => schools[k]['Type'] === 'Site').sort()"
formula="school ? schools[school]['principal']['email'] : ''"
```

### Filtering a dataset per step (privacy or scoping)

```json
"global": {
  "staff": {
    "datasetId": "REPLACE_ME",
    "filters": [
      { "steps": ["start"], "filter": "filterDataset({ matches: [ { fields: ['role'], value: 'Teacher' } ] })" }
    ]
  }
}
```

`fields` names a path inside the dataset record; `value` is a form field id or a quoted literal. Operators: `eq` (default), `ne`, `gt`, `gte`, `lt`, `lte`. No substring or array-membership matching. Filters apply only on the published form, not in the editor's tester. Filter by presence of a scalar field to drop records shaped differently. For a merely tidier dropdown, filter in the `options` expression instead.

### Datasets API

Droplet exposes a REST API (see docs.droplet.io, Developer and API, Datasets) for reading and writing datasets from scripts. Rows live in versions: create a new version with the full data, then publish it. Send `data` as a keyed object matching the shape above, not as an array, or the dataset publishes unkeyed and `dataset[key]` never resolves. Authentication exchanges a long-lived API token for a short-lived access token (`POST /v1/identity/client-access`, then use `data.accessToken`).

## Attributes (`docs/attributes.txt`)

Auto-fill fields from the logged-in profile at a step.

```json
{ "start": { "submittedByName": "fullName", "submittedByEmail": "primaryEmail" } }
```

Only name and email are reliably available. School, department, and position are not profile attributes; use dataset-driven dropdowns.

## Tag expressions (`docs/tagExpressions.txt`)

Tags label submissions for filtering and for role-scoped visibility.

```json
{ "school": "school", "Request ID": "requestId", "Stage": "currentStep() === 'principalApproval' ? 'Principal' : ''" }
```

Roles restricted to a school see submissions whose tag matches, so any form with per-school visibility should tag the school field. Match the tag label's case to the existing role condition in that workspace. Often `{}`.

## Translations (`docs/translations.txt`)

`{}` unless the form is translated in the editor.

## Integrations (`docs/integrations.txt`)

Outbound data on step events, keyed by step, then event (`onEnter` when the step begins, `onExit` when it finishes), then an array.

```json
{
  "completed": {
    "onExit": [
      {
        "type": "customWebhook",
        "configuration": {
          "itemName": "Post approved trip",
          "connectionId": 0,
          "endpoint": "https://example.org/hook?op=create&token=REPLACE_ME",
          "includeMetadata": false,
          "mappings": [
            { "source": "submittedByEmail", "targetField": "submittedByEmail" },
            { "source": "tripDate", "targetField": "tripDate" },
            { "source": "requestId", "targetField": "submissionId" }
          ]
        }
      }
    ]
  }
}
```

- Only mapped fields are sent, keyed by `targetField`. A visible `<Identifier>` makes a stable per-submission id.
- `connectionId` is a workspace connection created in the Droplet UI. A placeholder imports cleanly and then fails the first submission with `Missing the connectionId`. After import, bind the connection on one integration in the editor, export the form, read the real id from `docs/integrations.txt`, and write it into every integration.
- Never write `"secret": ""`. Omit the key unless referencing a real named secret in that workspace.
- Static parameters (tokens, an operation flag) ride in the endpoint query string.
- Sheet integrations configured in the UI export as `"type": "google"` with `itemName`, `connectionId`, and `mappings` whose `targetField` is the column header.

Webhooks placed inside `workflow.txt` do nothing; they must be here.

## URL prefill

Open a form with fields filled: `https://app.droplet.io/form/<formId>?data.<fieldId>=<value>&data.<other>=<value>`.

- URL-encode values. Dropdown and radio values must match an option key exactly.
- Datetime takes `YYYY-MM-DD`.
- Prefill is flat: table rows cannot be seeded.
- For an unpublished draft: `?preview=true&version=draft-<timestamp>&data....`
- With `loginRequired` and `submitAsLoggedIn`, the logged-in identity may override prefilled name and email.
