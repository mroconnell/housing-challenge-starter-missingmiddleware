"""Madison-like cities in statewide-ADU-law states (Gate 3 add-on, owner question 2026-10-25).

Definition (pre-registered in docs/gate3/MADISON_LIKE_CITIES.md section 0, before outcomes):
an incorporated place with 20,000-120,000 one-unit detached homes (ACS 2020-2024 B25024_002)
and a median owner home value of $250,000-$500,000 (B25077_001), not its state's largest city.

Outcome: ADU permits per 1,000 one-unit detached homes per year, one fixed ACS denominator.
    Washington: OFM permits workbook, 'Permitted Accessory Dwelling units', estimate years.
    Oregon:     DLCD HB 4006 annual summaries (permitted ADU column), calendar years.
    California: HCD APR Table A2 ADU building-permit units (study's primary measure), with the
                Building an ADU 2012-2019 compilation for the years before 2018.
    Rhode Island: EOH annual ADU report municipal counts (2023-2025).

Everything here is descriptive. Rates after a law are associated with the law, not caused by it.
"""
from __future__ import annotations

import re
import statistics
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# 0. Pre-registered definition
# ---------------------------------------------------------------------------
HOMES_MIN, HOMES_MAX = 20_000, 120_000
VALUE_MIN, VALUE_MAX = 250_000, 500_000
STATES = {"53": "WA", "41": "OR", "23": "ME", "50": "VT", "44": "RI", "06": "CA"}
MAIN_STATES = ("WA", "OR", "ME", "VT", "RI")
LARGEST_CITY = {"WA": "Seattle", "OR": "Portland", "CA": "Los Angeles", "RI": "Providence",
                "ME": "Portland", "VT": "Burlington"}
STATE_CAPITALS = {"WA": "Olympia", "OR": "Salem", "CA": "Sacramento", "RI": "Providence",
                  "ME": "Augusta", "VT": "Montpelier"}

# Model comparison lines (POOLED_MODEL.md section B; README.md), permits per 1,000 single-family
# homes per year.
MODEL_PATH = {1: 0.83, 2: 1.03, 3: 1.07, 4: 1.30}
MADISON_PLATEAU = 1.75
MADISON_CURRENT = 0.18

# Year 1 of each statewide law (same coding as POOLED_MODEL.md section A).
LAW_YEAR1 = {"WA": 2024, "OR": 2019, "CA": 2017, "RI": 2025}
LAW_LABEL = {"WA": "HB 1337, effective 2023-07-23 (year 1 = OFM EY2024)",
             "OR": "SB 1051, effective 2018-07-01 (2018 = law year, dropped; year 1 = 2019)",
             "CA": "SB 1069 / AB 2299, effective 2017-01-01 (year 1 = 2017)",
             "RI": "P.L. 2024 ch. 284/285, effective 2024-06-25 (2024 = law year, dropped; year 1 = 2025)"}
BEFORE_WINDOW = {"WA": (2019, 2023), "CA": (2014, 2016), "RI": (2023, 2023)}


def place_base_name(placename: str) -> str:
    return re.sub(r" (city|town|CDP|municipality|village)$", "", placename)


def read_place_codes(files: list[Path]) -> pd.DataFrame:
    df = pd.concat([pd.read_csv(f, sep="|", dtype=str) for f in files], ignore_index=True)
    df["geo_id"] = "1600000US" + df["STATEFP"] + df["PLACEFP"]
    df["name"] = df["PLACENAME"].map(place_base_name)
    return df[["geo_id", "STATE", "STATEFP", "PLACEFP", "PLACENAME", "name", "CLASSFP"]]


def read_acs_values(path: Path, column: str, prefixes: tuple[str, ...]) -> pd.Series:
    """One estimate column from an ACS table-based summary file, for GEO_IDs with given prefixes."""
    out = {}
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("|")
        i = header.index(column)
        for line in f:
            if line.startswith(prefixes):
                p = line.rstrip("\n").split("|")
                v = pd.to_numeric(p[i], errors="coerce")
                out[p[0]] = v if (v is not None and v >= 0) else float("nan")
    return pd.Series(out, name=column, dtype=float)


def screen(places: pd.DataFrame, homes: pd.Series, value: pd.Series) -> pd.DataFrame:
    """All incorporated places in the six states with their screen result. `madison_like` is the
    pre-registered rule; `fail_reason` says which test failed."""
    d = places[places["CLASSFP"].str.startswith("C")].copy()
    d["homes"] = d["geo_id"].map(homes)
    d["median_value"] = d["geo_id"].map(value)
    d = d[d["homes"].notna()]
    size_ok = d["homes"].between(HOMES_MIN, HOMES_MAX)
    value_ok = d["median_value"].between(VALUE_MIN, VALUE_MAX)
    largest = d.apply(lambda r: LARGEST_CITY.get(r["STATE"]) == r["name"], axis=1)
    d["madison_like"] = size_ok & value_ok & ~largest
    reasons = []
    for s, v, lg in zip(size_ok, value_ok, largest):
        r = [x for x, bad in (("size", not s), ("value", not v), ("largest_city", lg)) if bad]
        reasons.append(";".join(r))
    d["fail_reason"] = reasons
    return d


def university_flags(ipeds_hd: Path, cities: pd.DataFrame) -> pd.DataFrame:
    """Flag cities that are a state capital or contain a degree-granting four-year institution with
    10,000+ students (IPEDS HD2023: ICLEVEL 1, DEGGRANT 1, INSTSIZE 4 or 5). Matched on city name
    and state in the institution's address; Carnegie 2021 basic class 15 or higher."""
    hd = pd.read_csv(ipeds_hd, encoding="latin-1", dtype=str,
                     usecols=["INSTNM", "CITY", "STABBR", "ICLEVEL", "DEGGRANT", "INSTSIZE", "C21BASIC"])
    # Carnegie 2021 basic class 15+ = doctoral, master's or baccalaureate (drops community colleges
    # that grant a few bachelor's degrees and so carry ICLEVEL 1).
    big = hd[(hd["ICLEVEL"] == "1") & (hd["DEGGRANT"] == "1") & hd["INSTSIZE"].isin(["4", "5"])
             & (pd.to_numeric(hd["C21BASIC"], errors="coerce") >= 15)]
    rows = []
    for _, c in cities.iterrows():
        hit = big[(big["STABBR"] == c["STATE"]) & (big["CITY"].str.strip().str.lower() == c["name"].lower())]
        capital = STATE_CAPITALS.get(c["STATE"]) == c["name"]
        rows.append(dict(geo_id=c["geo_id"], state_capital=capital,
                         universities_10k=";".join(sorted(hit["INSTNM"])),
                         university_or_capital=bool(capital or len(hit))))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 1. Washington: OFM workbook (stdlib xlsx reader; the project has no Excel dependency)
# ---------------------------------------------------------------------------
_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _col(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx_sheet(path: Path, sheet: str) -> list[list[str]]:
    z = zipfile.ZipFile(path)
    try:
        sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
        shared = ["".join(t.text or "" for t in si.iter(_NS + "t")) for si in sst.findall(_NS + "si")]
    except KeyError:
        shared = []
    rows = []
    for _, el in ET.iterparse(z.open(sheet)):
        if el.tag == _NS + "row":
            r: dict[int, str] = {}
            for c in el.findall(_NS + "c"):
                t, v = c.get("t"), c.find(_NS + "v")
                if t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter(_NS + "t"))
                elif v is None:
                    continue
                else:
                    val = shared[int(v.text)] if t == "s" else v.text
                r[_col(c.get("r"))] = val
            rows.append([r.get(i, "") for i in range(max(r) + 1)] if r else [])
            el.clear()
    return rows


OFM_ADU_COL = "Permitted Accessory Dwelling units"
OFM_SFD_COL = "Permitted Single Family units"


def ofm_city_counts(rows: list[list[str]], cities: list[str]) -> pd.DataFrame:
    """Long table city x estimate year: permitted ADUs and single-family units."""
    header = rows[0]
    i_city, i_year = header.index("City Name"), header.index("Estimate Year")
    i_adu, i_sfd = header.index(OFM_ADU_COL), header.index(OFM_SFD_COL)
    out = []
    width = len(header)
    for r in rows[1:]:
        r = r + [""] * (width - len(r))  # trailing blank cells are absent in xlsx: missing, not zero
        if r[i_city] in cities:
            out.append(dict(city=r[i_city], year=int(r[i_year]),
                            adu_permits=float(r[i_adu]) if r[i_adu] != "" else float("nan"),
                            sfd_permits=float(r[i_sfd]) if r[i_sfd] != "" else float("nan")))
    df = pd.DataFrame(out)
    if df.duplicated(["city", "year"]).any():
        raise ValueError("duplicate OFM city-year rows (city name not unique across counties)")
    return df


# ---------------------------------------------------------------------------
# 2. Oregon: DLCD HB 4006 summaries (pdftotext -layout text)
# ---------------------------------------------------------------------------

def dlcd_year(text: str, fallback: int | None = None) -> int:
    m = re.search(r"Year:\s*(20\d\d)", text)
    if m:
        return int(m.group(1))
    if fallback is None:
        raise ValueError("no year in DLCD text")
    return fallback


def dlcd_adu_permitted(text: str, city: str) -> tuple[float, str]:
    """ADUs permitted for `city` from the first (all-units, permitted) table of one summary.
    Columns: total, SF total, SF detached, SF attached, duplex, ADU, manufactured, ...
    Checked: SF total = detached + attached + duplex + ADU + manufactured. Returns (value, check)."""
    for line in text.splitlines():
        m = re.match(rf"^{re.escape(city)}\s{{2,}}(.*)$", line)
        if not m:
            continue
        nums = [float(x) for x in re.findall(r"-?\d+", m.group(1))]
        if len(nums) >= 7 and abs(nums[1] - sum(nums[2:7])) < 0.5:
            return nums[5], "sf_total_check_ok"
        return float("nan"), "row_incomplete_or_check_failed"
    return float("nan"), "city_not_reported"


# ---------------------------------------------------------------------------
# 3. City annual series -> rates by year since law
# ---------------------------------------------------------------------------

def add_rates(annual: pd.DataFrame, homes: dict[str, float]) -> pd.DataFrame:
    a = annual.copy()
    a["homes"] = a["geo_id"].map(homes)
    a["rate_per_1000"] = a["adu_permits"] / a["homes"] * 1000
    a["year_since_law"] = [y - LAW_YEAR1[s] + 1 if s in LAW_YEAR1 else None
                           for s, y in zip(a["state"], a["year"])]
    return a


def before_rates(annual: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (gid, st), g in annual.groupby(["geo_id", "state"]):
        if st not in BEFORE_WINDOW:
            continue
        y0, y1 = BEFORE_WINDOW[st]
        w = g[g["year"].between(y0, y1) & g["adu_permits"].notna()]
        if len(w) == 0:
            continue
        n, yrs, h = w["adu_permits"].sum(), len(w), w["homes"].iloc[0]
        rows.append(dict(geo_id=gid, before_window=f"{y0}-{y1}", before_years=yrs, before_permits=n,
                         before_rate_per_1000=n / yrs / h * 1000))
    return pd.DataFrame(rows)


def median_path(rates: pd.DataFrame, group: str, min_year: int = 1, max_year: int = 9) -> pd.DataFrame:
    """Unweighted median city rate and pooled rate (sum permits / sum homes) by year since law."""
    out = []
    r = rates[rates["year_since_law"].between(min_year, max_year) & rates["adu_permits"].notna()]
    for y, g in r.groupby("year_since_law"):
        out.append(dict(group=group, year_since_law=int(y), n_cities=len(g),
                        median_rate=statistics.median(g["rate_per_1000"]),
                        min_rate=g["rate_per_1000"].min(), max_rate=g["rate_per_1000"].max(),
                        pooled_permits=g["adu_permits"].sum(), pooled_homes=g["homes"].sum(),
                        pooled_rate=g["adu_permits"].sum() / g["homes"].sum() * 1000,
                        model_typical_state=MODEL_PATH.get(min(int(y), 4))))
    return pd.DataFrame(out)


def verdict(path: pd.DataFrame, min_cities: int = 5) -> tuple[str, str]:
    """Pre-registered rule (doc section 0)."""
    ok = path[path["n_cities"] >= min_cities]
    if ok.empty or ok["year_since_law"].max() < 2:
        return "cannot_yet_test", "fewer than 5 cities with data in year 2 or later"
    late = ok[ok["year_since_law"] >= 3]
    if not late.empty and (late["median_rate"] < 0.8).any():
        y = int(late.loc[late["median_rate"] < 0.8, "year_since_law"].iloc[-1])
        m = float(late.loc[late["year_since_law"] == y, "median_rate"].iloc[0])
        return "contradicts", f"median {m:.2f} < 0.8 in year {y} with >= {min_cities} cities"
    last = ok.loc[ok["year_since_law"].idxmax()]
    if last["median_rate"] >= 1.0:
        return "supports", f"median {last['median_rate']:.2f} >= 1.0 in year {int(last['year_since_law'])}"
    return "cannot_yet_test", (f"median {last['median_rate']:.2f} in year {int(last['year_since_law'])} "
                               "is between 0.8 and 1.0 (neither rule met)")


# ---------------------------------------------------------------------------
# 4. Share of ADUs permitted with a new house
# ---------------------------------------------------------------------------

def apn_key(apn) -> str:
    s = re.sub(r"[^0-9A-Za-z]", "", str(apn or "")).upper()
    return "" if s in ("", "NAN", "NONE", "NA", "0") else s


TRACT_PATTERN = r"^\s*(TR|TRACT|TTM|VTTM)\s*[-#.]?\s*\d"


def apr_new_house_share(rows: pd.DataFrame, year_window: int = 0) -> pd.DataFrame:
    """For APR A2 rows (juris_name, year, apn, unit_cat, bp_units): ADU building-permit units whose
    parcel (APN) also has a single-family detached building permit in the same report year
    (year_window = 0) or within +/- year_window years. Rows with a blank APN count in the
    denominator and are reported separately."""
    r = rows[rows["bp_units"].fillna(0) > 0].copy()
    r["apn_key"] = r["apn"].map(apn_key)
    sfd = r[(r["unit_cat"] == "SFD") & (r["apn_key"] != "")][["juris_name", "apn_key", "year"]]
    adu = r[r["unit_cat"] == "ADU"].copy()
    keys = set()
    for j, a, y in sfd.itertuples(index=False):
        for d in range(-year_window, year_window + 1):
            keys.add((j, a, int(y) + d))
    adu["with_new_house"] = [(j, a, int(y)) in keys and a != ""
                             for j, a, y in zip(adu["juris_name"], adu["apn_key"], adu["year"])]
    names = adu["project_name"] if "project_name" in adu else pd.Series("", index=adu.index)
    adu["tract"] = adu["with_new_house"] & names.fillna("").str.upper().str.match(TRACT_PATTERN)
    g = adu.groupby("juris_name").agg(
        adu_units=("bp_units", "sum"),
        adu_units_blank_apn=("bp_units", lambda s: s[adu.loc[s.index, "apn_key"] == ""].sum()),
        adu_units_with_new_house=("bp_units", lambda s: s[adu.loc[s.index, "with_new_house"]].sum()),
        adu_units_with_new_house_tract=("bp_units", lambda s: s[adu.loc[s.index, "tract"]].sum()))
    g["share_with_new_house"] = g["adu_units_with_new_house"] / g["adu_units"]
    # Subdivision-driven (treated like the owner's condo-driven flag, 2026-10-25): at least half of
    # the city's with-new-house ADUs sit on rows named as a tract map, i.e. builder-installed ADUs in
    # new subdivisions, and they are at least 20% of all its ADUs.
    g["subdivision_driven"] = ((g["adu_units_with_new_house_tract"] >= 0.5 * g["adu_units_with_new_house"])
                               & (g["adu_units_with_new_house"] >= 0.2 * g["adu_units"]))
    return g.reset_index()


# Recent rules window per city (OTHER_CITIES.md), and owner flag (2026-10-25): Seattle's and
# Austin's high shares come from permissive condominium / unit-lot rules that let owners
# subdivide and sell, which is not part of the benchmark scenario.
OTHER_CITY_WINDOWS = {"seattle": (2021, 2024), "portland": (2022, 2025), "austin": (2016, 2023),
                      "denver": (2023, 2025), "minneapolis": (2021, 2025)}
CONDO_DRIVEN = {"seattle": "unit-lot subdivision / condo sale of ADUs on redevelopment sites (OPCD: 57% "
                           "of 2022 ADUs on condo parcels)",
                "austin": "condo regime lets owners split and sell secondary apartments built with a new house"}


def other_cities_new_house(annual: pd.DataFrame, windows: dict = OTHER_CITY_WINDOWS) -> pd.DataFrame:
    """Share of ADU units permitted together with a new house = excluded_with_new_house /
    (adu_units + excluded_with_new_house), summed over each city's recent rules window."""
    rows = []
    for city, (y0, y1) in windows.items():
        a = annual[(annual["city"] == city) & annual["year"].between(y0, y1)]
        main, nh = float(a["adu_units"].sum()), float(a["excluded_with_new_house"].sum())
        rows.append(dict(city=city, first_year=y0, last_year=y1, adu_units_existing_lot=main,
                         adu_units_with_new_house=nh, adu_units_total=main + nh,
                         share_with_new_house=nh / (main + nh) if main + nh else float("nan"),
                         condo_driven=city in CONDO_DRIVEN, condo_note=CONDO_DRIVEN.get(city, "")))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 5. Owner decision AQ-039: new-house ADUs split into teardown-rebuild vs vacant lot
# ---------------------------------------------------------------------------
# A new house (and any ADU permitted with it) is a teardown-rebuild when a demolition / wrecking
# permit for a dwelling on the same parcel (or same normalised street address) was issued from
# DEMO_BEFORE_DAYS before to DEMO_AFTER_DAYS after the new-house permit, or the new-house record
# itself reports demolished units. Otherwise it is on a vacant lot - unless the demolition data do
# not cover the whole look-back window, or the record has neither a parcel id nor an address, in
# which case it is unclassified.
DEMO_BEFORE_DAYS, DEMO_AFTER_DAYS = 730, 365


def norm_addr(a: pd.Series) -> pd.Series:
    s = (a.fillna("").astype(str).str.upper().str.replace(r"\s+-\s+UNIT.*$", "", regex=True)
         .str.replace(r"[^A-Z0-9 ]", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip())
    s = s.str.replace(r"\b(STREET)\b", "ST", regex=True).str.replace(r"\b(AVENUE)\b", "AVE", regex=True)
    return s


def norm_parcel(p: pd.Series) -> pd.Series:
    s = p.fillna("").astype(str).str.upper().str.replace(r"[^0-9A-Z]", "", regex=True)
    return s.where(~s.isin(["", "NAN", "NONE", "0"]), "")


def classify_lot(new: pd.DataFrame, demos: pd.DataFrame, demo_start: pd.Timestamp) -> pd.Series:
    """new: columns id, date, parcel, addr, [dem_units]; demos: date, parcel, addr.
    Returns 'teardown' / 'vacant' / 'unclassified' per row of `new` (index preserved)."""
    out = pd.Series("vacant", index=new.index, dtype=object)
    n = new.assign(parcel=norm_parcel(new["parcel"]), addr=norm_addr(new["addr"]),
                   date=pd.to_datetime(new["date"], errors="coerce"))
    d = demos.assign(parcel=norm_parcel(demos["parcel"]), addr=norm_addr(demos["addr"]),
                     date=pd.to_datetime(demos["date"], errors="coerce"))
    d = d[d["date"].notna()]
    hit = pd.Series(False, index=new.index)
    for key in ("parcel", "addr"):
        a = n[n[key] != ""][[key, "date"]].reset_index()
        m = a.merge(d[d[key] != ""][[key, "date"]], on=key, suffixes=("", "_d"))
        gap = (m["date_d"] - m["date"]).dt.days
        ok = m[(gap >= -DEMO_BEFORE_DAYS) & (gap <= DEMO_AFTER_DAYS)]
        hit.loc[ok["index"].unique()] = True
    if "dem_units" in n:
        hit |= pd.to_numeric(n["dem_units"], errors="coerce").fillna(0) > 0
    out[hit] = "teardown"
    no_key = (n["parcel"] == "") & (n["addr"] == "")
    early = n["date"] - pd.Timedelta(days=DEMO_BEFORE_DAYS) < demo_start
    out[~hit & (no_key | early | n["date"].isna())] = "unclassified"
    return out


def reform_compare(series: pd.DataFrame, before: tuple[int, int], after: tuple[int, int]) -> dict:
    """series: year, vacant_new_house_adus, vacant_new_houses, existing_lot_adus, homes.
    (a) vacant-lot new-house ADUs per 100 new houses on vacant lots; (b) ADUs on lots that
    already had a home (existing-lot + teardown new-house ADUs) per 1,000 single-family homes/yr."""
    out = {}
    for tag, (y0, y1) in (("before", before), ("after", after)):
        w = series[series["year"].between(y0, y1)]
        out[f"{tag}_years"] = f"{y0}-{y1}"
        out[f"{tag}_n_years"] = len(w)
        out[f"{tag}_vacant_adus"] = w["vacant_new_house_adus"].sum()
        out[f"{tag}_vacant_houses"] = w["vacant_new_houses"].sum()
        out[f"{tag}_a_per_100"] = (100 * w["vacant_new_house_adus"].sum() / w["vacant_new_houses"].sum()
                                   if w["vacant_new_houses"].sum() else float("nan"))
        out[f"{tag}_had_home_adus"] = w["had_home_adus"].sum()
        out[f"{tag}_b_per_1000"] = (w["had_home_adus"].sum() / len(w) / w["homes"].iloc[0] * 1000
                                    if len(w) else float("nan"))
    out["ratio_a"] = out["after_a_per_100"] / out["before_a_per_100"] if out["before_a_per_100"] else float("nan")
    out["ratio_b"] = out["after_b_per_1000"] / out["before_b_per_1000"] if out["before_b_per_1000"] else float("nan")
    return out


def _ms(s: pd.Series) -> pd.Series:
    return pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="ms", utc=True).dt.tz_localize(None)


def lot_split_portland(adus: pd.DataFrame, raw: pd.DataFrame, demo_raw: pd.DataFrame):
    """adus: oc.classify_portland output. raw: layer 89 rows. demo_raw: layer 126 rows.
    Returns (new-house ADU rows with lot status, new-house rows with lot status)."""
    site = raw[["FOLDERNUMB", "PROPGISID1", "PROP_ADDRE"]].rename(columns={"FOLDERNUMB": "permit_id"})
    nh = adus[adus["with_new_house"] & ~adus["legalization"]].merge(site, on="permit_id", how="left")
    nh = nh.drop_duplicates("permit_id")
    h = raw[raw["NEWCLASS"].eq("New Construction") & raw["NEWTYPE"].isin(["Single Family Dwelling", "Townhouse", "Rowhouse"])
            & raw["PDXBND"].astype(str).str.upper().eq("YES") & raw["ISSUEDATE"].notna()
            & ~raw["STATUS"].fillna("").str.contains(r"Application|VOID|Cancel", case=False)].copy()
    h["date"] = pd.to_datetime(h["ISSUEDATE"].str[:10].str.replace("/", "-"), errors="coerce")
    d = demo_raw[demo_raw["TYPE"].eq("Single Family Dwelling")
                 & demo_raw["STATUS"].isin(["Final", "Issued", "Under Inspection"])].copy()
    d = pd.DataFrame(dict(date=pd.to_datetime(d["ISSUED"].str[:10].str.replace("/", "-"), errors="coerce"),
                          parcel=d["STATEIDKEY"],
                          addr=d[["HOUSE", "DIRECTION", "PROPSTREET", "STREETTYPE"]].fillna("").agg(" ".join, axis=1)))
    start = pd.Timestamp("2000-01-01")
    nh["lot"] = classify_lot(pd.DataFrame(dict(date=nh["issue_date"], parcel=nh["PROPGISID1"], addr=nh["PROP_ADDRE"]),
                                          index=nh.index), d, start)
    h["lot"] = classify_lot(pd.DataFrame(dict(date=h["date"], parcel=h["PROPGISID1"], addr=h["PROP_ADDRE"]), index=h.index),
                            d, start)
    h["year"] = h["date"].dt.year
    return nh, h[["year", "lot"]]


def lot_split_denver(adus: pd.DataFrame, raw: pd.DataFrame, demo_raw: pd.DataFrame):
    site = raw[["PERMIT_NUM", "SCHEDNUM", "ADDRESS"]].rename(columns={"PERMIT_NUM": "permit_id"})
    nh = adus[adus["with_new_house"] & ~adus["legalization"]].merge(site, on="permit_id", how="left").drop_duplicates("permit_id")
    codes = raw[["STAT_CODE_1", "STAT_CODE_2", "STAT_CODE_3"]].fillna("").astype(str)
    h = raw[raw["CLASS"].fillna("").str.upper().str.contains("NEW BUILDING") & codes.eq("001").any(axis=1)
            & raw["CANCEL"].isna() & raw["DATE_ISSUED"].notna()].copy()
    h["date"] = _ms(h["DATE_ISSUED"])
    d = demo_raw[demo_raw["CLASS"].fillna("").str.upper().str.contains("WRECK") & demo_raw["CANCEL"].isna()]
    d = pd.DataFrame(dict(date=_ms(d["DATE_ISSUED"]), parcel=d["SCHEDNUM"], addr=""))
    start = d["date"].min()
    nh["lot"] = classify_lot(pd.DataFrame(dict(date=nh["issue_date"], parcel=nh["SCHEDNUM"], addr=""), index=nh.index), d, start)
    h["lot"] = classify_lot(pd.DataFrame(dict(date=h["date"], parcel=h["SCHEDNUM"], addr=""), index=h.index), d, start)
    h["year"] = h["date"].dt.year
    return nh, h[["year", "lot"]]


def lot_split_minneapolis(adus: pd.DataFrame, raw: pd.DataFrame, new_raw: pd.DataFrame, wreck_raw: pd.DataFrame):
    site = raw[["permitNumber", "APN", "dwellingUnitsEliminated"]].rename(columns={"permitNumber": "permit_id"})
    nh = adus[adus["with_new_house"] & ~adus["legalization"]].merge(site, on="permit_id", how="left").drop_duplicates("permit_id")
    h = new_raw[new_raw["occupancyType"].isin(["SFD", "TFD", "TH"]) & ~new_raw["status"].eq("Cancelled")
                & new_raw["issueDate"].notna()].copy()
    h["date"] = _ms(h["issueDate"])
    w = wreck_raw[wreck_raw["occupancyType"].isin(["SFD", "TFD", "MFD", "3to4"]) & ~wreck_raw["status"].eq("Cancelled")]
    d = pd.DataFrame(dict(date=_ms(w["issueDate"]), parcel=w["APN"], addr=""))
    start = d["date"].min()
    nh["lot"] = classify_lot(pd.DataFrame(dict(date=nh["issue_date"], parcel=nh["APN"], addr="",
                                               dem_units=nh["dwellingUnitsEliminated"]), index=nh.index), d, start)
    h["lot"] = classify_lot(pd.DataFrame(dict(date=h["date"], parcel=h["APN"], addr="",
                                              dem_units=h["dwellingUnitsEliminated"]), index=h.index), d, start)
    h["year"] = h["date"].dt.year
    return nh, h[["year", "lot"]]


def lot_split_apr(rows: pd.DataFrame):
    """APR A2 rows (juris_name, year, apn, unit_cat, bp_units, dem_units). New house = SFD row with
    building-permit units; teardown = any row on the same APN within +/- 1 report year reports
    demolished/destroyed units. New-house ADU = ADU row on an APN with an SFD row in the same
    report year (as apr_new_house_share). Report years start 2018, so the look-back for 2018 rows
    is short (one year)."""
    r = rows[rows["bp_units"].fillna(0) > 0].copy()
    r["apn_key"] = r["apn"].map(apn_key)
    dem = rows.assign(apn_key=rows["apn"].map(apn_key))
    dem = dem[(pd.to_numeric(dem["dem_units"], errors="coerce").fillna(0) > 0) & (dem["apn_key"] != "")]
    dk = {(j, a, int(y) + k) for j, a, y in zip(dem["juris_name"], dem["apn_key"], dem["year"]) for k in (-1, 0, 1)}
    sfd = r[r["unit_cat"] == "SFD"].copy()
    sk = {(j, a, int(y)) for j, a, y in zip(sfd["juris_name"], sfd["apn_key"], sfd["year"]) if a}
    def lot(j, a, y):
        if not a:
            return "unclassified"
        return "teardown" if (j, a, int(y)) in dk else "vacant"
    sfd["lot"] = [lot(j, a, y) for j, a, y in zip(sfd["juris_name"], sfd["apn_key"], sfd["year"])]
    adu = r[r["unit_cat"] == "ADU"].copy()
    adu["with_new_house"] = [(j, a, int(y)) in sk for j, a, y in zip(adu["juris_name"], adu["apn_key"], adu["year"])]
    adu["lot"] = [lot(j, a, y) if w else "existing" for j, a, y, w in
                  zip(adu["juris_name"], adu["apn_key"], adu["year"], adu["with_new_house"])]
    return adu, sfd


def lot_series(nh_adus: pd.DataFrame, houses: pd.DataFrame, existing: pd.DataFrame, homes: float,
               adu_units_col: str = "adu_units", house_units_col: str | None = None) -> pd.DataFrame:
    """Per year: new-house ADUs by lot status, new houses by lot status, existing-lot ADUs, and
    'had_home_adus' = existing-lot ADUs + teardown new-house ADUs."""
    a = nh_adus.assign(u=nh_adus[adu_units_col]).pivot_table(index="year", columns="lot", values="u", aggfunc="sum", fill_value=0)
    hu = houses.assign(u=houses[house_units_col] if house_units_col else 1)
    h = hu.pivot_table(index="year", columns="lot", values="u", aggfunc="sum", fill_value=0)
    e = existing.groupby("year")["units"].sum()
    years = sorted(set(a.index) | set(h.index) | set(e.index))
    out = pd.DataFrame(index=pd.Index(years, name="year"))
    for k in ("teardown", "vacant", "unclassified"):
        out[f"new_house_adus_{k}"] = a.get(k, pd.Series(dtype=float)).reindex(years).fillna(0)
        out[f"new_houses_{k}"] = h.get(k, pd.Series(dtype=float)).reindex(years).fillna(0)
    out["existing_lot_adus"] = e.reindex(years).fillna(0)
    out["vacant_new_house_adus"] = out["new_house_adus_vacant"]
    out["vacant_new_houses"] = out["new_houses_vacant"]
    out["had_home_adus"] = out["existing_lot_adus"] + out["new_house_adus_teardown"]
    out["homes"] = homes
    return out.reset_index()
