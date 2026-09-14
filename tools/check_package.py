#!/usr/bin/env python3
"""
check_package.py - validate the package before a commit or release. Exits 1 on any problem.

Checks: manifests parse and agree, SKILL.md frontmatter is valid for every host (name matches the
folder, description within 200 characters), no long dashes in authored Markdown, every exemplar has
its files and lints with zero errors, every exemplar has a built .drplt asset, and no real email
addresses, empty secrets, or live script ids remain in the exemplars.
"""
import importlib.util
import json
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "droplet-form-creator"
SKILL = PLUGIN / "skills" / "droplet-form-creator"
problems = []


def problem(msg):
    problems.append(msg)
    print("  PROBLEM  " + msg)


spec = importlib.util.spec_from_file_location("build_drplt", SKILL / "scripts" / "build_drplt.py")
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)

# manifests
try:
    mp = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    entry = next((p for p in mp.get("plugins", []) if p.get("name") == "droplet-form-creator"), None)
    if not entry:
        problem("marketplace.json has no droplet-form-creator plugin entry")
    elif not (ROOT / entry["source"]).is_dir():
        problem("marketplace.json source path does not exist: {}".format(entry["source"]))
except Exception as ex:
    problem("marketplace.json: {}".format(ex))
try:
    pj = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if pj.get("name") != "droplet-form-creator":
        problem("plugin.json name must be droplet-form-creator")
    version = pj.get("version", "")
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        problem("plugin.json version must look like 1.2.3")
except Exception as ex:
    problem("plugin.json: {}".format(ex))
    version = ""

# changelog agrees with the plugin version
changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") if (ROOT / "CHANGELOG.md").exists() else ""
m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)
if not m:
    problem("CHANGELOG.md has no '## [x.y.z]' section")
elif version and m.group(1) != version:
    problem("CHANGELOG.md top version {} does not match plugin.json version {}".format(m.group(1), version))

# skill frontmatter
skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
fm = re.match(r"^---\n(.*?)\n---\n", skill_md, re.S)
if not fm:
    problem("SKILL.md has no YAML frontmatter")
else:
    fields = dict(re.findall(r"^([a-z_-]+):\s*(.*)$", fm.group(1), re.M))
    if fields.get("name") != SKILL.name:
        problem("SKILL.md name '{}' must equal the folder name '{}'".format(fields.get("name"), SKILL.name))
    desc = fields.get("description", "")
    if not desc:
        problem("SKILL.md description is missing")
    elif len(desc) > 200:
        problem("SKILL.md description is {} characters; claude.ai allows 200".format(len(desc)))
lines = skill_md.count("\n")
if lines > 400:
    print("  note     SKILL.md is {} lines; keep it lean and push detail into references/".format(lines))

# long dashes in authored markdown
for md in [SKILL / "SKILL.md", ROOT / "README.md", ROOT / "MAINTAINING.md", ROOT / "CHANGELOG.md"] + sorted((SKILL / "references").glob("*.md")) + [SKILL / "references" / "exemplars" / "README.md"]:
    if md.exists():
        text = md.read_text(encoding="utf-8")
        for i, line in enumerate(text.split("\n"), 1):
            if "—" in line or "–" in line:
                problem("{}:{} contains a long dash".format(md.relative_to(ROOT), i))

# exemplars
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
cfg = json.loads((ROOT / "tools" / "exemplars.json").read_text(encoding="utf-8"))
keep = tuple(d.lower() for d in cfg.get("keep_domains", []))
ex_dir = SKILL / "references" / "exemplars"
asset_dir = SKILL / "assets" / "exemplars"
for ex in cfg["exemplars"]:
    d = ex_dir / ex["slug"]
    if not d.is_dir():
        problem("exemplar folder missing: {}".format(d.relative_to(ROOT)))
        continue
    lint = bd.Lint()
    meta, docs, data = bd.load_form_dir(str(d), lint)
    bd.lint_form(meta, docs, data, lint)
    if lint.errors:
        for where, msg in lint.errors:
            problem("{} {}: {}".format(ex["slug"], where, msg))
    asset = asset_dir / (ex["name"] + ".drplt")
    if not asset.exists():
        problem("built asset missing: {}".format(asset.relative_to(ROOT)))
    else:
        with zipfile.ZipFile(asset) as z:
            names = set(z.namelist())
            for need in ["meta.json", "docs/layout.txt", "import/layout.jsx", "import/metadata.js", "import/package.json"]:
                if need not in names:
                    problem("{} lacks {}".format(asset.name, need))
    for f in sorted(d.rglob("*")):
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="replace")
            for e in set(EMAIL.findall(text)):
                if not e.lower().endswith(keep):
                    problem("{} contains a non-placeholder email: {}".format(f.relative_to(ROOT), e))
            if '"secret": ""' in text:
                problem("{} contains an empty secret".format(f.relative_to(ROOT)))
            if re.search(r"script\.google\.com/macros/s/AK", text):
                problem("{} contains a live Apps Script id".format(f.relative_to(ROOT)))
for d in ex_dir.iterdir():
    if d.is_dir() and d.name not in {ex["slug"] for ex in cfg["exemplars"]}:
        problem("exemplar folder not in tools/exemplars.json: {}".format(d.name))

print("check_package: {} problem(s)".format(len(problems)))
sys.exit(1 if problems else 0)
