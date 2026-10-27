"""Combine the transit-oriented density (TOD) and parking reforms into one result set for the tool.

Rules: docs/shared/SCENARIO_CONTRACT.md section 9 (AQ-047, AQ-048, AQ-050).

- Inputs are each reform's published additions (ui/public/scenarios/<tod|parking>/runs/<run>/additions_by_area.json)
  and the shared all-housing baseline (reference/housing_baseline_by_area.csv, for current law and names), with
  reference/tod_near_stop_homes_by_muni.csv for county names and the share of homes near stops.
- The builder refuses bundles built on different baselines (`baseline_version`), and pairs paths by role:
  lower with lower, central with central, upper with upper. Paths are never crossed.
- Within each municipality the `elsewhere` parts are added. The `near_stops` parts are shown under two rules side by
  side: (a) the sum, which double-counts any overlap; (b) the larger of the two, taken per municipality and year.
  Rule (c), the sum minus a measured overlap term, has no measurement yet, so the bundle carries a note and no number.
- Neither reform's own numbers change; this is a separate bundle with its own run id.

Output: ui/public/scenarios/combined/runs/<run_id>/*.json and latest.json. The run id hashes the input files, so the
same inputs give the same bundle byte for byte.

Run (after build_tod_bundle.py and build_parking_bundle.py): uv run python scripts/build_combined_bundle.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
PUBLIC = ROOT / "ui" / "public" / "scenarios"
OUT_ROOT = PUBLIC / "combined" / "runs"
REPO_URL = "https://github.com/mroconnell/housing-challenge-starter-missingmiddleware"
ROLES = ["lower", "central", "upper"]
# order of the five-year values in each area row of areas.json (role -> list)
COLS = ("tod", "parking_near", "parking_elsewhere", "total_a", "total_b")
PARTS = ("near_stops", "elsewhere")
RULES = {
    "a": {"label": "Rule (a): add both near stops",
          "info": "Near stops, both reforms' additions are added. If the same new building would be counted by both reforms, it is counted twice, so this is the high reading."},
    "b": {"label": "Rule (b): the larger of the two near stops",
          "info": "Near stops, each place gets whichever reform adds more there in that year, as if the smaller one were already inside the larger. This is the low reading."},
}
RULE_C = ("Rule (c), adding both and then subtracting the overlap measured in cities that did both reforms, is a "
          "sensitivity case only and has no number yet. The cities that could measure it differ from Wisconsin and "
          "from each other: New York kept its parking minimums near transit, while Charlotte, Chicago and Saint Paul "
          "cut them, in different markets and decades.")
DOUBLE_COUNT = ("Both reforms make it easier to build apartments near frequent transit. A building that goes ahead "
                "because the law allows more height and also because it no longer needs a parking garage would be "
                "counted once by each reform's estimate. Adding the two estimates near stops counts it twice. Away "
                "from stops only the parking reform acts, so there is nothing to double count and the two are simply "
                "added.")


class CombineError(ValueError):
    """The two bundles cannot be combined (different baselines, years or role mappings)."""


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def r(v: float, nd: int = 4) -> float:
    x = round(float(v), nd)
    return 0.0 if x == 0 else x


def latest_additions(reform: str) -> tuple[str, Path]:
    run = json.loads((PUBLIC / reform / "runs" / "latest.json").read_text())["run_id"]
    return run, PUBLIC / reform / "runs" / run / "additions_by_area.json"


def by_role(add: dict) -> dict[str, dict[tuple[str, str], list[float]]]:
    """{role: {(area_id, part): yearly values}} using the reform's own role -> path mapping."""
    paths = {p["id"] for p in add["paths"]}
    roles = add.get("roles", {})
    out = {}
    for role in ROLES:
        path = roles.get(role)
        if path not in paths:
            raise CombineError(f"{add.get('reform')}: role {role!r} maps to {path!r}, which is not one of its paths {sorted(paths)}")
        vals = {}
        for a in add["areas"]:
            part = a.get("part", "elsewhere")
            if part not in PARTS:
                raise CombineError(f"{add.get('reform')}: unknown part {part!r} for {a['area_id']}")
            key = (a["area_id"], part)
            if key in vals:
                raise CombineError(f"{add.get('reform')}: {a['area_id']} {part} listed twice")
            v = [float(x) for x in a[path]]
            if len(v) != len(add["years"]):
                raise CombineError(f"{add.get('reform')}: {a['area_id']} has {len(v)} years, expected {len(add['years'])}")
            vals[key] = v
        out[role] = {"path": path, "values": vals}
    return out


def combine(tod: dict, parking: dict) -> dict:
    """Pair the two reforms' additions by role and apply the rules. Pure function: tests call it directly.

    Returns {"years", "baseline_version", "pairing", "areas": {area_id: {role: {...yearly lists...}}}}."""
    if tod.get("baseline_version") != parking.get("baseline_version"):
        raise CombineError(f"baseline_version differs: TOD {tod.get('baseline_version')!r}, parking {parking.get('baseline_version')!r}")
    if not tod.get("baseline_version"):
        raise CombineError("baseline_version is missing")
    if list(tod["years"]) != list(parking["years"]):
        raise CombineError(f"years differ: TOD {tod['years']}, parking {parking['years']}")
    if any(a.get("part") != "near_stops" for a in tod["areas"]):
        raise CombineError("TOD acts only near stops, but a TOD row is not part 'near_stops'")
    years = list(tod["years"])
    zero = [0.0] * len(years)
    T, P = by_role(tod), by_role(parking)
    labels = {x["id"]: x["label"] for x in tod["paths"]}, {x["id"]: x["label"] for x in parking["paths"]}
    pairing = [{"role": role, "tod_path": T[role]["path"], "tod_label": labels[0][T[role]["path"]],
                "parking_path": P[role]["path"], "parking_label": labels[1][P[role]["path"]]} for role in ROLES]
    ids = sorted({k[0] for k in T["central"]["values"]} | {k[0] for k in P["central"]["values"]})
    areas = {}
    for aid in ids:
        areas[aid] = {}
        for role in ROLES:
            t = T[role]["values"].get((aid, "near_stops"), zero)
            pn = P[role]["values"].get((aid, "near_stops"), zero)
            pe = P[role]["values"].get((aid, "elsewhere"), zero)
            near_a = [x + y for x, y in zip(t, pn)]
            near_b = [max(x, y) for x, y in zip(t, pn)]
            areas[aid][role] = {"tod": t, "parking_near": pn, "parking_elsewhere": pe, "near_a": near_a, "near_b": near_b,
                                "total_a": [x + y for x, y in zip(near_a, pe)], "total_b": [x + y for x, y in zip(near_b, pe)]}
    return {"years": years, "baseline_version": tod["baseline_version"], "pairing": pairing, "areas": areas}


def names() -> tuple[dict, dict, dict]:
    """Municipality name and county, current-law five-year baseline, and share of homes near stops."""
    b = pd.read_csv(REF / "housing_baseline_by_area.csv", dtype={"county_id": str})
    near = pd.read_csv(REF / "tod_near_stop_homes_by_muni.csv")
    county = {aid[5:10]: c for aid, c in zip(near["area_id"], near["county"])}
    first = b.drop_duplicates("area_id").set_index("area_id")
    info = {aid: {"name": row["name"], "county_id": row["county_id"], "county": county.get(str(row["county_id"]))}
            for aid, row in first.iterrows() if aid.startswith("muni:")}
    base = b.groupby("area_id")["five_year_central"].sum().to_dict()
    share = near.set_index("area_id")["share_near_main"].to_dict()
    return info, base, share


def totals(c: dict, role: str, key: str) -> list[float]:
    n = len(c["years"])
    return [sum(a[role][key][i] for a in c["areas"].values()) for i in range(n)]


def build(c: dict, tod_meta: dict, park_meta: dict) -> tuple[dict, dict]:
    info, base, share = names()
    years = c["years"]
    base_total = sum(base.values())
    roles = []
    for p in c["pairing"]:
        role = p["role"]
        t = totals(c, role, "tod")
        pn, pe = totals(c, role, "parking_near"), totals(c, role, "parking_elsewhere")
        na, nb = totals(c, role, "near_a"), totals(c, role, "near_b")
        series = {
            "tod": t, "parking": [x + y for x, y in zip(pn, pe)], "parking_near": pn, "parking_elsewhere": pe,
            "near_a": na, "near_b": nb, "both_a": [x + y for x, y in zip(na, pe)], "both_b": [x + y for x, y in zip(nb, pe)],
        }
        roles.append({**p, "by_year": {k: [r(v, 2) for v in vs] for k, vs in series.items()},
                      "total": {k: r(sum(vs), 2) for k, vs in series.items()},
                      "overlap_counted_twice": r(sum(na) - sum(nb), 2)})
    statewide = {
        "years": years, "baseline_total": r(base_total, 2),
        "baseline_note": "Current law, 2027–2031, all building sizes, from the shared all-housing baseline (the same for every pairing). It includes a small statewide adjustment not assigned to any place.",
        "roles": roles, "rules": RULES, "rule_c": RULE_C, "double_count": DOUBLE_COUNT,
        "role_labels": {"lower": "Low pairing", "central": "Central pairing", "upper": "High pairing"},
    }
    munis, counties = [], {}
    for aid, roles_v in c["areas"].items():
        meta = info.get(aid, {"name": aid, "county_id": None, "county": None})
        row = {"id": aid, "name": meta["name"], "county": meta["county"], "baseline": r(base.get(aid, 0.0), 2),
               "share_near": r(share.get(aid, 0.0), 4)}
        for role in ROLES:
            row[role] = [r(sum(roles_v[role][k]), 2) for k in COLS]
        munis.append(row)
        cid = meta["county_id"] or "unknown"
        cty = counties.setdefault(cid, {"id": cid, "name": meta["county"] or "County not known", "places": 0, "baseline": 0.0,
                                        **{role: [0.0] * len(COLS) for role in ROLES}})
        cty["places"] += 1
        cty["baseline"] += base.get(aid, 0.0)
        for role in ROLES:
            for i, k in enumerate(COLS):
                cty[role][i] += sum(roles_v[role][k])
    for cty in counties.values():
        cty["baseline"] = r(cty["baseline"], 2)
        for role in ROLES:
            cty[role] = [r(v, 2) for v in cty[role]]
    ia = COLS.index("total_a")
    munis.sort(key=lambda m: (-m["upper"][ia], m["name"]))
    areas = {"munis": munis, "counties": sorted(counties.values(), key=lambda x: (-x["upper"][ia], x["name"])),
             "cols": list(COLS), "col_labels": {"tod": "TOD alone (near stops)", "parking_near": "Parking alone, near stops",
                                                "parking_elsewhere": "Parking alone, elsewhere", "total_a": "Both, rule (a)", "total_b": "Both, rule (b)"},
             "sources": {"tod": tod_meta["run_id"], "parking": park_meta["run_id"]}}
    return statewide, areas


def validate(c: dict, statewide: dict, areas: dict) -> dict:
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
    check("both bundles use the same baseline", True, c["baseline_version"])
    check("paths paired by role, never crossed", [p["role"] for p in c["pairing"]] == ROLES,
          "; ".join(f"{p['role']}: {p['tod_path']} + {p['parking_path']}" for p in c["pairing"]))
    eps = 1e-6
    b_le_a = all(b <= a + eps for v in c["areas"].values() for role in ROLES for a, b in zip(v[role]["near_a"], v[role]["near_b"]))
    check("rule (b) never exceeds rule (a)", b_le_a, "every place, year and role")
    b_ge = all(b + eps >= max(t, p) for v in c["areas"].values() for role in ROLES
               for t, p, b in zip(v[role]["tod"], v[role]["parking_near"], v[role]["near_b"]))
    check("rule (b) is at least each reform alone", b_ge, "every place, year and role")
    rec = all(abs(x["total"]["both_a"] - x["total"]["tod"] - x["total"]["parking"]) < 0.05 for x in statewide["roles"])
    check("rule (a) total equals TOD plus parking", rec, "every role")
    ia, ib = COLS.index("total_a"), COLS.index("total_b")
    m_tot = all(abs(sum(m[x["role"]][ia] for m in areas["munis"]) - x["total"]["both_a"]) < 1
                and abs(sum(m[x["role"]][ib] for m in areas["munis"]) - x["total"]["both_b"]) < 1 for x in statewide["roles"])
    check("places add up to the statewide totals", m_tot, "both rules, every role")
    check("no place below zero", all(v >= 0 for m in areas["munis"] for role in ROLES for v in m[role]), "every role")
    check("every place has a name", all(not m["name"].startswith("muni:") for m in areas["munis"]), f"{len(areas['munis'])} places")
    return {"passed": sum(x["passed"] for x in checks), "failed": sum(not x["passed"] for x in checks), "checks": checks}


def main():
    tod_run, tod_path = latest_additions("tod")
    park_run, park_path = latest_additions("parking")
    inputs = ["scripts/build_combined_bundle.py", str(tod_path.relative_to(ROOT)), str(park_path.relative_to(ROOT)),
              "reference/housing_baseline_by_area.csv", "reference/tod_near_stop_homes_by_muni.csv"]
    hashes = [{"path": p, "sha256": sha256(ROOT / p)} for p in inputs]
    run_id = "combined-" + hashlib.sha256("".join(h["sha256"] for h in hashes).encode()).hexdigest()[:10]
    tod, park = json.loads(tod_path.read_text()), json.loads(park_path.read_text())
    c = combine(tod, park)  # raises CombineError on a baseline mismatch, before anything is written
    tod_m = json.loads((tod_path.parent / "manifest.json").read_text())
    park_m = json.loads((park_path.parent / "manifest.json").read_text())
    statewide, areas = build(c, tod_m, park_m)
    val = validate(c, statewide, areas)
    out = OUT_ROOT / run_id
    if OUT_ROOT.exists():
        for old in OUT_ROOT.iterdir():
            if old.is_dir() and old.name != run_id:
                shutil.rmtree(old)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1, "run_id": run_id, "scenario_id": "combined", "title": "Transit-oriented density and parking reform together",
        "outcome": {"short": "Extra homes in issued building permits from a transit-oriented density law and a parking law together, compared with current law, Wisconsin, 2027–2031. Not completed homes.",
                    "long": "Housing units authorized by building permits, counted at permit issuance, all building sizes. Each reform's addition over current law comes from its own bundle; near major transit stops the two are combined under two rules shown side by side, and elsewhere they are added.",
                    "rate_units": "extra homes permitted per year", "count_units": "homes (housing units) in issued permits"},
        "dates": {"last_observed_year": 2025, "forecast_years": c["years"], "effective": "Both stylized statewide laws in effect 1 January 2027"},
        "vintages": [{"what": "Transit-oriented density bundle", "vintage": tod_run}, {"what": "Parking bundle", "vintage": park_run},
                     {"what": "Shared all-housing baseline", "vintage": c["baseline_version"]}],
        "validation": val, "repo_url": REPO_URL, "inputs": hashes,
        "baseline_version": c["baseline_version"], "sources": {"tod": tod_run, "parking": park_run},
        "files": ["statewide.json", "areas.json"],
    }
    for name, obj in {"manifest.json": manifest, "statewide.json": statewide, "areas.json": areas}.items():
        (out / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")
    (OUT_ROOT / "latest.json").write_text(json.dumps({"run_id": run_id}) + "\n")
    print(run_id, f"validation {val['passed']} passed, {val['failed']} failed")
    for x in statewide["roles"]:
        t = x["total"]
        print(f"  {x['role']}: TOD {t['tod']:,.0f} + parking {t['parking']:,.0f}; both (a) {t['both_a']:,.0f}, (b) {t['both_b']:,.0f}")
    for x in val["checks"]:
        if not x["passed"]:
            print("FAILED", x)


if __name__ == "__main__":
    main()
