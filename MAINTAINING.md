# Maintaining this package

For whoever keeps the skill current: a Droplet team member, or an AI assistant working in this repo.

## Where things live

| Path | What it is | Ships to customers |
|---|---|---|
| `plugins/droplet-form-creator/skills/droplet-form-creator/` | The skill: `SKILL.md`, `references/`, `scripts/`, `assets/` | Yes (the zip is this folder) |
| `plugins/droplet-form-creator/.claude-plugin/plugin.json` | Plugin manifest, holds the version | Yes |
| `.claude-plugin/marketplace.json` | Lets Claude Code install from this repo | Yes |
| `tools/` | Maintainer scripts: package checks, exemplar refresh, release notes | No |
| `release.sh` | One-command release | No |
| `.github/workflows/` | CI on every push, release build on every tag | No |

## When a new rule, gotcha, or correction is learned

1. Decide where it goes. A rule the assistant must always apply goes into the hard-rules list in `SKILL.md` (keep that list short; it is the part every request loads). Detail, syntax, and examples go into the matching `references/*.md`. Import errors and silent failures also get a row in `references/gotchas.md`.
2. If the rule can be checked mechanically, add a check to `scripts/build_drplt.py` in `lint_form`, and add a case to the negative test in this file's "Testing" section. Errors are for things that break import or fail silently; warnings are for conventions.
3. Run `python3 tools/check_package.py`. It fails on long dashes, an over-long description, a frontmatter mismatch, or an exemplar that no longer lints.
4. Release (below).

Style rules for anything customer-facing: no em or en dashes, sentence-case labels, plain words. The `description` in `SKILL.md` frontmatter must stay at or under 200 characters or claude.ai refuses the upload.

## When Droplet changes

Same path as above. If a component gains or loses a prop, update `references/layout-components.md` and the linter's prop checks. If the archive format changes, update `scripts/build_drplt.py` (`wrap_layout`, `wrap_json_module`, `metadata_module`) and the Appendix in `SKILL.md`, then rebuild the exemplars.

## Adding or replacing an exemplar

Exemplars are generated, never hand-edited. `tools/exemplars.json` lists each one with a `slug`, display `name`, `source` (a folder holding `meta.json` + `docs/`, or a `.drplt`, relative to `sources_root`), `complexity`, a `shows` sentence, and an optional `note`.

```
python3 tools/refresh_exemplars.py
```

The script anonymizes every person (names next to emails, plus any listed in `extra_people`, plus their prose mentions), replaces Apps Script ids and `token=` values with placeholders, zeroes `connectionId`, drops empty secrets, writes `references/exemplars/<slug>/`, builds `assets/exemplars/<name>.drplt`, regenerates the exemplars README, and removes anything no longer listed. It stops if any exemplar fails lint. After running it, scan the output folder for any surname or first name that slipped through and add it to `extra_people`.

Keep the set small and varied. Every exemplar costs the assistant reading time.

## Releasing

```
./release.sh 1.0.1 "Added the Checkbox comparator rule and a lint check for it"
```

This bumps `plugin.json`, adds the line to `CHANGELOG.md`, runs the checks, commits everything pending, tags `v1.0.1`, and pushes. GitHub Actions then re-runs the checks, zips the skill folder, and publishes a release with `droplet-form-creator-skill.zip` attached. The README links customers to the latest release zip, so nothing else needs updating.

Version numbers: bump the last digit for rule additions and fixes, the middle digit for new references or exemplars, the first digit if the skill's process or file layout changes.

## The support article

A support article on support.droplet.io ("Build a form with your AI assistant") introduces the skill and mirrors the Install section of README.md. It is written and published from the support docs CMS, not from this repo. When a release changes an install step, tell whoever maintains that article so its install paragraphs match. Link the article from the README's "Questions and problems" section once it is live.

## How customers receive updates

- Claude Code plugin installs pull from this repo; customers refresh from the `/plugin` menu.
- claude.ai users re-upload the latest zip.
- Everyone who copied the folder re-copies it from the latest release.

Mention notable changes in the changelog line, since that becomes the release note customers read.

## Testing

- `python3 tools/check_package.py` runs every structural check and lints every exemplar.
- The skeleton in `SKILL.md` must build: copy its blocks into a folder and run `scripts/build_drplt.py build`.
- Negative test: build a form with known faults (a Boolean with `required`, `{label, value}` options, two conditions without `operator`, a Checkbox with `includes`, an editable Computed, `sendToSubmitter` inside `template`, a reminder using `assignmentUrl`, an empty `secret`, an element with `id="formId"`, a `<Distance>` with `display={{ action: "alwaysHide" }}`, an `assign` list of 8 entries plus `sendToSubmitter: true`) and confirm each produces an ERROR.
