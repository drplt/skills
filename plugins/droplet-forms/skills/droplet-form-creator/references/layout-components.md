# Layout components

`docs/layout.txt` is JSX-like markup on a 12-column grid. Components sit inside `<Section>` elements under a single root `<Form>`. Every input component defaults to `required={true}`; pass `required={false}` to make it optional.

## Structure

- `<Form>` is the root. Its only children are `<Section>` elements, `<Actions>` blocks, and (optionally) `<View>` wrappers.
- `<Section>` cannot nest. Sections are always full width.
- `<Tile>` nests to any depth and is the tool for columns, boxes, and conditional groups inside a Section. Prefer Tiles over Groups.
- `<Table>` goes directly inside a Section.
- `<Actions>` is a direct child of `<Form>` and needs no Section.

```jsx
<Form color="#203E7C">
  <Section id="sectionHeader">
    <Image id="logo" src="https://placeholder.example.com/logo.png" columns={4} align="center" width={50} />
    <Text id="textTitle" columns={8}>
      <h1><span style={{ color: "#203E7C", fontSize: 26 }}>Field Trip Request</span></h1>
    </Text>
  </Section>
  <Section id="sectionRequester">
    <Input id="submittedByName" label="Your Name" columns={6} />
    <Input id="submittedByEmail" label="Your Email" type="email" columns={6} />
  </Section>
  <Actions submitText="Submit" enableReject={false} />
</Form>
```

`color` on `<Form>` is the theme color (hex).

## Containers

### Section

```jsx
<Section
  id="sectionTripDetails"    // descriptive camelCase
  marginTop={30}             // optional, px
  marginBottom={10}          // optional, px
  wide                       // optional, reduces page side margins
  border                     // optional
  borderColor="#E3F3F1"      // optional
  background="#F8F8F8"       // optional
  display="isOvernight"      // optional display condition
>
```

### Tile

```jsx
<Tile
  id="tileCostSummary"
  columns={6}                // grid width 1 to 12
  background="#EEF7FF"       // optional
  border                     // optional
  borderColor="#EEF2FF"      // optional
  display="hasCosts"         // optional
>
```

Two Tiles with `columns={6}` side by side make a two-column layout.

## Input components

### Input

```jsx
<Input
  id="employeePhone"
  label="Phone"
  columns={4}
  type="email"               // optional: "email", "number"
  mask="/{phone}"            // optional
  placeholder="(   )    -"   // optional
  hint="Helper text under the field"
  tooltip="Longer explanation on hover"
  required={false}
  initialValue="default"
  display={...}
  validate={...}
  clear                      // resets the value when hidden by a display rule
/>
```

Masks:

| Mask | Effect |
|---|---|
| `/{currency}` | Currency formatting (named mask, preferred) |
| `/{phone}` | Phone formatting (named mask, preferred) |
| `/(5)9` | Exactly 5 digits |
| `/(8)[0-9]` | Up to 8 digits |
| `/9/9/9/9/9` | Five individual digits |
| `/[0-1]/[0-9]/[/]/[0-9]/[0-9]` | Character-class pattern (MM/YY) |

### Textarea

```jsx
<Textarea id="justification" label="Justification" rows={3} columns={12} placeholder="Optional" required={false} />
```

### Dropdown

```jsx
<Dropdown
  id="school"
  label="School"
  columns={6}
  options={["Option 1", "Option 2"]}
  // OR a dynamic expression that returns an array of strings:
  options="Object.keys(schools).sort()"
  // OR static single-pair objects when the stored value differs from the label:
  options={[
    { PreK: "UPK (Pre-Kindergarten)" },
    { K: "Kindergarten" },
    { "1": "1" },
  ]}
  hideSearch                 // optional; NOT compatible with multiple
  multiple                   // optional multi-select
  initialValue="Option 1"
  required={false}
/>
```

Rules: `{ label, value }` objects are rejected on import. A dynamic expression must return plain strings; an expression returning objects shows the same label for every option.

### Radio

```jsx
<Radio
  id="approvalDecision"
  label="Decision"
  columns={12}
  horizontal
  options={["Approve", "Deny"]}
  // OR key/value pairs (key stored, value displayed):
  options={[
    { me: "I am authorized to sign." },
    { notMe: "Someone else is authorized to sign." },
  ]}
/>
```

### Checkbox

```jsx
<Checkbox
  id="transportNeeds"
  label="Transportation"
  columns={12}
  horizontal
  minWidth={180}             // per option in horizontal mode
  options={["Bus", "Van", "Parent drivers"]}
  initialValue={["Bus"]}
/>
```

A Checkbox value is an array. Display conditions targeting it use `oneOf`, `allOf`, `noneOf`, `empty`, or `notEmpty` with an array value.

### Boolean

Single toggle. It does not support `required`; use `validate` to require it, or a single-option Checkbox for an optional tick box.

```jsx
<Boolean id="agreeToTerms" label="Terms" text="I have read the policy" columns={6} tooltip="..." initialValue />
```

A bare `initialValue` (no value) starts it checked.

### Datetime

```jsx
<Datetime id="tripDate" label="Trip Date" columns={4} min="today()" clear />
```

`min` and `max` accept several shapes:

```jsx
min="today()"
min="otherDateFieldId"
min={{ elementId: "otherDateFieldId" }}
min={{ adjustment: { weeks: 2 }, adjustor: "add", specialDate: "now" }}
max={{ adjustment: { years: 4 }, adjustor: "subtract", specialDate: "now" }}
min="addDays(-60, new Date())"
```

Use `min` and `max` for date bounds rather than a `validate` rule. Values are stored as `YYYY-MM-DD`.

### Signature and Timestamp

```jsx
<Signature id="employeeSignature" label="Signature" columns={8} />
<Timestamp
  id="employeeSignatureDate"
  label="Date Signed"
  columns={4}
  display={{ conditions: [{ elementId: "employeeSignature", comparator: "notEmpty" }], action: "show" }}
/>
```

A Timestamp records the moment it renders. Gated behind a Signature it becomes "date signed"; bare, it becomes "form started". It must be visible on the step where it should stamp. Values are `YYYY-MM-DDTHH:mm` local time.

### Upload

```jsx
<Upload id="receipts" label="Receipts" text="Add attachment" hint="PDF or image" multiple columns={6} required={false} />
```

There is no upload column for tables. For per-row attachments, add N Upload fields below the table gated by row count: `display="expenses.length >= 2"`, labeled with `##expenses.1.vendor##`.

### Address and Distance

```jsx
<Address id="startAddress" label="Start" columns={6} />
<Address id="endAddress" label="Destination" columns={6} />
<Distance id="tripMiles" label="Miles" columns={3} startAddress="startAddress" endAddress="endAddress" distanceUnits="mi" />
```

A Distance endpoint can be a Computed field, but it must return one geocodable string, not an address object.

A Distance only looks up miles while it is on screen. Hidden by `display` (including `alwaysHide`) or by a `hidden` permission, it stays blank, and so does every Computed that reads it. To show round trip or reimbursable miles, keep the one way Distance visible in its own labeled row and put the Computeds in the row below. Google returns its optimal driving route, which accounts for travel time, so it is not always the shortest distance.

### Computed

Read-only value driven by a formula (see the logic reference).

```jsx
<Computed id="totalCost" label="Total" columns={3} formula="toCurrency(sum(lineTotal))" hint="Auto-calculated" />
<Computed id="approverEmail" label="Approver Email" columns={3} formula="schools[school]['principal']['email']" display={{ action: "alwaysHide" }} />
```

Computed fields are `readonly` or `hidden` in every step, never `editable`.

### Identifier

Sequential id, claimed when the field renders.

```jsx
<Identifier id="requestId" label="Request ID" mode="auto" columns={3} formula="`FT${padStart(String(getSequenceId()), 5, '0')}`" />
```

Keep it visible on `start`. A hidden Identifier stays empty. Do not name it `formId`; that is a reserved email template key and the import fails. `referenceId`, `requestId`, or a form-specific id all work.

## Display components

### Text

Static content with `##fieldId##` interpolation.

```jsx
<Text id="textSummary" columns={12} marginTop={10} marginBottom={10} display="totalCost">
  <p>Total requested: <b>##totalCost##</b></p>
  <p style={{ textAlign: "center", color: "#555555", fontSize: 12 }}>First date: ##allDates[0]##</p>
</Text>
```

Styling inside Text is strict:

- Supported properties: `color`, `fontSize` (number, px), `fontFamily`, `textAlign`. `fontWeight` on a `<p>` or `<div>` also passes.
- `<p>` and `<div>` accept all four directly.
- Headings (`<h1>`, `<h2>`, `<h3>`) do not accept `color`, `fontSize`, or `fontFamily`. Wrap the content in a `<span>` and style the span. Put `textAlign` on the heading itself.
- `<span>` does not accept `textAlign`.
- No `margin`, `padding`, `background`, `border`, `borderRadius`, or any other box-model property. Use `marginTop`/`marginBottom` on Text, `background`/`border` on Tile or Section.
- `fontFamily: "signature"` on a span around `##signatureId##` renders a typed signature in a print view.

Interpolation forms: `##fieldId##`, `##arrayField[0]##`, `##tableId.0.columnId##`. Never `###fieldId##`.

### Image

```jsx
<Image id="logo" src="https://placeholder.example.com/logo.png" columns={4} align="center" width={50} />
```

Use a placeholder URL. The real asset is uploaded in the Droplet editor.

### Spacer, Line, Pagebreak

```jsx
<Spacer id="spacerTop" columns={12} height={32} />
<Line id="lineDivider" color="#F8F8F8" weight={2} wide />
<Line id="lineVertical" vertical />
<Pagebreak />
```

### Html

Static markup only: buttons and links.

```jsx
<Html columns={3} display="currentStep() === 'completed'">
  <a href="https://example.org/policy" target="_blank">
    <button class="drplt-btn drplt-btn-block drplt-btn-secondary"><b>View Policy</b></button>
  </a>
</Html>
```

Classes: `drplt-btn`, `drplt-btn-block`, `drplt-btn-secondary`. No `style="..."` strings (the form crashes). No `##interpolation##` (renders empty). Presentational attributes (`bgcolor`, `width`, `cellpadding`, `border`) pass through. Html ids never appear in `steps.txt`.

## Tables

```jsx
<Table
  id="expenses"
  label="Expenses"
  hint="Add one row per receipt"
  initialRows={1}            // starting rows; users add more with +
  displayRows="allDates.length"  // optional; locks the row count to the expression
  display="hasExpenses"
>
  <TableColumn id="expenseDate" label="Date" type="date" width={15} />
  <TableColumn id="vendor" label="Vendor" width={30} required />
  <TableColumn id="category" label="Category" type="dropdown" options={["Meals", "Lodging", "Other"]} hideSearch width={20} />
  <TableColumn id="amount" label="Amount" mask="/{currency}" width={15} sum />
  <TableColumn id="lineTotal" label="Total" width={20} formula="toCurrency(fromCurrency(getCell(amount)) * 1)" align="right" bold />
</Table>
```

TableColumn props: `type` (`dropdown`, `date`, `checkbox`, `email`, `address`, `distance`, or omit for text), `options` (static array or expression), `hideSearch`, `mask`, `width` (percent), `bold`, `sum` (column total), `required`, `formula` (computed column, use `getCell(columnId)` for the current row), `values` (pre-filled per-row values, for example `values={["##allDates[0]##", "##allDates[1]##"]}`), `validate`, `align` (only with `formula` or `values`).

Rules:

- No `initialValue` on a column. A checkbox column exists but cannot start checked.
- `display` on a column cannot reference a sibling column.
- Distance columns: `type="distance" startAddress="fromCol" endAddress="toCol" distanceUnits="mi"`, pointing at two typed `type="address"` columns. They must be `editable` in the step where addresses are entered.
- Permissions: the Table id and every column id each get an entry in `steps.txt`.
- For a read-only mirror of a table (print views), use `displayRows="Array.isArray(expenses) ? expenses.length : 0"` and formula columns reading `expenseDate[getCurrentRowIndex()]`.

## Actions

```jsx
<Actions
  display="currentStep() === 'start'"
  submitText="Submit Request"
  rejectText="Deny"
  enableSubmit={true}
  enableReject={false}
  enableNext={false}
  enableBack={false}
/>
```

Several `<Actions>` blocks with different `display` conditions give each step its own button labels. In parallel substeps, use `display` on Actions rather than `_actions` permissions.

## Print views

To produce a designed printable document instead of the default layout mirror, wrap the interactive sections in `<View type="web">` and add a `<View type="print">` built from Text, Tile, Section, Image, and read-only Tables with `##fieldId##` interpolation. `<Actions>` stays outside both views. Views take no id and no permissions; the elements inside a print view do take permissions (list them `readonly` in `start`). Input components live only in the web view since ids are unique form-wide; reference a signature in print through its Timestamp ("Signed electronically on ##employeeSignatureDate##"). Formula columns wrap text when printed; input cells clip.

## The `clear` prop

`clear` on any input resets its value when a display rule hides it, so stale answers do not travel with the submission. Add it to every field inside a conditionally shown Tile or Section.
