"""Regenerate reference/wi_adu_rules.csv and reference/wi_rights_exposure.csv from the hand-coded spec.

Usage: uv run python scripts/build_reference_rules.py reference reference [data/processed/adu_mention_scan]
(args: spec directory, output directory, optional scan directory). The spec in
reference/wi_adu_rules_spec.py is the human-edited record of each coding and its source.
"""
import csv, sys, collections
sys.path.insert(0, sys.argv[1])
import wi_adu_rules_spec as spec

out = sys.argv[2]
PR = ["rule_id", "jurisdiction_id", "jurisdiction_name", "provision", "value", "effective_from", "effective_to",
      "source_url", "source_section", "retrieved", "verification", "notes"]
RE = ["jurisdiction_id", "jurisdiction_name", "scenario_id", "current_class", "reform_class", "class_basis",
      "rules_as_of", "rights_added_text", "rule_ids", "aq023_default_class", "default_matches_coded", "notes"]
pr_rows, re_rows = [], []
for m in spec.M:
    jid = m["ids"][0]
    cnt = collections.Counter()
    ids, occ = [], False
    for prov, val, f, t, url, sec, ver, note in m["rules"]:
        cnt[prov] += 1
        rid = f"wi{jid}_{prov}_{cnt[prov]}"
        ids.append(rid)
        pr_rows.append(dict(rule_id=rid, jurisdiction_id=jid, jurisdiction_name=m["name"], provision=prov, value=val,
                            effective_from=f, effective_to=t, source_url=url, source_section=sec, retrieved=spec.R,
                            verification=ver, notes=note))
        if not t and ((prov == "owner_occupancy" and val in ("ongoing", "at_permit")) or
                      (prov == "occupant_restriction" and val == "related_only")):
            occ = True
    cur = m["cls"]
    for k, gid in enumerate(m["ids"]):
        name = m["name"] + ("" if k == 0 else " (part in another county)")
        for scen in ("adu_full", "adu_form_only"):
            if cur in ("compliant", "no_zoning"):
                ref, txt = cur, m["added"]
            elif scen == "adu_full":
                ref, txt = "compliant", m["added"]
            elif occ:
                ref, txt = "forms_with_occupancy_limits", "Form-only variant: forms and size/parking as in adu_full, but local owner-occupancy or related-occupant rules stay. Full: " + m["added"]
            else:
                ref, txt = "compliant", m["added"]
            re_rows.append(dict(jurisdiction_id=gid, jurisdiction_name=name, scenario_id=scen, current_class=cur,
                                reform_class=ref, class_basis=m["basis"], rules_as_of=m["as_of"], rights_added_text=txt,
                                rule_ids=";".join(ids), aq023_default_class="prohibited",
                                default_matches_coded=str(cur == "prohibited").lower(), notes=m["note"]))
scan = {}
import os
sp = os.path.join(sys.argv[3], "scan.csv") if len(sys.argv) > 3 else None
if sp:
    for r in csv.DictReader(open(sp)):
        scan[r["jurisdiction_name"]] = r
for m in spec.M:
    s = scan.get(m["name"])
    if not s:
        continue
    jid = m["ids"][0]
    if s["result"] in ("mentions_adu", "no_mention") and m["name"] not in spec.MANUAL_MENTIONS:
        val = "mentions_adu: " + ("yes" if s["result"] == "mentions_adu" else "no")
        note = f"automated scan {s['scan_date']}: host={s['code_host']}; method={s['search_method']}; HTTP {s['http_status']}; terms={s['matched_terms'] or 'none'}; sha256={s['sha256'][:12]}"
        if m["name"] in spec.SCAN_DOC_NOTE:
            note += "; " + spec.SCAN_DOC_NOTE[m["name"]]
        pr_rows.append(dict(rule_id=f"wi{jid}_mentions_adu_1", jurisdiction_id=jid, jurisdiction_name=m["name"], provision="other",
                            value=val, effective_from="", effective_to="", source_url=s["url_searched"], source_section=s["first_hit_section"],
                            retrieved=s["scan_date"], verification="verified", notes=note))
    else:
        res, sec, terms, ver, how = spec.MANUAL_MENTIONS[m["name"]]
        note = f"automated scan {s['scan_date']}: host={s['code_host']}; HTTP {s['http_status']} -> {'could_not_access' if s['result']=='could_not_access' else 'scanned document is not the code text (' + s['result'] + ')'}; manual first pass 2026-10-23: {how}; terms={terms or 'none'}"
        pr_rows.append(dict(rule_id=f"wi{jid}_mentions_adu_1", jurisdiction_id=jid, jurisdiction_name=m["name"], provision="other",
                            value="mentions_adu: " + res, effective_from="", effective_to="", source_url=s["url_searched"], source_section=sec,
                            retrieved=s["scan_date"], verification=ver, notes=note))
for fn, cols, rows in (("wi_adu_rules.csv", PR, pr_rows), ("wi_rights_exposure.csv", RE, re_rows)):
    with open(f"{out}/{fn}", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    print(fn, len(rows))
