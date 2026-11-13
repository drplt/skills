#!/usr/bin/env bash
# Cut a release: bumps the version, records the changelog line, commits, tags, and pushes.
# GitHub Actions then validates the package, builds the claude.ai zip, and publishes the release.
#
#   ./release.sh 1.0.1 "Added the Checkbox comparator rule and a lint check for it"
#
# Any uncommitted edits are included in the release commit.
set -euo pipefail
VERSION="${1:?usage: ./release.sh <x.y.z> \"<what changed>\"}"
SUMMARY="${2:?usage: ./release.sh <x.y.z> \"<what changed>\"}"
cd "$(dirname "$0")"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "version must look like 1.2.3"; exit 1; }
git rev-parse "v$VERSION" >/dev/null 2>&1 && { echo "tag v$VERSION already exists"; exit 1; }

python3 - "$VERSION" "$SUMMARY" <<'PY'
import json, pathlib, re, sys, datetime
version, summary = sys.argv[1], sys.argv[2]
pj = pathlib.Path("plugins/droplet-forms/.claude-plugin/plugin.json")
data = json.loads(pj.read_text()); data["version"] = version
pj.write_text(json.dumps(data, indent=2) + "\n")
cl = pathlib.Path("CHANGELOG.md"); text = cl.read_text()
if "## [{}]".format(version) not in text:
    entry = "## [{}] - {}\n- {}\n\n".format(version, datetime.date.today().isoformat(), summary)
    text = re.sub(r"^(# Changelog\n\n)", r"\1" + entry.replace("\\", "\\\\"), text, count=1, flags=re.M)
    cl.write_text(text)
print("version {} written to plugin.json and CHANGELOG.md".format(version))
PY

python3 tools/check_package.py
git add -A
git commit -m "Release v$VERSION: $SUMMARY" || true
git tag -a "v$VERSION" -m "v$VERSION: $SUMMARY"
git push origin HEAD
git push origin "v$VERSION"
echo
echo "Pushed. The Release workflow is building the zip and publishing:"
echo "  https://github.com/drplt/skills/releases/tag/v$VERSION"
echo "Watch it with: gh run watch"
