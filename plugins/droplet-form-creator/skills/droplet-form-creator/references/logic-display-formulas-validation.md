# Display conditions, formulas, and validation

## Display conditions

Any component can take a `display` prop in one of three forms.

### 1. Expression string

```jsx
display="isOvernight"                          // truthy
display="tripType === 'Overnight'"             // equality
display="isOvernight && studentCount > 30"     // logic
display="currentStep() === 'start'"            // step check
display="currentStep() !== 'start'"
display="typeof _reason !== 'undefined'"       // a reject reason exists
display="value || (nextAction && nextAction === 'Approve')"
display="false"                                // always hidden
```

`value` refers to the component's own current value. `_reason` holds the reject or send-back reason.

### 2. Conditions object

```jsx
display={{
  conditions: [
    { elementId: "tripType", comparator: "equal", value: "Overnight" },
    { elementId: "studentCount", comparator: "notEmpty" },
  ],
  operator: "and",   // REQUIRED with two or more conditions; no default
  action: "show",    // "show" or "hide"
}}
```

Comparators for scalar fields: `equal`, `notEmpty`, `empty`, `truthy`, `falsy`, `includes` (substring).

Comparators for `<Checkbox>` fields (array values): `oneOf`, `allOf`, `noneOf`, `empty`, `notEmpty`. `value` is an array:

```jsx
display={{ conditions: [{ elementId: "transportNeeds", comparator: "oneOf", value: ["Other"] }], action: "show" }}
```

### 3. Always hide

```jsx
display={{ action: "alwaysHide" }}
```

Used for Sections holding helper Computed fields. Never put an Identifier or Timestamp in an always-hidden Section if its value is needed.

### Use progressive disclosure sparingly

Show every section that every submission fills out with no `display` prop. Reserve `display` for content that depends on an answer: the overnight details only when `tripType === 'Overnight'`, the grant fields only when `fundingSource === 'Grant'`, the ineligible message only on the dead-end path. Revealing one section at a time frustrates people who want to see the shape of the form.

### The `clear` prop

Add `clear` to fields inside conditionally shown containers so their values reset when hidden.

## Formulas

Computed fields, formula columns, dynamic `options`, `displayRows`, `validate`, workflow `if` strings, and notification `if` strings are all JavaScript expressions. Every field id is a variable. Dataset names are variables too.

### Simple expressions

```js
formula="fieldA + fieldB"
formula="reimbursement > 0 ? 'Reimbursement' : 'Employee owes'"
formula="'$0.70'"
formula="100"
formula="toCurrency(sum(lineTotal))"
```

### IIFE for anything with statements

```js
formula="(()=>{
  if (!startDate || !endDate) return [];
  const start = new Date(startDate + 'T00:00:00');
  const end = new Date(endDate + 'T00:00:00');
  const days = [];
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    days.push(d.toISOString().slice(0, 10));
  }
  return days;
})()"
```

### Built-in helpers

| Helper | Use |
|---|---|
| `sum(a, b, ...)` / `sum(columnId)` | Add values, or total a table column |
| `multiply(a, b)` | Multiply |
| `toCurrency(n)` / `fromCurrency(s)` | Format to `$1,234.56` / parse back to a number |
| `getCell(columnId)` | Current row's value inside a TableColumn formula |
| `getCurrentRowIndex()` | Current row index inside a TableColumn formula |
| `getSequenceId()` | Auto-increment number for Identifier formulas |
| `padStart(str, len, ch)` | Left-pad a string |
| `currentStep()` | Current workflow step id (the substep id inside a parallel step) |
| `getAssignedTo()` | The current assignee |
| `equals(a, b)` / `notEquals(a, b)` | Comparison helpers |
| `isGreaterThan(a, b)` / `isLessThanOrEqualTo(a, b)` | Numeric comparison helpers |
| `or(a, b)` | Logical or helper |
| `isBlank(v)` / `isNotBlank(v)` | Emptiness checks (also for `_reason`) |
| `isRequired(v)` / `isOptional()` | Inside `validate`: require a value, or declare the field optional |
| `today()` / `addDays(n, date)` | Date helpers, common in Datetime `min` and `max` |
| `withinRange(time, '00:00', '06:00')` | Time-of-day range check |
| `getDatasetChildValues(dataset, keyCol, keyVal, wantedCol)` | Dataset lookup; always returns an array |

### Dataset access

```js
formula="Object.keys(schools).sort()"
formula="Object.keys(schools).filter(k => schools[k]['Type'] === 'Site')"
formula="schools[school]['Address']"
formula="budgetCodes[budgetCode]['Approver']['email']"
```

Guard every lookup, since the selector may be empty:

```js
formula="(()=>{
  if (!school) return '';
  const rec = schools[school];
  return rec && rec['principal'] ? rec['principal']['email'] : '';
})()"
```

### Runtime limits and traps

- `new Set()` is not available. Dedupe with `filter((v, i, a) => a.indexOf(v) === i)`.
- Arrays, objects, Math, String, Date, ternaries, template literals, and IIFEs all work.
- `sum()` over a column of `toCurrency(...)` strings can return a string, and `"0.00" + 5` concatenates. Coerce first:
  ```js
  const n = v => parseFloat(String(v).replace(/[^0-9.-]/g, '')) || 0;
  return toCurrency(n(sum(lineTotal)) + n(freight));
  ```
- Computed fields re-evaluate every time the submission is viewed. A value that depends on `new Date()` alone drifts while the submission sits in approvals. Anchor it on a stored Timestamp:
  ```js
  const signed = employeeSignatureDate ? new Date(employeeSignatureDate) : null;
  const now = signed && !isNaN(signed.getTime()) ? signed : new Date();
  ```
- `getDatasetChildValues` returns an array even for one match. A Computed used as `submittedByName` must return a string or submit fails with a generic error:
  ```js
  const v = getDatasetChildValues(staff, 'email', submittedByEmail, 'name');
  const x = Array.isArray(v) ? v[0] : v;
  return x == null ? '' : String(x);
  ```
- A Computed feeding a `<Distance>` endpoint must return one address string.
- A Computed that outputs an HTML string is escaped when interpolated in `<Text>`. Do not try to render markup from a formula.

### Interpolation in Text and notifications

`##fieldId##` inserts the current value. Array access: `##allDates[0]##`. Table cell: `##expenses.0.vendor##`. Do not write `###fieldId##`; put a space between a literal hash and the interpolation.

### Self-approval prevention

When the assignee could be the submitter, route around it in the computed:

```js
formula="(()=>{
  const sup = schools[school] && schools[school]['supervisor'];
  if (!sup) return '';
  if (sup['email'] && submittedByEmail && sup['email'].toLowerCase() === submittedByEmail.toLowerCase()) {
    return schools[school]['director']['email'];
  }
  return sup['email'];
})()"
```

## Validation

### Expression string

```jsx
validate="getCell(drivingAmount) ? getCell(mileage) : true"
validate="sum(amount) === fromCurrency(totalContractValue)"
validate="currentStep() === 'start' ? isOptional() : isRequired(value)"   // required only after start
validate="agreeToTerms === true"                                         // require a Boolean
```

### Conditions object

```jsx
validate={{
  conditions: [{ elementId: "submittedByEmail", comparator: "includes", value: "@district.org" }],
  action: "valid",
}}
```

Two or more conditions need `operator`. Use Datetime `min`/`max` for date bounds instead of `validate`.
