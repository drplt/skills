#!/usr/bin/env python3
"""Print the CHANGELOG.md section for a version tag (v1.2.3 or 1.2.3) as release notes."""
import pathlib
import re
import sys

tag = sys.argv[1] if len(sys.argv) > 1 else ""
version = tag.lstrip("v")
text = (pathlib.Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
m = re.search(r"^## \[{}\][^\n]*\n(.*?)(?=^## \[|\Z)".format(re.escape(version)), text, re.M | re.S)
body = m.group(1).strip() if m else "See CHANGELOG.md."
print(body)
print("\nInstall and update instructions: see README.md. The attached zip is the claude.ai upload.")
