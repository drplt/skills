# Droplet Form Creator Skill

An AI skill that builds and edits Droplet Forms and Workflows files (`.drplt`) from a plain-language description of a form and its approval process. Give your AI assistant a request like "Build a field trip request form that goes to the principal, then the transportation office, and emails the teacher when approved," and it produces a `.drplt` file you import into Droplet.

The skill works in Claude Code, claude.ai, OpenAI Codex, GitHub Copilot, Gemini CLI, Cursor, and any assistant that accepts pasted instructions.

## What is inside

The skill folder is `plugins/droplet-form-creator/skills/droplet-form-creator/`. Everything else in this repository is packaging.

| Path | Purpose |
|---|---|
| `SKILL.md` | The instructions the assistant follows: the file format, the build process, and the rules that keep a form importable. |
| `references/` | Detailed reference for each part of a form: layout components, display logic and formulas, workflow and permissions, notifications, datasets and integrations, and a consolidated list of gotchas. |
| `references/exemplars/` | Eight complete example forms as readable text, from a component showcase to district forms with parallel review, dataset-driven routing, and webhooks. |
| `assets/exemplars/` | The same forms as ready-to-import `.drplt` files. Import one into Droplet to see how it looks and behaves. |
| `scripts/build_drplt.py` | A dependency-free Python 3 script that lints a form for common import failures, builds the `.drplt` archive, or extracts an existing one for editing. |

## Install

### Claude Code

Install as a plugin, which also gives you updates:

```
/plugin marketplace add drplt/droplet-form-creator
/plugin install droplet-form-creator@droplet-forms
```

Or copy the skill folder into a project (`.claude/skills/`) or your personal skills folder (`~/.claude/skills/`). Then ask for a form. Claude Code loads the skill when a request mentions Droplet forms or `.drplt` files.

### Claude.ai (web and desktop)

1. Download the zip from the latest release: <https://github.com/drplt/droplet-form-creator/releases/latest/download/droplet-form-creator-skill.zip>
2. In Claude, open Customize, then Skills, then Create skill, then Upload a skill, and choose the zip.
3. Code execution must be on under Settings, then Capabilities. Team and Enterprise admins enable skills under Organization settings. With it on, Claude runs the build script itself and hands you the finished `.drplt` to download.

### OpenAI Codex, GitHub Copilot, Gemini CLI, and Cursor

These tools read the same skill format from a shared folder:

```
git clone https://github.com/drplt/droplet-form-creator.git
mkdir -p .agents/skills
cp -R droplet-form-creator/plugins/droplet-form-creator/skills/droplet-form-creator .agents/skills/
```

Tool-specific locations also work: `.github/skills/` for Copilot, `.gemini/skills/` for Gemini CLI, `.cursor/skills/` for Cursor. Codex invokes skills with `$droplet-form-creator`, Cursor from the `/` menu, Copilot and Gemini CLI automatically.

### ChatGPT and Gemini apps

- ChatGPT on Business, Enterprise, or Edu plans: upload the zip under Plugins, then Skills, then Create. On other plans, create a Custom GPT: paste `SKILL.md` into the instructions (trim if you hit the length limit) and attach the `references/*.md` files and one exemplar's `docs/*.txt` files as knowledge.
- Gemini: create a Gem. Paste `SKILL.md` as the instructions and attach the reference files as knowledge.

These assistants cannot run the build script, so ask for the `meta.json` and `docs/` text files, then build the archive yourself:

```
python3 scripts/build_drplt.py build "My Form Folder"
```

### Any other assistant

Paste `SKILL.md` and the relevant reference files into the conversation, or attach them. They are plain Markdown.

## Using the finished file

1. In Droplet, open Forms, then Import, and choose the `.drplt` file.
2. Replace the placeholders the assistant listed in its handoff: dataset ids, approver names and emails, the logo image, and any webhook connection.
3. Open the form in the editor, run the workflow tester, and publish when satisfied.
4. For later changes, do not import again: an import creates a second form with a new link. Open the existing form in the editor and paste each changed `docs/*.txt` file into the matching code view, in this order: layout, workflow, steps, notifications, then datasets, attributes, and tag expressions if they changed.

## Building and editing by hand

```
python3 scripts/build_drplt.py lint    "My Form Folder"       # check for import problems
python3 scripts/build_drplt.py build   "My Form Folder"       # lint, then produce My Form.drplt
python3 scripts/build_drplt.py extract "Existing Form.drplt"  # unpack for editing
```

A form folder holds `meta.json` and a `docs/` directory with nine text files. `SKILL.md` shows the layout of each.

## Staying current

The skill improves as Droplet changes and as new import rules are learned. Each change is a release with a changelog line.

- Claude Code plugin: open `/plugin`, choose the `droplet-forms` marketplace, and update.
- claude.ai: download the latest zip from the link above and upload it again.
- Copied folders: re-copy from the latest release.

Watch or star this repository to hear about releases.

## Questions and problems

Open an issue on this repository, or contact your Droplet customer experience contact. If Droplet reports an import error the assistant did not anticipate, paste the error back into the conversation; the skill usually recognizes the pattern from its gotchas reference, and the report helps the next release.

## Notes

- The example forms use fictional people and `example.org` addresses. District names and branding were kept so the forms read as real. Logo images point at placeholder assets; upload your own in the Droplet editor.
- Dataset ids inside the examples belong to the workspace each form came from. Point them at datasets in your own workspace after importing.
