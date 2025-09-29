
import json, yaml, os, html

def _load_plan(plan_path):
    with open(plan_path, "r") as f:
        return json.load(f)

def _load_rules(rules_path):
    with open(rules_path, "r") as f:
        data = yaml.safe_load(f) or {}
        return data.get("rules", [])

def _iter_resources(root):
    # Yield (type, name, values, ref) recursively from planned_values.root_module.*
    def walk(module):
        for r in module.get("resources", []):
            ref = f"{r.get('type','')}.{r.get('name','')}"
            yield r.get("type",""), r.get("name",""), r.get("values", {}), r, ref
        for child in module.get("child_modules", []):
            yield from walk(child)
    planned = root.get("planned_values", {})
    rm = planned.get("root_module", {})
    yield from walk(rm)

def _parse_path(path):
    out, buf, i = [], "", 0
    while i < len(path):
        ch = path[i]
        if ch == ".":
            if buf: out.append(buf); buf=""
            i+=1; continue
        if ch == "[":
            if buf: out.append(buf); buf=""
            j = path.find("]", i)
            idx = int(path[i+1:j])
            out.append(idx)
            i = j+1
            continue
        buf += ch
        i+=1
    if buf: out.append(buf)
    return out

def _get_nested(value, path):
    cur = value
    for token in _parse_path(path):
        if isinstance(token, str):
            if not isinstance(cur, dict) or token not in cur: return None
            cur = cur[token]
        else:
            if not isinstance(cur, list) or token >= len(cur): return None
            cur = cur[token]
    return cur

def _set_nested(value, path, newval):
    cur = value
    toks = _parse_path(path)
    for i, token in enumerate(toks):
        last = i == len(toks)-1
        if isinstance(token, str):
            if last:
                if isinstance(cur, dict):
                    cur[token] = newval
            else:
                cur = cur.get(token, {})
        else:
            if isinstance(cur, list) and token < len(cur):
                if last:
                    cur[token] = newval
                else:
                    cur = cur[token]

def _rule_require_tags(values, params):
    required = params.get("required", [])
    tags = values.get("tags") or values.get("labels") or {}
    missing = [k for k in required if k not in tags]
    if missing:
        return {"message": f"Missing required tags: {', '.join(missing)}",
                "fix": {"tags": {k: "FIXME" for k in missing}}}

def _rule_field_equals(values, field, equals):
    val = _get_nested(values, field)
    if val != equals:
        return {"message": f"Field '{field}' expected '{equals}', got '{val}'",
                "fix_field": field, "fix_value": equals}

def _rule_forbid_cidr(values, field, value):
    arr = _get_nested(values, field)
    if isinstance(arr, list) and value in arr:
        newarr = [x for x in arr if x != value]
        return {"message": f"CIDR '{value}' is forbidden in '{field}'",
                "fix_field": field, "fix_value": newarr}

def run_scan(plan_path, rules_path, html_out=None, autofix_out=None):
    root = _load_plan(plan_path)
    rules = _load_rules(rules_path)

    findings = []
    fixes = {}
    for rtype, rname, values, rsrc, ref in _iter_resources(root):
        for rule in rules:
            target = rule.get("target","any")
            if not (target == "any" or target == rtype):
                continue
            level = rule.get("level","error")
            rid   = rule.get("id","rule")
            rkind = rule.get("type")
            params = rule.get("params",{})
            res = None
            if rkind == "require_tags":
                res = _rule_require_tags(values, params)
            elif rkind == "field_equals":
                res = _rule_field_equals(values, rule.get("field",""), rule.get("equals"))
            elif rkind == "forbid_cidr":
                res = _rule_forbid_cidr(values, rule.get("field",""), rule.get("value"))
            if res:
                res.update({"rule_id": rid, "level": level,
                            "resource_type": rtype, "resource_name": rname})
                findings.append(res)
                if "fix" in res:
                    # merge deep tags
                    existing = fixes.setdefault(ref, {})
                    tags_fix = res["fix"].get("tags")
                    if tags_fix:
                        existing_tags = existing.get("tags", {})
                        existing_tags.update(tags_fix)
                        existing["tags"] = existing_tags
                elif "fix_field" in res:
                    fixes.setdefault(ref, {})[res["fix_field"]] = res["fix_value"]

    if findings:
        print(f"LaGuardia: found {len(findings)} issue(s)")
        for f in findings:
            print(f"[{f['level'].upper()}] {f['rule_id']} {f['resource_type']}.{f['resource_name']}: {f['message']}")
    else:
        print("LaGuardia: no issues found ✅")

    if html_out:
        _write_html_report(findings, html_out)
    if autofix_out and fixes:
        with open(autofix_out, "w") as f:
            json.dump(fixes, f, indent=2)
        print(f"Auto-fix suggestions written to {autofix_out}")

    return findings

def _write_html_report(findings, path):
    rows = []
    for f in findings:
        rows.append(f"""
        <tr>
          <td>{html.escape(f.get('level',''))}</td>
          <td>{html.escape(f.get('rule_id',''))}</td>
          <td>{html.escape(f.get('resource_type',''))}</td>
          <td>{html.escape(f.get('resource_name',''))}</td>
          <td>{html.escape(f.get('message',''))}</td>
        </tr>
        """)
    table = "".join(rows) if rows else "<tr><td colspan='5'>No issues 🎉</td></tr>"
    html_doc = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>LaGuardia Report</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:20px}
h1{margin:0 0 10px}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #ddd;padding:8px;text-align:left}
th{background:#f5f5f5}
footer{margin-top:20px;color:#777;font-size:12px}
a{color:inherit}
</style>
</head>
<body>
  <h1>LaGuardia Report</h1>
  <table>
    <thead><tr><th>Level</th><th>Rule</th><th>Resource Type</th><th>Resource Name</th><th>Message</th></tr></thead>
    <tbody>""" + table + """</tbody>
  </table>
  <footer>
    Generated by LaGuardia • <a href="https://senora.dev" target="_blank" rel="noopener noreferrer">senora.dev</a>
  </footer>
</body>
</html>"""
    with open(path, "w") as f:
        f.write(html_doc)
