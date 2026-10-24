"""Regenerate reference/wi_adu_rules.csv and reference/wi_rights_exposure.csv from the hand-coded spec.

Usage: uv run python scripts/build_reference_rules.py reference reference [data/processed/adu_mention_scan]
(args: spec directory, output directory, optional scan directory). The spec in
reference/wi_adu_rules_spec.py is the human-edited record of each coding and its source.

Derived rows and columns (rights classes and flags per missing_middleware.contracts, AQ-026):
- `approval_pathway` rule rows (ministerial / discretionary / unknown), one per approval_type row, or one
  derived from the current form rows where a place has no approval_type row (see `pathway()`).
- `ordinance_status` rule rows (first pass), from the scan plus the manual answers in the spec.
- exposure columns `restrictions` (current-law flags the reform removes), `reform_restrictions` (flags left
  after the reform; only occupancy flags in adu_form_only) and `approval_pathway`.
"""
import collections
import csv
import os
import re
import sys

sys.path.insert(0, sys.argv[1])
import wi_adu_rules_spec as spec  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from missing_middleware.contracts import RESTRICTION_FLAGS  # noqa: E402

out = sys.argv[2]
PR = ["rule_id", "jurisdiction_id", "jurisdiction_name", "provision", "value", "effective_from", "effective_to",
      "source_url", "source_section", "retrieved", "verification", "notes"]
RE = ["jurisdiction_id", "jurisdiction_name", "scenario_id", "current_class", "reform_class", "class_basis",
      "rules_as_of", "restrictions", "reform_restrictions", "approval_pathway", "rights_added_text", "rule_ids",
      "aq023_default_class", "default_matches_coded", "notes"]
OCC_FLAGS = ("owner_occupancy", "related_occupant")
DISC = re.compile(r"(?i)conditional|special use|plan commission")
MIN = re.compile(r"(?i)ministerial|permit|permitted|administrative|staff|limited use|by right")


def pathway_of_text(text: str) -> str:
    if re.search(r"(?i)\bministerial\b", text):
        return "ministerial"
    if DISC.search(text):
        return "discretionary"
    return "ministerial" if MIN.search(text) else "unknown"


def pathway(m):
    """approval_pathway rows: (value, from, to, url, section, verification, note)."""
    rows = []
    for prov, val, f, t, url, sec, ver, note in m["rules"]:
        if prov == "approval_type":
            rows.append((pathway_of_text(val), f, t, url, sec, ver, f"derived from approval_type '{val}'"))
    if rows:
        return rows
    cur = [r for r in m["rules"] if r[0] in ("detached_allowed", "attached_allowed") and not r[3]]
    vals = {r[1] for r in cur}
    src = cur[0] if cur else m["rules"][0]
    if "by_right" in vals:
        v, why = "ministerial", "derived from a current by_right form (no approval_type row)"
    elif "conditional" in vals:
        v, why = "discretionary", "derived from a current conditional form (no approval_type row)"
    elif vals and vals <= {"prohibited"}:
        v, why = "unknown", "not applicable: no ADU form is allowed"
    else:
        v, why = "unknown", "approval route not found"
    return [(v, src[2], "", src[4], src[5], src[6] if v != "unknown" else "unknown", why)]


def occupancy_flags(m):
    """Occupancy flags implied by current rule rows (must match the spec's flags)."""
    flags = set()
    for prov, val, f, t, *_ in m["rules"]:
        if t:
            continue
        if prov == "owner_occupancy" and val in ("ongoing", "at_permit"):
            flags.add("owner_occupancy")
        if prov == "occupant_restriction" and val in ("related_only", "employee_only", "other"):
            flags.add("related_occupant")
    return flags


pr_rows, re_rows, errors = [], [], []
for m in spec.M:
    jid = m["ids"][0]
    cnt = collections.Counter()
    ids = []

    def add(prov, val, f, t, url, sec, ver, note, retrieved=spec.R, jid=jid, cnt=cnt, ids=ids, m=m):
        cnt[prov] += 1
        rid = f"wi{jid}_{prov}_{cnt[prov]}"
        ids.append(rid)
        pr_rows.append(dict(rule_id=rid, jurisdiction_id=jid, jurisdiction_name=m["name"], provision=prov, value=val,
                            effective_from=f, effective_to=t, source_url=url, source_section=sec, retrieved=retrieved,
                            verification=ver, notes=note))
        return rid

    for r in m["rules"]:
        add(*r)
    paths = pathway(m)
    for v, f, t, url, sec, ver, note in paths:
        add("approval_pathway", v, f, t, url, sec, ver, note)
    cur_path = next((p[0] for p in paths if not p[2]), "unknown")
    m["_ids"], m["_path"], m["_add"] = ids, cur_path, add

    cur, flags = m["cls"], m["flags"]
    occ = occupancy_flags(m)
    if cur == "restricted":
        if not flags:
            errors.append(f"{m['name']}: restricted but no flags")
        if occ != set(flags) & set(OCC_FLAGS):
            errors.append(f"{m['name']}: occupancy flags {sorted(set(flags) & set(OCC_FLAGS))} != rules {sorted(occ)}")
        if cur_path == "discretionary" and "discretionary_review" not in flags:
            errors.append(f"{m['name']}: discretionary pathway but no discretionary_review flag")
    elif flags:
        errors.append(f"{m['name']}: flags given for class {cur}")
    bad = set(flags) - RESTRICTION_FLAGS
    if bad:
        errors.append(f"{m['name']}: unknown flags {sorted(bad)}")
    if ("size_below_benchmark" in flags) != (m["name"] in spec.SIZE_BINDS):
        errors.append(f"{m['name']}: size_below_benchmark flag and SIZE_BINDS entry must go together")
    exp_note = m["note"]
    if m["name"] in spec.SIZE_BINDS:
        exp_note = (exp_note + " " if exp_note else "") + "Size cap binds: " + spec.SIZE_BINDS[m["name"]] + "."
    keep = [f for f in flags if f in OCC_FLAGS]
    for k, gid in enumerate(m["ids"]):
        name = m["name"] + ("" if k == 0 else " (part in another county)")
        for scen in ("adu_full", "adu_form_only"):
            if cur in ("scenario_benchmark", "no_zoning"):
                ref, rest_after, txt = cur, [], m["added"]
            elif scen == "adu_form_only" and keep:
                ref, rest_after = "restricted", keep
                txt = ("Form-only variant: forms, size, parking and process as in adu_full, but local "
                       + " and ".join(f.replace("_", "-") for f in keep) + " rules stay. Full: " + m["added"])
            else:
                ref, rest_after, txt = "scenario_benchmark", [], m["added"]
            re_rows.append(dict(jurisdiction_id=gid, jurisdiction_name=name, scenario_id=scen, current_class=cur,
                                reform_class=ref, class_basis=m["basis"], rules_as_of=m["as_of"],
                                restrictions=";".join(flags), reform_restrictions=";".join(rest_after),
                                approval_pathway=cur_path, rights_added_text=txt, rule_ids=";".join(ids),
                                aq023_default_class="undetermined",
                                default_matches_coded=str(cur.startswith("prohibited")).lower(), notes=exp_note))

# First pass: ordinance_status rows
scan = {}
sp = os.path.join(sys.argv[3], "scan.csv") if len(sys.argv) > 3 else None
if sp:
    for r in csv.DictReader(open(sp)):
        scan[r["jurisdiction_name"]] = r
for m in spec.M:
    s = scan.get(m["name"])
    add = m["_add"]
    manual = spec.MANUAL_FIRST_PASS.get(m["name"])
    if s and s["result"] in ("mentions_adu", "no_mention") and not manual:
        if s["result"] == "mentions_adu":
            val, why = spec.FIRST_PASS_HIT_STATUS.get(m["name"], ("mentioned_allowed", ""))
        else:
            val, why = "unmentioned", ""
        kind = s.get("document_kind", "")
        note = (f"automated scan {s['scan_date']}: host={s['code_host']}; document={kind}; method={s['search_method']}; "
                f"HTTP {s['http_status']}; terms={s['matched_terms'] or 'none'}; sha256={s['sha256'][:12]}")
        if m["name"] in spec.SCAN_DOC_NOTE:
            note += "; " + spec.SCAN_DOC_NOTE[m["name"]]
        if why:
            note += "; " + why
        ver = "source_lead" if kind == "mirror" else "verified"
        add("ordinance_status", val, "", "", s["url_searched"], s["first_hit_section"], ver, note, retrieved=s["scan_date"])
    elif manual:
        val, sec, terms, ver, how = manual
        if s:
            got = ("could_not_access" if s["result"] == "could_not_access"
                   else "scanned document is not the code text (" + s["result"] + ")")
            pre = f"automated scan {s['scan_date']}: host={s['code_host']}; HTTP {s['http_status']} -> {got}; "
            url, ret = s["url_searched"], s["scan_date"]
        else:
            pre, url, ret = "not scanned; ", m["rules"][0][4], spec.R
        add("ordinance_status", val, "", "", url, sec, ver,
            pre + f"manual first pass 2026-10-23: {how}; terms={terms or 'none'}", retrieved=ret)
    else:
        add("ordinance_status", "could_not_access", "", "", m["rules"][0][4], "", "unknown", "no scan row and no manual reading")
    # keep exposure rule_ids complete
    for row in re_rows:
        if row["jurisdiction_id"] in m["ids"]:
            row["rule_ids"] = ";".join(m["_ids"])

if errors:
    for e in errors:
        print("SPEC ERROR:", e)
    sys.exit(1)
pr_rows.sort(key=lambda r: [x["ids"][0] for x in spec.M].index(r["jurisdiction_id"]))
for fn, cols, rows in (("wi_adu_rules.csv", PR, pr_rows), ("wi_rights_exposure.csv", RE, re_rows)):
    with open(f"{out}/{fn}", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(fn, len(rows))
