#!/usr/bin/env python3
"""
build_drplt.py - build, extract, and lint Droplet ".drplt" form archives.

A .drplt file is a zip containing:
  meta.json                 form name, description, login settings
  docs/<module>.txt         plain JSON (or bare JSX for layout.txt)
  import/<module>.js        the same data wrapped as a JS module export
  import/layout.jsx         the layout wrapped as  const layout = () => ( ... )
  import/metadata.js        metadata module derived from meta.json
  import/package.json       { "name": "@drplt/form-<sha256>", "type": "module" }

You author ONLY meta.json and the docs/ text files. This script derives the
import/ half, lints the form for the most common import and runtime failures,
and zips everything into a .drplt.

Usage:
  python3 build_drplt.py build   <form-dir> [-o "Output Name.drplt"] [--skip-lint]
  python3 build_drplt.py lint    <form-dir>
  python3 build_drplt.py extract <file.drplt> [-o <out-dir>]

<form-dir> layout:
  meta.json
  docs/layout.txt  docs/workflow.txt  docs/steps.txt  docs/notifications.txt
  docs/datasets.txt  docs/attributes.txt  docs/tagExpressions.txt
  docs/translations.txt  docs/integrations.txt

No third-party dependencies. Python 3.8+.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import zipfile

JSON_MODULES = ["workflow", "steps", "notifications", "datasets", "attributes",
                "tagExpressions", "translations", "integrations"]
ALL_DOCS = ["layout"] + JSON_MODULES

RESERVED_ID_ERROR = {"formId"}
RESERVED_ID_WARN = {"formName", "submissionId", "submissionUrl", "assignmentUrl", "recipientFirstName",
                    "recipientLastName", "recipientFullName", "recipientEmail", "initiatedByFullName",
                    "initiatedByFirstName", "initiatedByEmail", "_reason"}

INPUT_TYPES = {"Input", "Textarea", "Dropdown", "Radio", "Checkbox", "Boolean", "Datetime", "Signature",
               "Upload", "Address", "Table", "TableColumn"}
STRUCTURAL = {"Section", "Tile", "Group", "Text", "Image", "Spacer", "Line", "Pagebreak", "Table"}
NO_PERMISSIONS = {"Html", "Actions", "View", "Form"}
PERMISSION_VALUES = {"editable", "readonly", "hidden", "redacted"}
CONTAINERS = {"Form", "Section", "Tile", "Group", "Table", "Text", "Html", "View", "Actions"}
TEXT_STYLE_OK = {"color", "fontSize", "fontFamily", "textAlign", "fontWeight", "backgroundColor"}
SYSTEM_TEMPLATE_VARS = {"recipientFirstName", "initiatedByFullName", "submissionUrl", "assignmentUrl",
                        "_reason", "link", "notificationUrl", "recipientFullName", "initiatedByFirstName"}
EM_DASH = "—"
EN_DASH = "–"


# ----------------------------------------------------------------------------
# JSX scanning (regex-free tag walker that tolerates formulas in attributes)
# ----------------------------------------------------------------------------

def parse_attrs(text):
    """Parse a JSX attribute region into {name: ('str', v) | ('expr', v) | True}."""
    attrs = {}
    i, n = 0, len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        if text.startswith("{/*", i):
            end = text.find("*/}", i)
            i = n if end < 0 else end + 3
            continue
        m = re.match(r"[A-Za-z_][\w\-]*", text[i:])
        if not m:
            i += 1
            continue
        name = m.group(0)
        i += m.end()
        j = i
        while j < n and text[j].isspace():
            j += 1
        if j < n and text[j] == "=":
            j += 1
            while j < n and text[j].isspace():
                j += 1
            if j < n and text[j] == '"':
                k = text.find('"', j + 1)
                if k < 0:
                    k = n
                attrs[name] = ("str", text[j + 1:k])
                i = k + 1
            elif j < n and text[j] == "{":
                depth, quote, k = 0, None, j
                while k < n:
                    c = text[k]
                    if quote:
                        if c == "\\":
                            k += 2
                            continue
                        if c == quote:
                            quote = None
                    elif c in "\"'`":
                        quote = c
                    elif c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                attrs[name] = ("expr", text[j + 1:k])
                i = k + 1
            else:
                attrs[name] = True
                i = j
        else:
            attrs[name] = True
    return attrs


def scan_tags(src):
    """Return a list of uppercase JSX tags in document order.

    Each tag: {name, closing, self_closing, attrs, start, end, line}
    """
    tags = []
    i, n = 0, len(src)
    while True:
        j = src.find("<", i)
        if j < 0:
            break
        m = re.match(r"</([A-Z][A-Za-z0-9]*)\s*>", src[j:])
        if m:
            tags.append({"name": m.group(1), "closing": True, "self_closing": False,
                         "attrs": {}, "start": j, "end": j + m.end()})
            i = j + m.end()
            continue
        m = re.match(r"<([A-Z][A-Za-z0-9]*)(?=[\s/>])", src[j:])
        if not m:
            i = j + 1
            continue
        name = m.group(1)
        k = j + m.end()
        attr_start = k
        depth, quote = 0, None
        while k < n:
            c = src[k]
            if quote:
                if depth > 0 and c == "\\":
                    k += 2
                    continue
                if c == quote:
                    quote = None
                k += 1
                continue
            if depth == 0:
                if c == '"':
                    quote = '"'
                elif c == "{":
                    depth = 1
                elif c == ">":
                    break
                k += 1
            else:
                if src.startswith("/*", k):
                    end = src.find("*/", k + 2)
                    k = n if end < 0 else end + 2
                    continue
                if c in "\"'`":
                    quote = c
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                k += 1
        attrs_text = src[attr_start:k]
        self_closing = attrs_text.rstrip().endswith("/")
        if self_closing:
            attrs_text = attrs_text.rstrip()[:-1]
        tags.append({"name": name, "closing": False, "self_closing": self_closing,
                     "attrs": parse_attrs(attrs_text), "start": j, "end": k + 1})
        i = k + 1
    line_starts = [0] + [m.end() for m in re.finditer(r"\n", src)]
    for t in tags:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= t["start"]:
                lo = mid
            else:
                hi = mid - 1
        t["line"] = lo + 1
    return tags


def build_tree(tags):
    """Attach parent chain info to each opening tag. Returns list of element dicts."""
    stack = []
    elements = []
    for t in tags:
        if t["closing"]:
            for idx in range(len(stack) - 1, -1, -1):
                if stack[idx]["name"] == t["name"]:
                    del stack[idx:]
                    break
            continue
        el = dict(t)
        el["parents"] = [s["name"] for s in stack]
        el["parent_ids"] = [s["attrs"].get("id", ("str", ""))[1] if isinstance(s["attrs"].get("id"), tuple) else "" for s in stack]
        elements.append(el)
        if not t["self_closing"] and t["name"] in CONTAINERS:
            stack.append(el)
    return elements


def elem_id(el):
    v = el["attrs"].get("id")
    return v[1] if isinstance(v, tuple) else None


# ----------------------------------------------------------------------------
# Lint
# ----------------------------------------------------------------------------

class Lint:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, where, msg):
        self.errors.append((where, msg))

    def warn(self, where, msg):
        self.warnings.append((where, msg))

    def report(self):
        for where, msg in self.errors:
            print("  ERROR    {}: {}".format(where, msg))
        for where, msg in self.warnings:
            print("  warning  {}: {}".format(where, msg))
        print("  {} error(s), {} warning(s)".format(len(self.errors), len(self.warnings)))
        return not self.errors


def load_form_dir(form_dir, lint):
    docs = {}
    for mod in ALL_DOCS:
        path = os.path.join(form_dir, "docs", mod + ".txt")
        if not os.path.exists(path):
            lint.error("docs/{}.txt".format(mod), "file is missing")
            docs[mod] = None
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        docs[mod] = text
    data = {}
    for mod in JSON_MODULES:
        if docs.get(mod) is None:
            data[mod] = None
            continue
        try:
            data[mod] = json.loads(docs[mod])
        except json.JSONDecodeError as ex:
            lint.error("docs/{}.txt".format(mod), "invalid JSON: {}".format(ex))
            data[mod] = None
    meta_path = os.path.join(form_dir, "meta.json")
    meta = None
    if os.path.exists(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
        except json.JSONDecodeError as ex:
            lint.error("meta.json", "invalid JSON: {}".format(ex))
    else:
        lint.error("meta.json", "file is missing")
    return meta, docs, data


def condition_objects(obj, path="", out=None):
    """Recursively find every {conditions: [...]} object in a JSON structure."""
    if out is None:
        out = []
    if isinstance(obj, dict):
        if isinstance(obj.get("conditions"), list):
            out.append((path, obj))
        for k, v in obj.items():
            condition_objects(v, "{}.{}".format(path, k) if path else k, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            condition_objects(v, "{}[{}]".format(path, i), out)
    return out


def check_conditions(lint, where, cond_obj, types):
    conds = cond_obj.get("conditions") or []
    if len(conds) > 1 and "operator" not in cond_obj:
        lint.error(where, "{} conditions but no \"operator\" (\"and\"/\"or\" is required with more than one condition)".format(len(conds)))
    for c in conds:
        if not isinstance(c, dict):
            continue
        eid = c.get("elementId")
        comp = c.get("comparator")
        if eid and eid not in types and not eid.startswith("_"):
            lint.error(where, "condition references unknown elementId \"{}\"".format(eid))
        if eid and types.get(eid) == "Checkbox" and comp in ("includes", "equal", "truthy", "falsy"):
            lint.error(where, "Checkbox \"{}\" cannot use comparator \"{}\"; use oneOf/allOf/noneOf (with an array value), empty, or notEmpty".format(eid, comp))


def jsx_condition_blocks(layout):
    """Yield (line, attr, text) for display={{...}} / validate={{...}} blocks in the layout."""
    for m in re.finditer(r"\b(display|validate)=\{\{", layout):
        start = m.end() - 2
        depth, quote, k = 0, None, start
        while k < len(layout):
            c = layout[k]
            if quote:
                if c == "\\":
                    k += 2
                    continue
                if c == quote:
                    quote = None
            elif c in "\"'`":
                quote = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        line = layout.count("\n", 0, m.start()) + 1
        yield line, m.group(1), layout[start:k + 1]


def lint_form(meta, docs, data, lint):
    layout = docs.get("layout")
    types, tables_of_columns, ids_in_order = {}, {}, []
    elements = []
    if layout is not None:
        stripped = layout.strip()
        if not stripped.startswith("<Form"):
            lint.error("docs/layout.txt", "must start with <Form ...>; it holds bare JSX, no const/export wrapper")
        if not stripped.endswith("</Form>"):
            lint.error("docs/layout.txt", "must end with </Form>")
        elements = build_tree(scan_tags(layout))
        for el in elements:
            eid = elem_id(el)
            where = "docs/layout.txt:{}".format(el["line"])
            name = el["name"]
            if eid:
                if eid in types:
                    lint.error(where, "duplicate id \"{}\" (ids must be unique across the whole form)".format(eid))
                if eid in RESERVED_ID_ERROR:
                    lint.error(where, "id \"{}\" is a reserved email template key and the form will not import; use referenceId or requestId".format(eid))
                elif eid in RESERVED_ID_WARN:
                    lint.warn(where, "id \"{}\" matches a notification template variable; pick another id to be safe".format(eid))
                types[eid] = name
                ids_in_order.append(eid)
                if name == "TableColumn":
                    parent_table = ""
                    for pname, pid in zip(el["parents"], el["parent_ids"]):
                        if pname == "Table":
                            parent_table = pid
                    tables_of_columns[eid] = parent_table
            elif name not in ("Form", "Actions", "View", "Pagebreak", "Html", "Spacer", "Line") and name in (
                    "Input", "Textarea", "Dropdown", "Radio", "Checkbox", "Boolean", "Datetime", "Signature",
                    "Timestamp", "Upload", "Address", "Distance", "Computed", "Identifier", "Table", "TableColumn"):
                lint.error(where, "<{}> has no id".format(name))
            attrs = el["attrs"]
            # structural rules
            if name == "Section" and "Section" in el["parents"]:
                lint.error(where, "Sections cannot be nested inside Sections")
            if name == "Table" and "Tile" in el["parents"]:
                lint.warn(where, "Table inside a Tile; the documented safe placement is directly inside a Section")
            if name not in ("Form", "Section", "Actions", "View") and "Section" not in el["parents"] and name != "Pagebreak":
                lint.error(where, "<{}> must be inside a <Section>".format(name))
            # prop rules
            if name == "Boolean" and "required" in attrs:
                lint.error(where, "<Boolean> does not support the required prop (use a validate rule instead)")
            if name == "TableColumn":
                if "initialValue" in attrs:
                    lint.error(where, "<TableColumn> does not accept initialValue; use a formula or values array")
                if "align" in attrs and "formula" not in attrs and "values" not in attrs:
                    lint.error(where, "align on a TableColumn only works when formula or values is also set")
                if attrs.get("type") == ("str", "upload"):
                    lint.error(where, "there is no upload column type; place Upload fields outside the table")
            if name == "Dropdown" and "hideSearch" in attrs and "multiple" in attrs:
                lint.error(where, "<Dropdown> hideSearch is not compatible with multiple")
            if name in ("Dropdown", "Radio", "Checkbox", "TableColumn") and isinstance(attrs.get("options"), tuple) and attrs["options"][0] == "expr":
                if re.search(r"\blabel\s*:", attrs["options"][1]) and re.search(r"\bvalue\s*:", attrs["options"][1]):
                    lint.error(where, "options entries cannot be {label, value} objects; use single-pair objects like { stored: \"Display Text\" }")
            for key in ("label", "hint", "tooltip", "placeholder", "text"):
                v = attrs.get(key)
                if isinstance(v, tuple) and (EM_DASH in v[1] or EN_DASH in v[1]):
                    lint.warn(where, "{} contains a long dash; house style avoids em/en dashes in form copy".format(key))
        # Text inline style rules
        for m in re.finditer(r"<(h[1-6]|span|p|div|b|i|li|td|th)\s+style=\{\{([^}]*)\}\}", layout):
            tag, body = m.group(1), m.group(2)
            line = layout.count("\n", 0, m.start()) + 1
            keys = set(re.findall(r"\b([A-Za-z]+)\s*:", body))
            bad = keys - TEXT_STYLE_OK
            where = "docs/layout.txt:{}".format(line)
            if bad:
                lint.error(where, "unsupported style props on <{}>: {} (only color, fontSize, fontFamily, textAlign are allowed inside <Text>)".format(tag, ", ".join(sorted(bad))))
            if tag.startswith("h") and keys & {"color", "fontSize", "fontFamily"}:
                lint.error(where, "<{}> cannot take color/fontSize/fontFamily; wrap the content in a <span> and style the span".format(tag))
            if tag == "span" and "textAlign" in keys:
                lint.error(where, "<span> cannot take textAlign; put it on the parent block element")
        for m in re.finditer(r"style=\"", layout):
            line = layout.count("\n", 0, m.start()) + 1
            lint.error("docs/layout.txt:{}".format(line), "style=\"...\" string attribute; inside <Html> this crashes the form (React error #62). Use style={{ }} in <Text> or presentational attributes in <Html>")
        for m in re.finditer(r"(?<!#)###(?!#)[A-Za-z_]", layout):
            line = layout.count("\n", 0, m.start()) + 1
            lint.warn("docs/layout.txt:{}".format(line), "\"###field##\" renders empty; the parser eats the literal #. Put a space or other character between # and the interpolation")
        if EM_DASH in layout:
            lint.warn("docs/layout.txt", "contains em dashes; house style avoids them in form copy")
        for line, attr, block in jsx_condition_blocks(layout):
            comps = len(re.findall(r"\bcomparator\s*:", block))
            if comps > 1 and not re.search(r"\boperator\s*:", block):
                lint.error("docs/layout.txt:{}".format(line), "{} has {} conditions but no operator (\"and\"/\"or\" is required with more than one condition)".format(attr, comps))
            for cm in re.finditer(r"elementId\s*:\s*[\"']([^\"']+)[\"']\s*,\s*comparator\s*:\s*[\"']([^\"']+)[\"']", block):
                eid, comp = cm.group(1), cm.group(2)
                if eid not in types and not eid.startswith("_"):
                    lint.error("docs/layout.txt:{}".format(line), "{} condition references unknown elementId \"{}\"".format(attr, eid))
                elif types.get(eid) == "Checkbox" and comp in ("includes", "equal", "truthy", "falsy"):
                    lint.error("docs/layout.txt:{}".format(line), "Checkbox \"{}\" cannot use comparator \"{}\"; use oneOf/allOf/noneOf with an array value".format(eid, comp))
        for required in ("submittedByName", "submittedByEmail"):
            if required not in types:
                lint.error("docs/layout.txt", "required system field \"{}\" is missing; the form will not import".format(required))
        if "Actions" not in [e["name"] for e in elements]:
            lint.warn("docs/layout.txt", "no <Actions> block; the default submit bar will be used")

    # workflow
    wf = data.get("workflow")
    steps_def = {}
    parallel_containers = set()
    substeps_all = set()
    if isinstance(wf, dict):
        steps_def = wf.get("steps") or {}
        if "start" not in steps_def:
            lint.error("docs/workflow.txt", "workflow has no \"start\" step")
        if "completed" not in steps_def:
            lint.error("docs/workflow.txt", "workflow has no \"completed\" step")
        for sid, step in steps_def.items():
            where = "docs/workflow.txt steps.{}".format(sid)
            if not isinstance(step, dict):
                lint.error(where, "step must be an object")
                continue
            if step.get("type") == "parallel":
                parallel_containers.add(sid)
                subs = step.get("substeps") or []
                if not subs:
                    lint.error(where, "parallel step needs a non-empty substeps array")
                for sub in subs:
                    substeps_all.add(sub)
                    if sub not in steps_def:
                        lint.error(where, "substep \"{}\" is not defined as a top-level step".format(sub))
                    elif sub in ("start", "completed", "rejected"):
                        lint.error(where, "\"{}\" cannot be a substep".format(sub))
                on_enter = step.get("onEnter") or {}
                if "assign" in on_enter or "sendToSubmitter" in on_enter:
                    lint.error(where, "parallel container cannot have onEnter.assign or sendToSubmitter; substeps carry the assignment")
                if "onSubmit" not in step:
                    lint.error(where, "parallel container must define onSubmit for its substeps")
            for key in ("onSubmit", "onReject"):
                rules = step.get(key)
                if rules is None:
                    continue
                if not isinstance(rules, list):
                    lint.error(where, "{} must be an array of routing rules".format(key))
                    continue
                for i, rule in enumerate(rules):
                    tgt = rule.get("target") if isinstance(rule, dict) else None
                    if tgt not in steps_def:
                        lint.error(where, "{}[{}] targets unknown step \"{}\"".format(key, i, tgt))
                    if isinstance(rule, dict) and isinstance(rule.get("if"), dict):
                        check_conditions(lint, where + ".{}[{}].if".format(key, i), rule["if"], types)
            on_enter = step.get("onEnter")
            if isinstance(on_enter, dict):
                assign = on_enter.get("assign")
                if isinstance(assign, dict):
                    for k in ("nameElementId", "emailElementId"):
                        if k in assign and assign[k] not in types:
                            lint.error(where, "onEnter.assign.{} references unknown field \"{}\"".format(k, assign[k]))
                        elif k in assign and types.get(assign[k]) not in ("Computed", "Input", "Dropdown"):
                            lint.warn(where, "onEnter.assign.{} points at a <{}>; a Computed (or Input) returning a string is expected".format(k, types.get(assign[k])))
                    if "name" in assign and "email" in assign and not assign.get("email"):
                        lint.error(where, "static assign has an empty email")
                elif isinstance(assign, str):
                    if assign in types:
                        lint.warn(where, "onEnter.assign uses the legacy single-object form; prefer nameElementId/emailElementId")
                    elif re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", assign):
                        lint.error(where, "onEnter.assign references unknown field \"{}\"".format(assign))
                    else:
                        lint.warn(where, "onEnter.assign is an expression returning {name, email} (legacy); prefer nameElementId/emailElementId computeds")
                if isinstance(on_enter.get("if"), dict):
                    check_conditions(lint, where + ".onEnter.if", on_enter["if"], types)
                for sa in on_enter.get("scheduledActions") or []:
                    if isinstance(sa, dict) and sa.get("type") == "remind" and not sa.get("notificationTemplateId"):
                        lint.error(where, "scheduledActions remind entry needs a notificationTemplateId")
        for sid, step in steps_def.items():
            if sid in substeps_all and isinstance(step, dict):
                where = "docs/workflow.txt steps.{}".format(sid)
                if step.get("status") != "pending":
                    lint.error(where, "substep must have \"status\": \"pending\"")
                if "onSubmit" in step or "onReject" in step:
                    lint.error(where, "substeps cannot define onSubmit/onReject; the parallel container owns them")
                on_enter = step.get("onEnter") or {}
                if "assign" not in on_enter and "sendToSubmitter" not in on_enter:
                    lint.error(where, "substep needs onEnter.assign or onEnter.sendToSubmitter")
            if sid not in ("start",) and isinstance(step, dict) and sid not in parallel_containers and sid not in substeps_all:
                if "status" not in step:
                    lint.error("docs/workflow.txt steps.{}".format(sid), "non-start step needs a status (pending, completed, or rejected)")
        for sid, step in steps_def.items():
            for tgt_list in ("onSubmit", "onReject"):
                for rule in (step.get(tgt_list) or []) if isinstance(step, dict) else []:
                    if isinstance(rule, dict) and rule.get("target") in substeps_all:
                        lint.error("docs/workflow.txt steps.{}".format(sid), "{} targets substep \"{}\"; transitions may only target the parallel container".format(tgt_list, rule["target"]))

    # steps (permissions)
    st = data.get("steps")
    if isinstance(st, dict) and layout is not None:
        for sid, entry in st.items():
            where = "docs/steps.txt {}".format(sid)
            if steps_def and sid not in steps_def:
                lint.error(where, "step is not defined in workflow.txt")
            if sid in parallel_containers:
                lint.error(where, "parallel container steps do not take a permissions entry; only their substeps do")
            perms = (entry or {}).get("permissions") if isinstance(entry, dict) else None
            if not isinstance(perms, dict):
                lint.error(where, "needs a \"permissions\" object")
                continue
            for fid, val in perms.items():
                if val not in PERMISSION_VALUES:
                    lint.error(where, "\"{}\": \"{}\" is not a valid permission (editable, readonly, hidden, redacted)".format(fid, val))
                if fid == "_actions":
                    continue
                t = types.get(fid)
                if t is None:
                    lint.warn(where, "permission for unknown element id \"{}\" (Droplet ignores it, but it is probably stale)".format(fid))
                    continue
                if t in NO_PERMISSIONS:
                    lint.error(where, "<{} id=\"{}\"> cannot take step permissions; remove it".format(t, fid))
                if val == "editable" and t == "Computed":
                    lint.error(where, "<Computed id=\"{}\"> cannot be editable (readonly, hidden, or redacted only)".format(fid))
                if val == "editable" and t in ("Identifier", "Timestamp"):
                    lint.warn(where, "<{} id=\"{}\"> is editable; these are normally readonly".format(t, fid))
                if val == "editable" and t in STRUCTURAL and t != "Table":
                    lint.error(where, "<{} id=\"{}\"> is structural and cannot be editable".format(t, fid))
            for fid, val in perms.items():
                if val == "editable" and types.get(fid) == "TableColumn":
                    table_id = tables_of_columns.get(fid)
                    table_perm = perms.get(table_id, "editable" if sid == "start" and table_id in perms else None)
                    if sid == "start":
                        table_perm = perms.get(table_id)
                    else:
                        table_perm = perms.get(table_id, "readonly")
                    if table_perm != "editable":
                        lint.error(where, "column \"{}\" is editable but its table \"{}\" is {} in this step; the Table must also be editable".format(fid, table_id, table_perm or "unlisted"))
            if sid == "start":
                missing = [fid for fid in ids_in_order if fid not in perms and types.get(fid) in INPUT_TYPES]
                for fid in missing:
                    lint.warn(where, "\"{}\" (<{}>) has no start-step permission, so it defaults to readonly and cannot be filled in".format(fid, types.get(fid)))
            if sid in ("completed", "rejected") and perms.get("_actions") != "hidden":
                lint.warn(where, "terminal step should set \"_actions\": \"hidden\"")
        for sid in steps_def:
            if sid not in st and sid not in parallel_containers:
                lint.warn("docs/steps.txt", "workflow step \"{}\" has no permissions entry (fields default to readonly)".format(sid))

    # notifications
    nt = data.get("notifications")
    if isinstance(nt, dict):
        for sid, events in nt.items():
            where = "docs/notifications.txt {}".format(sid)
            if steps_def and sid not in steps_def:
                lint.error(where, "step is not defined in workflow.txt")
            if not isinstance(events, dict):
                lint.error(where, "must be an object keyed by onEnter / onExit")
                continue
            for ev, payload in events.items():
                if ev not in ("onEnter", "onExit"):
                    lint.error(where, "unknown event \"{}\" (use onEnter or onExit)".format(ev))
                items = payload if isinstance(payload, list) else [payload]
                for i, n in enumerate(items):
                    w = "{}.{}[{}]".format(where, ev, i)
                    if not isinstance(n, dict):
                        lint.error(w, "notification must be an object")
                        continue
                    tpl = n.get("template")
                    if not isinstance(tpl, dict):
                        lint.error(w, "missing template {subject, body}")
                        continue
                    extra = set(tpl.keys()) - {"subject", "body"}
                    if extra:
                        lint.error(w, "template may only contain subject and body; move {} up a level".format(", ".join(sorted(extra))))
                    body = "{} {}".format(tpl.get("subject", ""), tpl.get("body", ""))
                    if n.get("type") == "remind" and "##assignmentUrl##" in body:
                        lint.error(w, "reminder templates cannot use ##assignmentUrl##; link with ##submissionUrl##")
                    if n.get("type") == "assignment" and "recipients" in n:
                        lint.warn(w, "assignment notifications go to the assignee; recipients is usually not needed here")
                    if n.get("type") not in (None, "assignment", "remind"):
                        lint.error(w, "unknown notification type \"{}\"".format(n.get("type")))
                    if n.get("type") not in ("assignment", "remind") and not n.get("sendToSubmitter") and not n.get("recipients"):
                        lint.warn(w, "notification has no recipients, no sendToSubmitter, and is not an assignment; it will reach nobody")
                    if re.search(r"(?<!#)###(?!#)[A-Za-z_]", body):
                        lint.warn(w, "\"###field##\" renders empty; separate the literal # from the interpolation")
                    if EM_DASH in body:
                        lint.warn(w, "contains em dashes; house style avoids them")
                    for var in re.findall(r"##([A-Za-z_][A-Za-z0-9_]*)(?:[.\[][^#]*)?##", body):
                        if var not in types and var not in SYSTEM_TEMPLATE_VARS:
                            lint.warn(w, "##{}## does not match a field id or a known template variable".format(var))
                    if isinstance(n.get("if"), dict):
                        check_conditions(lint, w + ".if", n["if"], types)
                    for r in n.get("recipients") or [] if isinstance(n.get("recipients"), list) else []:
                        if isinstance(r, dict):
                            for k in ("nameElementId", "emailElementId"):
                                if k in r and r[k] not in types:
                                    lint.error(w, "recipient {} references unknown field \"{}\"".format(k, r[k]))
                    for h in n.get("hidden") or []:
                        if h not in types:
                            lint.warn(w, "hidden entry \"{}\" is not an element id".format(h))
        # scheduledActions must point at an existing reminder id
        if isinstance(wf, dict):
            reminder_ids = set()
            for sid, events in nt.items():
                if isinstance(events, dict):
                    for ev, payload in events.items():
                        for n in (payload if isinstance(payload, list) else [payload]):
                            if isinstance(n, dict) and n.get("type") == "remind" and n.get("id"):
                                reminder_ids.add(n["id"])
            for sid, step in steps_def.items():
                if isinstance(step, dict):
                    for sa in (step.get("onEnter") or {}).get("scheduledActions") or []:
                        if isinstance(sa, dict) and sa.get("notificationTemplateId") and sa["notificationTemplateId"] not in reminder_ids:
                            lint.error("docs/workflow.txt steps.{}".format(sid), "scheduledActions references reminder id \"{}\" but no notification with type remind and that id exists".format(sa["notificationTemplateId"]))

    # datasets
    ds = data.get("datasets")
    if isinstance(ds, dict):
        if ds.get("local"):
            lint.warn("docs/datasets.txt", "local datasets are present; the recommended pattern is a global dataset referenced by datasetId")
        for name, ref in (ds.get("global") or {}).items():
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                lint.error("docs/datasets.txt", "dataset name \"{}\" is not a valid identifier (it becomes a formula variable)".format(name))
            if isinstance(ref, dict) and ref.get("datasetId") in ("", "REPLACE_ME", "REPLACE_WITH_DATASET_ID"):
                lint.warn("docs/datasets.txt", "dataset \"{}\" has a placeholder datasetId; replace it after uploading the dataset in Droplet".format(name))
            if isinstance(ref, dict) and "datasetId" not in ref and name not in (ds.get("resolved") or {}):
                lint.warn("docs/datasets.txt", "dataset \"{}\" has no datasetId and no resolved snapshot; it will be empty".format(name))

    # attributes
    at = data.get("attributes")
    if isinstance(at, dict):
        for sid, mapping in at.items():
            if steps_def and sid not in steps_def:
                lint.error("docs/attributes.txt {}".format(sid), "step is not defined in workflow.txt")
            for fid, attr in (mapping or {}).items():
                if fid not in types:
                    lint.error("docs/attributes.txt {}".format(sid), "unknown field id \"{}\"".format(fid))
                if attr not in ("fullName", "primaryEmail", "firstName", "lastName") and not attr.startswith("customAttribute"):
                    lint.warn("docs/attributes.txt {}".format(sid), "\"{}\" is not a known profile attribute (fullName, primaryEmail, customAttributeN)".format(attr))

    # integrations
    ig = data.get("integrations")
    if isinstance(ig, dict):
        for sid, events in ig.items():
            where = "docs/integrations.txt {}".format(sid)
            if steps_def and sid not in steps_def:
                lint.error(where, "step is not defined in workflow.txt")
            if not isinstance(events, dict):
                continue
            for ev, arr in events.items():
                if ev not in ("onEnter", "onExit"):
                    lint.error(where, "unknown event \"{}\" (use onEnter or onExit)".format(ev))
                for i, integ in enumerate(arr if isinstance(arr, list) else []):
                    cfg = (integ or {}).get("configuration") or {}
                    w = "{}.{}[{}]".format(where, ev, i)
                    if "secret" in cfg and not cfg["secret"]:
                        lint.error(w, "\"secret\": \"\" fails validation; omit the secret key entirely unless referencing a real named secret")
                    if cfg.get("connectionId") in (0, None, ""):
                        lint.warn(w, "connectionId is a placeholder; the step will fail at runtime until the real workspace connection id is set")
                    for mp in cfg.get("mappings") or []:
                        if isinstance(mp, dict) and mp.get("source") not in types:
                            lint.warn(w, "mapping source \"{}\" is not a field id".format(mp.get("source")))

    # tag expressions
    te = data.get("tagExpressions")
    if isinstance(te, dict):
        for label, expr in te.items():
            if not isinstance(expr, str):
                lint.error("docs/tagExpressions.txt", "\"{}\" must map to an expression string".format(label))

    # meta
    if isinstance(meta, dict):
        form = meta.get("form") or {}
        if not form.get("name"):
            lint.error("meta.json", "form.name is required")
        for k in ("loginRequired", "submitAsLoggedIn"):
            if k in form and not isinstance(form[k], bool):
                lint.error("meta.json", "form.{} must be true or false".format(k))
    return lint


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------

EXPORT_BLOCK = "\n\n// -------\n// Exports\n// -------\n\nexport {{ {name} }};\n"


def wrap_json_module(name, text):
    return "const {} = {};{}".format(name, text.strip(), EXPORT_BLOCK.format(name=name))


def wrap_layout(text):
    lines = text.strip("\n").split("\n")
    out = ["const layout = () => ("]
    for i, line in enumerate(lines):
        if line.strip() == "":
            out.append("")
        elif i == 0:
            out.append("  " + line)
        else:
            out.append("    " + line)
    out.append(");")
    return "\n".join(out) + EXPORT_BLOCK.format(name="layout")


def metadata_module(meta):
    form = (meta or {}).get("form") or {}
    md = {
        "name": form.get("name", "Untitled Form"),
        "description": form.get("description", ""),
        "version": "draft-{}".format(int(time.time() * 1000)),
        "loginRequired": bool(form.get("loginRequired", False)),
        "submitAsLoggedIn": bool(form.get("submitAsLoggedIn", False)),
        "published": False,
        "archived": False,
    }
    return "const metadata = {};{}".format(json.dumps(md, indent=2), EXPORT_BLOCK.format(name="metadata"))


def build(form_dir, output, skip_lint):
    lint = Lint()
    meta, docs, data = load_form_dir(form_dir, lint)
    if not skip_lint:
        lint_form(meta, docs, data, lint)
    print("Lint results for {}:".format(form_dir))
    ok = lint.report()
    if not ok:
        print("Build aborted: fix the errors above (or pass --skip-lint to build anyway).")
        return 1
    if any(docs.get(m) is None for m in ALL_DOCS) or meta is None:
        print("Build aborted: missing files.")
        return 1
    form_name = ((meta.get("form") or {}).get("name") or "Form").strip()
    if not output:
        output = os.path.join(os.path.abspath(form_dir), form_name + ".drplt")
    files = {}
    files["meta.json"] = json.dumps(meta, indent=2) + "\n"
    files["docs/layout.txt"] = docs["layout"].strip("\n") + "\n"
    files["import/layout.jsx"] = wrap_layout(docs["layout"])
    for mod in JSON_MODULES:
        files["docs/{}.txt".format(mod)] = docs[mod].strip("\n") + "\n"
        files["import/{}.js".format(mod)] = wrap_json_module(mod, docs[mod])
    files["import/metadata.js"] = metadata_module(meta)
    digest = hashlib.sha256("".join(files[k] for k in sorted(files)).encode("utf-8")).hexdigest()
    files["import/package.json"] = json.dumps({"name": "@drplt/form-" + digest, "type": "module"}, indent=2) + "\n"
    os.makedirs(os.path.dirname(os.path.abspath(output)) or ".", exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ["import/metadata.js", "docs/layout.txt", "import/layout.jsx"] + \
                    [p for mod in JSON_MODULES for p in ("docs/{}.txt".format(mod), "import/{}.js".format(mod))] + \
                    ["import/package.json", "meta.json"]:
            z.writestr(name, files[name])
    print("Built {} ({} bytes)".format(output, os.path.getsize(output)))
    return 0


# ----------------------------------------------------------------------------
# Extract
# ----------------------------------------------------------------------------

def extract(path, out_dir):
    if not out_dir:
        out_dir = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(os.path.join(out_dir, "docs"), exist_ok=True)
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        for mod in ALL_DOCS:
            n = "docs/{}.txt".format(mod)
            if n in names:
                with open(os.path.join(out_dir, "docs", mod + ".txt"), "wb") as f:
                    f.write(z.read(n))
            else:
                print("  note: archive has no {}".format(n))
        if "meta.json" in names:
            meta = json.loads(z.read("meta.json").decode("utf-8"))
        elif "import/metadata.js" in names:
            js = z.read("import/metadata.js").decode("utf-8")
            body = js[js.index("{"): js.index("};") + 1]
            m = json.loads(body)
            meta = {"version": 1, "form": {"name": m.get("name", ""), "description": m.get("description", ""),
                                            "loginRequired": m.get("loginRequired", False),
                                            "submitAsLoggedIn": m.get("submitAsLoggedIn", False)}}
        else:
            meta = {"version": 1, "form": {"name": os.path.splitext(os.path.basename(path))[0], "description": "",
                                            "loginRequired": False, "submitAsLoggedIn": False}}
        with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
    print("Extracted {} -> {}/ (meta.json + docs/; the import/ half is regenerated on build)".format(path, out_dir))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Build, lint, or extract Droplet .drplt archives.")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="lint then zip <form-dir> into a .drplt")
    b.add_argument("form_dir")
    b.add_argument("-o", "--output", help="output .drplt path (default: <form name>.drplt next to the form dir)")
    b.add_argument("--skip-lint", action="store_true")
    l = sub.add_parser("lint", help="check <form-dir> for common import and runtime failures")
    l.add_argument("form_dir")
    e = sub.add_parser("extract", help="unpack a .drplt into meta.json + docs/ for editing")
    e.add_argument("drplt")
    e.add_argument("-o", "--output")
    a = p.parse_args(argv)
    if a.cmd == "build":
        return build(a.form_dir, a.output, a.skip_lint)
    if a.cmd == "lint":
        lint = Lint()
        meta, docs, data = load_form_dir(a.form_dir, lint)
        lint_form(meta, docs, data, lint)
        print("Lint results for {}:".format(a.form_dir))
        return 0 if lint.report() else 1
    if a.cmd == "extract":
        return extract(a.drplt, a.output)
    return 2


if __name__ == "__main__":
    sys.exit(main())
