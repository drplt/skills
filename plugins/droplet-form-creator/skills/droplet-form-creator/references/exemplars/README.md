# Exemplar forms

Complete forms, each as `meta.json` plus the nine `docs/*.txt` files. The same forms are packaged as importable `.drplt` archives in `assets/exemplars/`. Study the one closest in complexity to the request before writing.

| Folder | What it shows | Complexity |
|---|---|---|
| `component-library/` | Every basic component with minimal props on a single-step form. Read first if the layout syntax is new. | Low |
| `building-use-request/` | One approval step, dataset-driven dropdowns, profile auto-fill through attributes, a validate conditions object, a hidden section of computed fields, and a sheet integration on completed. | Medium |
| `peekskill-facilities-request/` | Sequential superintendent, athletic director, and theater reviews, each able to send the request back to start or reject it, then a request-entry step assigned per building from a dataset through a legacy expression assign, with a full set of notification emails. | High |
| `avon-incident-report/` | A public form with no login, banner tiles per section, an Identifier, a dataset dropdown with an appended option, date min and max rules, one review step with its own Actions bar, and an FYI notification with the submission PDF attached. | Medium |
| `avon-mileage-reimbursement/` | Two trip tables with distance columns, a per-row mileage rate looked up by effective date, a principal step skipped through onEnter.if when no principal exists, two static approvers, reject to terminal, notifications carrying the reject reason, and a print view built with View wrappers and mirrored read-only tables. | High |
| `avon-student-registration/` | A long community-facing registration form: a grade selector that computes the school, sections gated by grade and gender, Checkbox tiles for health history, two signatures, registrar review, then parallel nurse and transportation substeps with the nurse assigned per building from a dataset. Drafted from a district's paper packet and not yet imported at the time of packaging; treat it as a pattern reference. | High |
| `avon-instructional-extra-work/` | One form that reshapes itself from a type-of-work selector: sessions tables or a pay-period grid, fiscal-year rate lookups, a pay calendar dataset, a running hours ledger read from a dataset with per-year buckets, a chain of up to five approvers with per-step skip flags, a frozen expected pay date anchored on the signature timestamp, and outbound webhooks on start and rejected that write the ledger back. Webhook endpoints, tokens, and connection ids are placeholders; the ledger write-back needs an external script. | Very high |
| `conference-expense-report/` | Multi-table expense math with getCell and sum, a date-range generator, per-diem lookups from datasets, mileage through Distance, dynamic approver assignment with self-approval prevention, onEnter.if to skip steps, hidden computed sections, and return-to-submitter routing. | High |

## Reading notes

- Forms exported from Droplet carry a `resolved` block in `datasets.txt`: a snapshot of rows Droplet writes on export so previews render. New forms should reference datasets by `datasetId` and omit `resolved`.
- Some exported forms list permission ids that no longer exist in the layout. Droplet ignores them. Do not copy the habit.
- Dataset ids belong to the workspace the form came from. After importing an exemplar, point each dataset at one in your own workspace.
- Every person is fictional (`example.org` addresses) and every webhook endpoint, token, and connection id is a placeholder. District names, addresses, and branding were kept so the forms read as real.
- Distance fields and columns must be editable in the step where their addresses are entered, which is why some appear editable in `start`. Identifiers are normally readonly.
