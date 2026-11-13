#!/usr/bin/env python3
"""
refresh_exemplars.py - rebuild the skill's exemplar forms from their source files.

Reads tools/exemplars.json. For each entry it loads the source form (a folder holding
meta.json + docs/, or a .drplt archive), anonymizes people and secrets, writes
references/exemplars/<slug>/ (meta.json + docs/), builds assets/exemplars/<Name>.drplt
through the skill's own build script (lint must pass), and regenerates
references/exemplars/README.md. Exemplars no longer in the config are removed.

Run from anywhere:  python3 tools/refresh_exemplars.py
"""
import importlib.util
import json
import pathlib
import re
import shutil
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "droplet-forms" / "skills" / "droplet-form-creator"
CONFIG = ROOT / "tools" / "exemplars.json"
REF_DIR = SKILL / "references" / "exemplars"
ASSET_DIR = SKILL / "assets" / "exemplars"

spec = importlib.util.spec_from_file_location("build_drplt", SKILL / "scripts" / "build_drplt.py")
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)

FIRST = ["Avery", "Jordan", "Casey", "Riley", "Morgan", "Taylor", "Quinn", "Reese", "Dakota", "Emerson",
         "Harper", "Rowan", "Sawyer", "Skyler", "Blake", "Finley", "Hayden", "Kendall", "Marlow", "Parker",
         "Peyton", "Sage", "Tatum", "Wren", "Ellis", "Devin", "Lane", "Remy", "Shiloh", "Arden"]
LAST = ["Whitfield", "Okafor", "Lindqvist", "Marchetti", "Castellano", "Nakamura", "Delacroix", "Abernathy",
        "Vasquez", "Holloway", "Kowalski", "Brennan", "Fontaine", "Ashworth", "Ferreira", "Thornbury",
        "Halvorsen", "Ramsay", "Ingram", "Salazar", "Beaumont", "Caldwell", "Donovan", "Espinoza", "Galloway",
        "Hartigan", "Iverson", "Kingsley", "Lachlan", "Montague"]
# first names that are also ordinary words; never replaced on their own
FIRST_NAME_STOPLIST = {"grant", "lane", "mark", "bill", "will", "may", "april", "june", "hope", "faith", "joy",
                       "chase", "forest", "rose", "sky", "ray", "art", "gene", "guy", "pat", "sue", "dawn",
                       "summer", "autumn", "penny", "chip", "rich", "frank", "bob", "jack", "max", "pearl"}
# surnames that are also ordinary words or place names; never replaced on their own
LAST_NAME_STOPLIST = {"smith", "brown", "green", "white", "black", "young", "little", "north", "south", "field",
                      "church", "house", "banks", "wells", "woods", "stone", "lane", "grant", "price", "rose",
                      "baker", "cook", "miller", "taylor", "mason", "walker", "hunter", "fisher", "carter"}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class Anonymizer:
    def __init__(self, keep_domains, extra_people):
        self.keep = tuple(d.lower() for d in keep_domains)
        self.people = {}      # original email (lower) -> (fake name, fake email)
        self.names = {}       # original full name -> fake full name
        for n in extra_people:
            self.names[n] = self._fresh_name()

    def _fresh_name(self):
        i = len(self.people) + len(self.names)
        return "{} {}".format(FIRST[i % len(FIRST)], LAST[(i // len(FIRST) + i) % len(LAST)])

    def fake(self, email):
        key = email.lower()
        if key not in self.people:
            name = self._fresh_name()
            self.people[key] = (name, name.lower().replace(" ", ".") + "@example.org")
        return self.people[key]

    def learn(self, obj):
        """Pre-pass: remember real names that sit next to an email so prose mentions get replaced too."""
        if isinstance(obj, dict):
            e, n = obj.get("email"), obj.get("name")
            if isinstance(e, str) and e.strip() and isinstance(n, str) and n.strip() and not e.lower().endswith(self.keep):
                self.names[n.strip()] = self.fake(e)[0]
            for v in obj.values():
                self.learn(v)
        elif isinstance(obj, list):
            for v in obj:
                self.learn(v)

    def text(self, s):
        s = EMAIL.sub(lambda m: m.group(0) if m.group(0).lower().endswith(self.keep) else self.fake(m.group(0))[1], s)
        s = re.sub(r"https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec",
                   "https://script.google.com/macros/s/REPLACE_WITH_YOUR_SCRIPT_ID/exec", s)
        s = re.sub(r"([?&]token=)[^&\"' ]+", r"\1REPLACE_ME", s)
        s = s.replace("@droplet.io", "@example.com")
        return s

    def names_pass(self, s):
        for full, fk in sorted(self.names.items(), key=lambda kv: -len(kv[0])):
            s = re.sub(r"\b" + re.escape(full) + r"\b", fk, s)
            first, ffirst = full.split()[0], fk.split()[0]
            last, flast = full.split()[-1], fk.split()[-1]
            if len(first) >= 4 and first.lower() not in FIRST_NAME_STOPLIST:
                s = re.sub(r"\b" + re.escape(first) + r"\b", ffirst, s)
            if len(last) >= 5 and last.lower() not in LAST_NAME_STOPLIST:
                s = re.sub(r"\b" + re.escape(last) + r"\b", flast, s)
        return s

    def walk(self, obj, path=""):
        if isinstance(obj, dict):
            out = {}
            if "email" in obj and "name" in obj and isinstance(obj.get("email"), str) and obj["email"].strip() \
                    and not obj["email"].lower().endswith(self.keep):
                n, e = self.fake(obj["email"])
                obj = dict(obj)
                obj["name"], obj["email"] = n, e
            for k, v in obj.items():
                if k == "connectionId" and isinstance(v, int):
                    out[k] = 0
                elif k == "secret" and v == "":
                    continue
                else:
                    out[k] = self.walk(v, path + "." + k)
            return out
        if isinstance(obj, list):
            return [self.walk(x, path) for x in obj]
        if isinstance(obj, str):
            return self.text(obj)
        return obj


def load_source(path):
    """Return (meta, docs) from a folder or a .drplt archive."""
    if path.is_dir():
        meta = json.loads((path / "meta.json").read_text(encoding="utf-8"))
        docs = {m: (path / "docs" / (m + ".txt")).read_text(encoding="utf-8") for m in bd.ALL_DOCS}
        return meta, docs
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        docs = {m: z.read("docs/{}.txt".format(m)).decode("utf-8") for m in bd.ALL_DOCS if "docs/{}.txt".format(m) in names}
        for m in bd.ALL_DOCS:
            docs.setdefault(m, "{}\n" if m != "layout" else "")
        if "meta.json" in names:
            meta = json.loads(z.read("meta.json").decode("utf-8"))
        else:
            js = z.read("import/metadata.js").decode("utf-8")
            m = json.loads(js[js.index("{"): js.index("};") + 1])
            meta = {"version": 1, "form": {"name": m.get("name", ""), "description": m.get("description", ""),
                                            "loginRequired": m.get("loginRequired", False),
                                            "submitAsLoggedIn": m.get("submitAsLoggedIn", False)}}
        return meta, docs


def dumps(o):
    return json.dumps(o, indent=2, ensure_ascii=False) + "\n"


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    sources_root = (ROOT / cfg.get("sources_root", "..")).resolve()
    anon = Anonymizer(cfg.get("keep_domains", []), cfg.get("extra_people", []))
    loaded = []
    for ex in cfg["exemplars"]:
        src = sources_root / ex["source"]
        if not src.exists():
            sys.exit("source not found: {}".format(src))
        meta, docs = load_source(src)
        loaded.append((ex, meta, docs))
        for m in bd.JSON_MODULES:
            try:
                anon.learn(json.loads(docs[m]))
            except json.JSONDecodeError:
                pass
    wanted_slugs = {ex["slug"] for ex in cfg["exemplars"]}
    wanted_assets = {ex["name"] + ".drplt" for ex in cfg["exemplars"]}
    REF_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for d in REF_DIR.iterdir():
        if d.is_dir() and d.name not in wanted_slugs:
            shutil.rmtree(d)
            print("removed", d.relative_to(ROOT))
    for f in ASSET_DIR.glob("*.drplt"):
        if f.name not in wanted_assets:
            f.unlink()
            print("removed", f.relative_to(ROOT))
    failures = 0
    for ex, meta, docs in loaded:
        dst = REF_DIR / ex["slug"]
        if dst.exists():
            shutil.rmtree(dst)
        (dst / "docs").mkdir(parents=True)
        meta = anon.walk(meta)
        (dst / "meta.json").write_text(anon.names_pass(dumps(meta)), encoding="utf-8")
        for m in bd.ALL_DOCS:
            if m == "layout":
                out = anon.text(docs[m]).rstrip("\n") + "\n"
            else:
                out = dumps(anon.walk(json.loads(docs[m])))
            (dst / "docs" / (m + ".txt")).write_text(anon.names_pass(out), encoding="utf-8")
        asset = ASSET_DIR / (ex["name"] + ".drplt")
        print("== {} ({})".format(ex["name"], ex["slug"]))
        rc = bd.build(str(dst), str(asset), skip_lint=False)
        if rc != 0:
            failures += 1
    write_readme(cfg)
    print("\n{} people anonymized, {} names learned".format(len(anon.people), len(anon.names)))
    if failures:
        sys.exit("{} exemplar(s) failed to build; fix the errors above".format(failures))


def write_readme(cfg):
    lines = ["# Exemplar forms", "",
             "Complete forms, each as `meta.json` plus the nine `docs/*.txt` files. The same forms are packaged as importable `.drplt` archives in `assets/exemplars/`. Study the one closest in complexity to the request before writing.",
             "", "| Folder | What it shows | Complexity |", "|---|---|---|"]
    for ex in cfg["exemplars"]:
        note = " " + ex["note"] if ex.get("note") else ""
        lines.append("| `{}/` | {}{} | {} |".format(ex["slug"], ex["shows"], note, ex["complexity"]))
    lines += ["", "## Reading notes", "",
              "- Forms exported from Droplet carry a `resolved` block in `datasets.txt`: a snapshot of rows Droplet writes on export so previews render. New forms should reference datasets by `datasetId` and omit `resolved`.",
              "- Some exported forms list permission ids that no longer exist in the layout. Droplet ignores them. Do not copy the habit.",
              "- Dataset ids belong to the workspace the form came from. After importing an exemplar, point each dataset at one in your own workspace.",
              "- Every person is fictional (`example.org` addresses) and every webhook endpoint, token, and connection id is a placeholder. District names, addresses, and branding were kept so the forms read as real.",
              "- Distance fields and columns must be editable in the step where their addresses are entered, which is why some appear editable in `start`. Identifiers are normally readonly.",
              ""]
    (REF_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", (REF_DIR / "README.md").relative_to(ROOT))


if __name__ == "__main__":
    main()
