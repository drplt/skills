# droplet-forms evals

Eval cases for the `droplet-form-creator` skill, run with `claude plugin eval`. Each case hands the skill one plain-language request from a made-up district, lets it build (or revise) a form, and grades the files it wrote plus its handoff message. Nothing is imported into Droplet: the harness runs the skill's own build script, which lints first and only writes the `.drplt` when there are 0 errors.

## Run

From the repo root (needs Claude Code with `claude plugin eval`):

```
# The whole suite, 3 runs per case: about 15 minutes and $15 to $20
claude plugin eval plugins/droplet-forms --tag frozen --scaffold --ablation none \
  --allow-tools Bash Write Edit --runs 3 -j 4

# One case, keeping its sandbox to inspect what it built
claude plugin eval plugins/droplet-forms --case revise-live-form --scaffold --ablation none \
  --allow-tools Bash Write Edit --runs 1 --keep-temp
```

- `--scaffold` runs a case's `scaffold.sh`. Only `revise-live-form` has one: it builds the fixture form in `_fixtures/` into an exported `.drplt` for the skill to edit.
- `--ablation none` skips the no-plugin comparison arm. Without the skill there is nothing to build, so that arm mostly measures noise. Run it now and then to check the skill still triggers.
- Each case defaults to 1 run. Use `--runs 3` before a release or when deciding whether a change helped, since single runs vary.
- Add `--max-cost-usd 30` if you want a hard spending cap.
- Results land in `evals/results/<timestamp>/` (gitignored) with an HTML report.

## The cases

| Case | Tags | What it checks |
|---|---|---|
| `identifier-not-formid` | regression | The user asks for an auto number named `formId`. The skill picks another id, the build is clean, and the handoff explains the rename (v1.0.1) |
| `mileage-distance-visible` | regression | A one-trip mileage form keeps the Distance visible while addresses are entered, and derives round trip miles and dollars in Computeds (v1.0.3) |
| `revise-live-form` | regression, revision | Changes to a form already live in Droplet: the handoff says to paste the changed modules into the existing form and lists them, never to re-import (v1.0.2) |
| `nine-processors-cap` | regression | Nine registrars, any one can act: no step goes past 8 assignees, and the handoff explains the limit (v1.0.4) |
| `everyone-must-approve-parallel` | regression | Three people must each sign off: a parallel step with one substep each, not a group assign (v1.0.4) |
| `ack-checkbox-not-required-boolean` | gotcha | A must-tick agreement box is enforced without `required` on a Boolean |
| `coded-dropdown-options` | gotcha | A grade dropdown stores codes with single-pair options (no `{ label, value }`), and a two-condition display rule sets `operator` |
| `webhook-no-empty-secret` | gotcha | A webhook with no signing secret omits `secret` (never `""`), and the handoff warns that the connection must be set up in Droplet |
| `field-trip-conditional-approval` | everyday | Principal by school, Assistant Superintendent only for overnight or out of state, Transportation only for a district bus, computed total |
| `purchase-request-thresholds` | everyday | Line items with a computed grand total; approvals over $5,000 and $25,000 compare numbers, not currency text |
| `facility-use-computed-fee` | everyday | Fee from hours, space rate, and a nonprofit discount; a policy button; principal by building, then Facilities Director |
| `any-one-of-group-assignment` | everyday | Three HR assistants share one step through a group assign, not a parallel step |

Every case also checks: the skill fired, the build ended with 0 lint errors and wrote `out/form.drplt`, no em or en dashes in the layout, and no tooling words in the handoff (`lint`, `python`, script names, `nameElementId`, `onSubmit`, and similar).

All cases are tagged `frozen`. The skill never reads the web, so there are no `live` cases; if one is added later (for example, building from a district's real PDF), tag it `live` and keep it out of the release check.

How a case runs: each `prompt.md` appends a short harness note to the system prompt. It tells the agent nobody can answer questions, to write the form into `./out/form`, to build it with `-o out/form.drplt` without `--skip-lint`, and to keep the test setup out of the handoff. Graders read the files in `out/form/docs/`, the trace (for the lint result and the skill call), and the final message.

## Fixtures

Every district, person, and email in the prompts and graders is made up (`*.example.org`), so the answer keys never go stale and nothing private lands in this public repo. `_fixtures/harbor-point-field-trip/` is the form `revise-live-form` starts from. If you change a fixture or a prompt, update the graders that describe it.

## Hill-climbing

1. Run the suite with `--runs 3` to get a baseline.
2. Change one thing in the skill, usually the top failure from the last report.
3. Re-run. Keep the change if the total goes up and nothing that passed before starts failing.
4. Turn each new real-world failure into a case. Every line in `CHANGELOG.md` that fixes a rule should have a regression case here.

## Known quirks

- When `claude plugin eval` runs as root on Linux, the sandbox makes the working directory read-only for Bash, so the build cannot write the `.drplt` and `built` fails. Run as a normal user.
- An `llm` judge reads text only, so graders grade the `docs/*.txt` files, never the zipped `.drplt`.
- The `lint-clean` grader passes when the last lint report in the trace shows 0 errors. Edits made after that last build are not re-checked.
