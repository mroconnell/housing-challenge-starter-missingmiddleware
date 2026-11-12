"""Parking lot-fit test (docs/parking/LOT_FIT_PLAN.md; its Choices and Audit fixes blocks override the draft).

On each residential lot, for a new 2-, 3- and 4-unit building: does the building fit with setbacks and coverage and
no parking (step 1), and does it still fit once the place's required stalls and their access are added (step 2)?
    share = lots where parking blocks / lots where the building fits without parking.

    uv run --all-extras python scripts/run_parking_lotfit.py --synthetic    # smoke run on made-up lots (no data)
    uv run --all-extras python scripts/run_parking_lotfit.py --go           # real run (only after the audit)

Inputs: data/raw/parking_lotfit/ (scripts/fetch_parking_lotfit.py), data/raw/milwaukee_mprop/mprop.csv,
data/raw/madison_parcels/tax_parcels.geojson, data/raw/madison_tod/tod_boundary.geojson and the hand-coded rules
reference/parking_lotfit_rules.csv. Geometry: missing_middleware/geom.py and geom_extra_tod.py (numpy/scipy; no
shapely, audit fix 1). Choices the plan leaves open are listed in docs/parking/LOT_FIT_CODE_NOTES.md.

Outputs (aggregates only, real run): reference/parking_lotfit_shares.csv, reference/parking_lotfit_spans.csv,
reference/parking_lotfit_sanity_milwaukee.csv.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import math
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from missing_middleware import geom as G  # noqa: E402
from missing_middleware import geom_extra_tod as GX  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

RULES_CSV = REFERENCE / "parking_lotfit_rules.csv"
D = RAW / "parking_lotfit"
CRS_M = 3071                      # Wisconsin Transverse Mercator, metres
FT_PER_M = 1 / 0.3048
SQFT_PER_SQM = FT_PER_M ** 2
UNITS = (2, 3, 4)

# place label (rules CSV) -> fetch key (data/raw/parking_lotfit/v12_<key>.geojson) and county FIPS for roads
PLACES = {
    "Milwaukee": ("milwaukee", ["55079", "55131", "55133"]),
    "Madison": ("madison", ["55025"]),
    "Appleton": ("appleton", ["55087", "55015", "55139"]),
    "Waukesha": ("waukesha", ["55133"]),
    "Eau Claire": ("eau_claire", ["55035", "55017"]),
    "Oshkosh": ("oshkosh", ["55139"]),
    "Germantown": ("germantown", ["55131"]),
    "Green Bay": ("green_bay", ["55009"]),
    "Kenosha": ("kenosha", ["55059"]),
    "Racine": ("racine", ["55101"]),
    "Janesville": ("janesville", ["55105"]),
}
ZONED = ("Milwaukee", "Madison")              # choice C6: zoning by lot only here, so only here the main version runs
# span variants applied in every place even where a place's code states the central value (plan 3.3 / audit fix 2)
FORCE_ALL = {("setback_parking_rear", "not_allowed"), ("tandem_counts", "no")}
SANITY_LABEL = "rule model may be too strict"
# Alleys (audit option b): TIGER barely maps Wisconsin alleys, so every lot is run twice under preset bounds
ALLEY_BOUNDS = {"upper bound: no lot has an alley": False, "lower bound: every lot has an alley": True}
BOUND_LABEL = ("alley bounds: preset assumptions (all lots without / all lots with an alley), not a range; TIGER "
               "alleys are not used")
SPAN_LABEL = "span of assumptions (low/high across rule variants; not a statistical range)"
WAIVER_LABEL = ("waivers, reductions and adjustments are ignored, so blocking may be overstated; Milwaukee 2-unit "
                "blocking is 0 by rule (no minimum)")


# ================================================================================================== rules
def load_rules(path: Path = RULES_CSV) -> pd.DataFrame:
    r = pd.read_csv(path, dtype=str).fillna("")
    r["rid"] = np.arange(len(r))
    return r


def _units_ok(cell: str, n: int) -> bool:
    return cell == "" or str(n) in cell.split(";")


def variant_group(r) -> str:
    """A span variant's name: the CSV's variant_group when set (rows applied together, e.g. a stall's width and
    depth), else provision=value with the place."""
    g = getattr(r, "variant_group", "") or ""
    return g if g else f"{r.provision}={r.value} [{r.place}]"


def _score(row) -> int:
    """Specificity: a condition row (alley, corner, TOD overlay, small lot) is a deliberate override and beats
    everything; then place, district, unit count."""
    return 16 * (row.condition != "") + 8 * (row.place != "*") + 4 * (row.district != "*") + 2 * (row.units != "")


class Rules:
    """Look-ups in reference/parking_lotfit_rules.csv. The most specific matching row wins (see _score). Rows with
    use 'central' are the main run; one 'span_variant' row can replace its central counterpart for a variant run:
    it applies where it is at least as specific as the central row (so a plan default variant only reaches places
    whose code is silent), except the FORCE_ALL variants, which apply everywhere."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._by_prov: dict = {}
        for r in df[df.use == "central"].itertuples(index=False):
            self._by_prov.setdefault(r.provision, []).append(r)
        self._row = {int(r.rid): r for r in df.itertuples(index=False)}
        self._groups: dict = {}
        for r in df[df.use == "span_variant"].itertuples(index=False):
            self._groups.setdefault(variant_group(r), []).append(r)
        self._memo: dict = {}

    def get(self, place, district, prov, n, conds=frozenset(), variant: str | None = None):
        """Value of a provision (string), or None when no row applies."""
        key = (place, district, prov, n, frozenset(conds), variant)
        if key not in self._memo:
            self._memo[key] = self._get(place, district, prov, n, conds, variant)
        return self._memo[key]

    @staticmethod
    def _match(r, place, district, n, conds) -> bool:
        return (r.place in (place, "*") and r.district in (district, "*") and _units_ok(r.units, n)
                and (r.condition == "" or r.condition in conds))

    def _get(self, place, district, prov, n, conds, variant):
        c = [r for r in self._by_prov.get(prov, []) if self._match(r, place, district, n, conds)]
        best = None
        if c:
            top = max(_score(r) for r in c)
            vals = {r.value for r in c if _score(r) == top}
            if len(vals) > 1:
                raise ValueError(f"conflicting rows for {place}/{district}/{prov}/n={n}/{sorted(conds)}: {vals}")
            best = (top, vals.pop())
        if variant is not None:
            hits = [v for v in self._groups[variant] if v.provision == prov and self._match(v, place, district, n, conds)]
            if hits:
                v = max(hits, key=_score)
                forced = (v.provision, v.value) in FORCE_ALL
                if best is None or forced or _score(v) >= best[0]:
                    return v.value
        return None if best is None else best[1]

    def group(self, variant: str) -> list:
        return self._groups[variant]

    def row(self, rid: int):
        return self._row[int(rid)]

    def variants(self, place: str) -> list[str]:
        """Span-variant groups that can apply in a place (rows of one group are applied together)."""
        return [k for k, rows in self._groups.items() if any(r.place in (place, "*") for r in rows)]

    def as_if_district(self, place: str, n: int) -> str:
        d = self.get(place, "*", "as_if_district", n)
        if not d:
            raise ValueError(f"no as-if district for {place}")
        return d

    def districts(self, place: str) -> set[str]:
        return set(self.df[(self.df.place == place) & (self.df.district != "*")].district)


def _f(x, default=None):
    if x is None or x == "":
        return default
    return float(x)


@dataclass(frozen=True)
class Params:
    """Everything the fit test needs for one place, district, unit count and variant (feet and square feet)."""
    units: int
    min_area: float = 0.0
    min_width: float = 0.0
    front: float = 0.0
    side: float = 0.0
    side_other: float = 0.0
    side_total: float = 0.0
    rear: float = 0.0
    rear_pct: float | None = None
    cov_cap: float | None = None          # cap on building (basis 'building') or building + paving ('impervious')
    cov_basis: str = "none"
    bldg_cov_cap: float | None = None     # separate cap on buildings only (Janesville open-space rule)
    floors: int = 2
    unit_area: float = 1000.0
    story_h: float = 11.0
    max_height: float | None = None
    max_stories: float | None = None
    min_dim: float = 20.0
    stalls: int = 0
    enclosed: int = 0
    tandem: bool = True
    drive_counts: bool = False
    drive_max: float = math.inf
    stall_w: float = 9.0
    stall_d: float = 18.0
    aisle: float = 24.0
    drive_w: float = 10.0
    encl_w: float = 12.0
    encl_d: float = 22.0
    park_rear_setback: bool = True
    park_side_setback: bool = True


def counted(value: str | None, silent_counts: bool) -> bool:
    """yes -> counted; no -> not; silent / missing -> the main run's default (choice C4: counted)."""
    if value in ("yes",):
        return True
    if value in ("no",):
        return False
    return silent_counts


def resolve(R: Rules, place: str, district: str, n: int, conds=frozenset(), variant: str | None = None) -> Params:
    g = lambda prov: R.get(place, district, prov, n, conds, variant)  # noqa: E731
    side = _f(g("side_setback_ft"), 0.0)
    other = _f(g("side_setback_other_ft"), side)
    per_unit = _f(g("min_lot_area_per_unit_sqft"), 0.0)
    rear_pct = _f(g("rear_setback_pct_depth"))
    stalls = _f(g(f"stalls_total_{n}"), 0.0)
    encl = _f(g(f"enclosed_stalls_{n}"), 0.0)
    code_drive_min = _f(g("driveway_min_width_ft"), 0.0)
    tandem = counted(g("tandem_counts"), True)
    drive_counts = counted(g("driveway_counts"), True) if tandem else False   # the 'no tandem' variant drops both
    if variant is not None:
        if any((v.provision, v.value) == ("tandem_counts", "no") for v in R.group(variant)):
            tandem, drive_counts = False, False
    rear_park = g("setback_parking_rear")
    side_park = g("setback_parking_side")
    return Params(
        units=n,
        min_area=max(_f(g("min_lot_area_sqft"), 0.0), n * per_unit),
        min_width=_f(g("min_lot_width_ft"), 0.0),
        front=_f(g("front_setback_ft"), 0.0),
        side=side, side_other=other, side_total=_f(g("side_setback_total_ft"), 0.0),
        rear=_f(g("rear_setback_ft"), 0.0), rear_pct=rear_pct,
        cov_cap=_f(g("max_lot_coverage")), cov_basis=g("coverage_basis") or "none",
        bldg_cov_cap=_f(g("max_building_coverage")),
        floors=int(_f(g("floors"), 2)), unit_area=_f(g("unit_floor_area_sqft"), 1000.0),
        story_h=_f(g("story_height_ft"), 11.0), max_height=_f(g("max_height_ft")), max_stories=_f(g("max_stories")),
        min_dim=_f(g("min_building_dim_ft"), 20.0),
        stalls=int(math.ceil(stalls - 1e-9)), enclosed=int(math.ceil(encl - 1e-9)),
        tandem=tandem, drive_counts=drive_counts, drive_max=_f(g("driveway_counts_max"), math.inf),
        stall_w=_f(g("stall_width_ft"), 9.0), stall_d=_f(g("stall_depth_ft"), 18.0), aisle=_f(g("aisle_width_ft"), 24.0),
        drive_w=max(_f(g("driveway_width_ft"), 10.0), code_drive_min),
        encl_w=_f(g("enclosed_stall_width_ft"), 12.0), encl_d=_f(g("enclosed_stall_depth_ft"), 22.0),
        park_rear_setback=(rear_park != "not_allowed"), park_side_setback=(side_park != "not_allowed"))


def units_allowed(R: Rules, place: str, district: str, n: int, conds=frozenset()) -> bool:
    v = R.get(place, district, "units_allowed", n, conds)
    return bool(v) and str(n) in v.split(";")


# ================================================================================================ fit test
@dataclass(frozen=True)
class Lot:
    area: float          # sq ft
    width: float         # ft (shorter side of the minimum rotated rectangle)
    depth: float         # ft (area / width)
    alley: bool = False
    corner: bool = False


FITS, PARKING, OTHER = "fits", "parking_blocks", "other_blocks"


def floors_used(p: Params) -> int:
    """Planned floors, never above the district's story or height cap (plan 3.2); a half story is not a floor."""
    f = p.floors
    if p.max_stories is not None:
        f = min(f, int(math.floor(p.max_stories + 1e-9)))
    if p.max_height is not None:
        f = min(f, int(math.floor(p.max_height / p.story_h + 1e-9)))
    return max(f, 1)


def _building(bw_avail: float, footprint: float, bd_avail: float, min_dim: float):
    """Building width and depth: as wide as allowed but no shallower than min_dim; None when it can't fit."""
    if bw_avail < min_dim - 1e-9:
        return None
    w = min(bw_avail, footprint / min_dim)
    if w < min_dim - 1e-9:
        w = min_dim
    d = footprint / w
    if d > bd_avail + 1e-9:
        return None
    return w, d


def _fill_row(length: float, depth: float, need_g: int, p: Params, tandem: bool):
    """Garages first (12 x 22 ft each), then open stalls; open stalls doubled when tandem counts and the row is two
    stalls deep. Returns (garages, open stalls)."""
    g = 0
    if need_g > 0 and depth >= p.encl_d - 1e-9:
        g = min(need_g, int(math.floor(length / p.encl_w + 1e-9)))
    rest = length - g * p.encl_w
    o = int(math.floor(rest / p.stall_w + 1e-9)) if depth >= p.stall_d - 1e-9 and rest > 0 else 0
    if tandem and depth >= 2 * p.stall_d - 1e-9:
        o *= 2
    return g, o


def _layouts(lot: Lot, p: Params, bd: float, rear_sb: float, side_sum: float):
    """Candidate parking layouts behind the building: (garages, open stalls, paved sq ft excluding stalls)."""
    W = lot.width
    Wz = W if p.park_side_setback else W - side_sum
    Rz = lot.depth - p.front - bd - (0.0 if p.park_rear_setback else rear_sb)
    if Rz <= 0 or Wz <= 0:
        return []
    E = p.enclosed
    out = []
    if lot.alley:                                         # alley is the aisle; stalls back into it
        g, o = _fill_row(Wz, Rz, E, p, p.tandem)
        out.append((g, o, 0.0))
        return out
    drive = (p.front + bd) * p.drive_w
    # N0: up to 2 stalls (or a 2-car garage) side by side at the end of the drive, backing down it; no aisle
    g = min(E, 2, int(math.floor(Wz / p.encl_w + 1e-9))) if Rz >= p.encl_d - 1e-9 else 0
    o_pos = 0
    if Rz >= p.stall_d - 1e-9:
        o_pos = max(0, min(2 - g, int(math.floor((Wz - g * p.encl_w) / p.stall_w + 1e-9))))
    o = o_pos * (2 if (p.tandem and Rz >= 2 * p.stall_d - 1e-9) else 1)
    k = 0
    if p.drive_counts:                                    # in-line stalls on the drive beside the building
        k = int(min(p.drive_max, math.floor(bd / p.stall_d + 1e-9)))
    out.append((g, o + k, drive))
    # N1: cross aisle behind the building, row behind it (and a row in front of it when deep enough)
    A = p.aisle
    if Rz >= A + p.stall_d - 1e-9:
        g1, o1 = _fill_row(Wz, Rz - A, E, p, p.tandem)
        out.append((g1, o1, drive + A * Wz))
        if Rz >= A + 2 * p.stall_d - 1e-9:
            g2, o2 = _fill_row(Wz, Rz - A - p.stall_d, E, p, p.tandem)
            _, o3 = _fill_row(Wz - p.drive_w, p.stall_d, 0, p, False)
            out.append((g2, o2 + o3, drive + A * Wz))
    # N2: the drive widens to an aisle along the side; stalls perpendicular to it (one or both sides)
    if Wz >= A + p.stall_d - 1e-9:
        g1, o1 = _fill_row(Rz, Wz - A, E, p, p.tandem)
        out.append((g1, o1, drive + A * Rz))
        if Wz >= A + 2 * p.stall_d - 1e-9:
            ga, oa = _fill_row(Rz, p.stall_d, E, p, False)
            gb, ob = _fill_row(Rz, p.stall_d, max(0, E - ga), p, False)
            out.append((ga + gb, oa + ob, drive + A * Rz))
    return out


def fit_lot(lot: Lot, p: Params) -> tuple[str, str]:
    """(class, reason). Class: fits / parking_blocks / other_blocks (plan 3.5)."""
    A, W, Dp = lot.area, lot.width, lot.depth
    # ---- step 1: building, setbacks, coverage, lot minimums; no parking
    if A < p.min_area - 1e-6:
        return OTHER, "lot_area"
    if W < p.min_width - 1e-6:
        return OTHER, "lot_width"
    side_sum = max(p.side + p.side_other, p.side_total)
    BW = W - side_sum
    rear_sb = p.rear if p.rear_pct is None else min(p.rear, p.rear_pct * Dp)
    BD = Dp - p.front - rear_sb
    f = floors_used(p)
    F = p.units * p.unit_area / f
    b = _building(BW, F, BD, p.min_dim)
    if b is None:
        return OTHER, "building_box"
    if p.cov_cap is not None and p.cov_basis in ("building", "impervious") and F > p.cov_cap * A + 1e-6:
        return OTHER, "coverage"
    if p.bldg_cov_cap is not None and F > p.bldg_cov_cap * A + 1e-6:
        return OTHER, "coverage"
    # ---- step 2: required stalls and their access
    S, E = p.stalls, p.enclosed
    if S <= 0 and E <= 0:
        return FITS, "no_minimum"
    S = max(S, E)
    # with an alley: rear stalls off the alley first; the owner may still use a driveway layout instead, so an alley
    # never makes a lot worse than having no alley (keeps the alley lower bound a true lower bound)
    tries = [(lot, b[1])] if lot.alley else []
    no_alley = replace(lot, alley=False)
    side_drive = side_sum - min(p.side, p.side_other)              # the drive runs in the wider side setback
    encroach = max(0.0, p.drive_w - side_drive)
    b2 = _building(BW - encroach, F, BD, p.min_dim)
    if b2 is not None:
        tries.append((no_alley, b2[1]))
    if not tries:
        return PARKING, "driveway_squeezes_building"
    reason = "stalls"
    for lt, bd in tries:
        for g, o, paved in _layouts(lt, p, bd, rear_sb, side_sum):
            if g < E or g + o < S:
                continue
            open_used = S - E
            garages = E * p.encl_w * p.encl_d
            build = F + garages
            imperv = build + paved + open_used * p.stall_w * p.stall_d
            if p.cov_cap is not None and p.cov_basis == "building" and build > p.cov_cap * A + 1e-6:
                reason = "coverage_with_parking"
                continue
            if p.cov_cap is not None and p.cov_basis == "impervious" and imperv > p.cov_cap * A + 1e-6:
                reason = "coverage_with_parking"
                continue
            if p.bldg_cov_cap is not None and build > p.bldg_cov_cap * A + 1e-6:
                reason = "coverage_with_parking"
                continue
            return FITS, "parking_fits"
    return PARKING, reason


# ============================================================================================ lot geometry
def lot_shapes(polys: list) -> pd.DataFrame:
    """Per lot (EPSG:3071 metres in): area, width, depth (ft / sq ft), rectangle fill, centre and depth axis."""
    width_m = GX.min_rect_widths(polys)
    area_m2 = G.areas(polys)
    rows = []
    for k, f in enumerate(polys):
        rings = [r for part in (f or []) for r in part[:1] if len(r)]
        c = GX.min_rotated_rectangle(np.concatenate(rings)) if rings else None
        if c is None:
            rows.append((np.nan, np.nan, np.nan, np.nan, np.nan))
            continue
        e1, e2 = c[1] - c[0], c[2] - c[1]
        l1, l2 = float(np.hypot(*e1)), float(np.hypot(*e2))
        u = (e1 / l1) if l1 >= l2 else (e2 / l2)
        cx, cy = c.mean(axis=0)
        rows.append((l1 * l2, cx, cy, u[0], u[1]))
    r = pd.DataFrame(rows, columns=["rect_m2", "cx", "cy", "ux", "uy"])
    r["area_sqft"] = area_m2 * SQFT_PER_SQM
    r["width_ft"] = width_m * FT_PER_M
    r["depth_ft"] = r.area_sqft / r.width_ft
    r["fill"] = area_m2 / r.rect_m2
    return r


def _densify(lines: list, step: float) -> np.ndarray:
    pts = []
    for ln in lines:
        for a, b in zip(ln[:-1], ln[1:]):
            n = max(1, int(math.ceil(float(np.hypot(*(b - a))) / step)))
            t = np.linspace(0, 1, n + 1)[:, None]
            pts.append(a + t * (b - a))
    return np.concatenate(pts) if pts else np.zeros((0, 2))


def alley_flags(polys: list, shapes: pd.DataFrame, alleys: list, streets: list, buffer_m: float = 5.0,
                step: float = 1.0) -> np.ndarray:
    """True where an alley (TIGER S1730) lies within buffer_m of the lot's rear half: the half of the depth axis away
    from the nearest other road. With no other road within 100 m, any alley within buffer_m counts."""
    out = np.zeros(len(polys), bool)
    ap = _densify([seg for f in alleys for seg in f], step)
    if not len(ap):
        return out
    at = cKDTree(ap)
    sp = _densify([seg for f in streets for seg in f], step * 2)
    st = cKDTree(sp) if len(sp) else None
    for k, f in enumerate(polys):
        rings = [r for part in (f or []) for r in part[:1] if len(r)]
        if not rings or not np.isfinite(shapes.cx[k]):
            continue
        c0 = np.array([shapes.cx[k], shapes.cy[k]])
        reach = max(float(np.hypot(*(r - c0).T).max()) for r in rings)
        if at.query(c0)[0] > reach + buffer_m:
            continue
        bnd = _densify(rings, step)
        hits = at.query_ball_point(bnd, buffer_m)
        idx = sorted({i for h in hits for i in h})
        if not idx:
            continue
        c = np.array([shapes.cx[k], shapes.cy[k]])
        u = np.array([shapes.ux[k], shapes.uy[k]])
        if st is None:
            out[k] = True
            continue
        dist, j = st.query(c)
        if not np.isfinite(dist) or dist > 100:
            out[k] = True
            continue
        s = np.sign((sp[j] - c) @ u)
        if s == 0:
            out[k] = True
            continue
        out[k] = bool((((ap[idx] - c) @ u) * s < 0).any())
    return out


def read_roads(fips_list: list[str]):
    """(alley lines, other road lines) in EPSG:3071 from TIGER/Line 2024 county roads files."""
    alleys, streets = [], []
    for fips in fips_list:
        path = D / f"tl_2024_{fips}_roads.zip"
        if not path.exists():
            raise FileNotFoundError(f"{path}: run scripts/fetch_parking_lotfit.py")
        L = G.read_shapefile(path, columns=["MTFCC"]).to_crs(CRS_M)
        is_alley = (L.attrs.MTFCC == "S1730").values
        for f, a in zip(L.polys, is_alley):
            (alleys if a else streets).append(f)
    return alleys, streets


# ============================================================================================== lot tables
def load_place_lots(place: str, rules: Rules) -> pd.DataFrame:
    """Residential lots (PROPCLASS exactly '1') of a place with shape, alley and condition flags; Milwaukee and
    Madison also carry zoning (MPROP ZONING; Madison Zoning1) and the conditions those places' rules use."""
    key, fips = PLACES[place]
    L = G.read_geojson(D / f"v12_{key}.geojson", columns=["OBJECTID", "PARCELID", "PROPCLASS"]).to_crs(CRS_M)
    keep = (L.attrs.PROPCLASS.astype(str).str.strip() == "1").values
    L = L.subset(keep)
    sh = lot_shapes(L.polys)
    sh["alley"] = False                     # set per alley bound in run_place (audit option b); TIGER not used
    lots = pd.concat([L.attrs.reset_index(drop=True), sh], axis=1)
    lots["place"] = place
    lots["corner"] = False
    lots["tod_overlay"] = False
    lots["district"] = ""
    if place == "Milwaukee":
        m = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", dtype=str,
                        usecols=["TAXKEY", "ZONING", "CORNER_LOT", "NR_UNITS", "PARKING_SPACES"]).drop_duplicates("TAXKEY")
        lots = lots.merge(m, left_on="PARCELID", right_on="TAXKEY", how="left")
        lots["district"] = lots.ZONING.fillna("").str.strip()
        lots["corner"] = lots.CORNER_LOT.fillna("").str.upper().eq("Y")
    elif place == "Madison":
        mp = G.read_geojson(RAW / "madison_parcels" / "tax_parcels.geojson", columns=["Parcel", "ZoningAll"])
        z = mp.attrs.drop_duplicates("Parcel")
        lots = lots.merge(z, left_on="PARCELID", right_on="Parcel", how="left")
        lots["district"] = lots.ZoningAll.map(lambda v: madison_base_district(v, rules.districts("Madison")))
        tod = G.read_geojson(RAW / "madison_tod" / "tod_boundary.geojson").to_crs(CRS_M)
        px, py = GX.interior_points(L.polys)
        lots["tod_overlay"] = G.points_in_any(px, py, tod.polys)
    return lots


def madison_base_district(zoning_all, coded: set) -> str:
    """Base district from Madison's ZoningAll (e.g. 'WP-27, TR-V1, HIS-UH'; Zoning1 is empty in the file on disk):
    the first coded district listed, else the first entry that is not a wellhead (WP-) or historic (HIS-) overlay."""
    if not isinstance(zoning_all, str):
        return ""
    toks = [t.strip() for t in zoning_all.split(",") if t.strip()]
    for t in toks:
        if t in coded:
            return t
    for t in toks:
        if not t.startswith(("WP-", "HIS-")):
            return t
    return ""


def conds_of(row, place: str) -> frozenset:
    c = set()
    if row.alley:
        c.add("alley")
    if row.corner:
        c.add("corner")
    if row.tod_overlay:
        c.add("tod_overlay")
    if row.area_sqft <= 7500:
        c.add("lot_area_le_7500")
    if row.width_ft < 60 or row.depth_ft < 100:
        c.add("small_lot_w60_d100")
    return frozenset(c)


# ================================================================================================ the run
def lot_keys(lots: pd.DataFrame, place: str) -> tuple[pd.Series, pd.Series]:
    """Valid-geometry mask and the condition set of every lot (computed once per place)."""
    ok = np.isfinite(lots.area_sqft.values) & np.isfinite(lots.width_ft.values) & (lots.width_ft.values > 0)
    conds = pd.Series([conds_of(r, place) for r in lots.itertuples(index=False)], index=lots.index)
    return pd.Series(ok, index=lots.index), conds


def classify(lots: pd.DataFrame, R: Rules, place: str, version: str, n: int, variant: str | None,
             keys: tuple | None = None, central: pd.Series | None = None) -> pd.Series:
    """Class per lot ('' where the lot is out of this version: main needs its district to allow n units). With
    `central` given, groups of lots whose parameters equal the central ones reuse the central class."""
    ok, conds = keys if keys is not None else lot_keys(lots, place)
    coded = R.districts(place)
    if version == "main":
        dist = lots.district.fillna("").astype(str)
    else:
        dist = pd.Series(R.as_if_district(place, n), index=lots.index)
    out = pd.Series("", index=lots.index, dtype=object)
    groups = pd.DataFrame({"d": dist, "c": conds})[ok.values].groupby(["d", "c"], sort=False).groups
    for (d, c), idx in groups.items():
        if version == "main" and (d not in coded or not units_allowed(R, place, d, n, c)):
            continue
        p = resolve(R, place, d, n, c, variant)
        if central is not None and variant is not None and p == resolve(R, place, d, n, c, None):
            out.loc[idx] = central.loc[idx]
            continue
        sub = lots.loc[idx]
        out.loc[idx] = [fit_lot(Lot(a, w, dp, bool(al), bool(co)), p)[0]
                        for a, w, dp, al, co in zip(sub.area_sqft, sub.width_ft, sub.depth_ft, sub.alley, sub.corner)]
    return out


def summarise(lots: pd.DataFrame, cls: pd.Series, keys: dict, fill_min: float) -> list[dict]:
    """Counts and shares for all lots and the splits: regular / irregular, width < 40 / >= 40 ft (the alley split
    is replaced by the two alley bounds)."""
    rows = []
    df = pd.DataFrame({"cls": cls, "w40": lots.width_ft.values >= 40, "regular": lots.fill.values >= fill_min})
    df = df[df.cls != ""]
    splits = {"regular lots": df.regular, "irregular lots (fill < 80%)": ~df.regular,
              "regular, width < 40 ft": df.regular & ~df.w40, "regular, width >= 40 ft": df.regular & df.w40}
    for name, m in splits.items():
        s = df[m]
        n_all = len(s)
        n_other = int((s.cls == OTHER).sum())
        n_fit0 = int((s.cls != OTHER).sum())
        n_park = int((s.cls == PARKING).sum())
        rows.append({**keys, "split": name, "lots": n_all, "other_rules_block": n_other,
                     "fit_without_parking": n_fit0, "parking_blocks": n_park,
                     "share_parking_blocks": (n_park / n_fit0) if n_fit0 else np.nan,
                     "share_other_rules_block": (n_other / n_all) if n_all else np.nan})
    return rows


def run_place(place: str, lots: pd.DataFrame, R: Rules) -> list[dict]:
    fill_min = float(R.get("*", "*", "rect_fill_min", 2) or 0.8)
    out = []
    versions = ["main", "as_if"] if place in ZONED else ["as_if"]
    for bound, has_alley in ALLEY_BOUNDS.items():
        lots = lots.assign(alley=has_alley)
        lk = lot_keys(lots, place)
        for version in versions:
            for n in UNITS:
                central = None
                for rid in [None] + R.variants(place):
                    cls = classify(lots, R, place, version, n, rid, lk, central)
                    if rid is None:
                        central = cls
                    keys = {"place": place, "alley_bound": bound, "version": version, "units": n,
                            "variant": rid or "central"}
                    out += summarise(lots, cls, keys, fill_min)
    return out


def pooled(rows: pd.DataFrame) -> pd.DataFrame:
    """Lot-weighted 'tested places' rows: sums of numerators over sums of denominators, per version / units /
    split, central and each variant (a variant that cannot apply in a place leaves that place at its central)."""
    out = []
    for (bound, version, n, split), g in rows.groupby(["alley_bound", "version", "units", "split"]):
        central = g[g.variant == "central"].set_index("place")
        for rid in sorted(g.variant.unique()):
            v = g[g.variant == rid].set_index("place")
            use = central.copy()
            use.loc[v.index] = v
            s = use[["lots", "other_rules_block", "fit_without_parking", "parking_blocks"]].sum()
            out.append({"place": "tested places (lot-weighted)", "alley_bound": bound, "version": version, "units": n, "split": split,
                        "variant": rid,
                        **s.to_dict(),
                        "share_parking_blocks": s.parking_blocks / s.fit_without_parking if s.fit_without_parking else np.nan,
                        "share_other_rules_block": s.other_rules_block / s.lots if s.lots else np.nan})
    return pd.DataFrame(out)


def spans(shares: pd.DataFrame) -> pd.DataFrame:
    """Central share with the low / high across variants (each variant alone), labelled as a span of assumptions."""
    out = []
    for (place, bound, version, n, split), g in shares.groupby(["place", "alley_bound", "version", "units", "split"]):
        c = g[g.variant == "central"].share_parking_blocks
        allv = g.share_parking_blocks.dropna()
        lo = g.loc[allv.idxmin()] if len(allv) else None
        hi = g.loc[allv.idxmax()] if len(allv) else None
        out.append({"place": place, "alley_bound": bound, "version": version, "units": n, "split": split,
                    "central_share": float(c.iloc[0]) if len(c) else np.nan,
                    "span_low": float(lo.share_parking_blocks) if lo is not None else np.nan,
                    "span_low_variant": lo.variant if lo is not None else "",
                    "span_high": float(hi.share_parking_blocks) if hi is not None else np.nan,
                    "span_high_variant": hi.variant if hi is not None else "",
                    "span_label": SPAN_LABEL, "bound_label": BOUND_LABEL, "waiver_note": WAIVER_LABEL})
    return pd.DataFrame(out)


def sanity_milwaukee(lots: pd.DataFrame, R: Rules) -> pd.DataFrame:
    """Audit fix 5: apply the model to Milwaukee's existing 2-4 unit buildings (MPROP NR_UNITS); label 'rule model
    may be too strict' when over 50% could not fit. Two stall counts, each its own rows:
    - 'modelled rules' (the label rule): the stalls the modelled rules require on the lot's district (RT4 where the
      district is not coded);
    - 'recorded spaces': MPROP PARKING_SPACES. Buildings with no recorded value are left out; when none has one
      (the MPROP file on disk leaves the field empty) the rows say 'not computable'."""
    cut = float(R.get("*", "*", "sanity_too_strict_share", 2) or 0.5)
    rule_txt = f"label when share_could_not_fit > {cut:.0%} (convention, audit fix 5); no retuning"
    m = lots.copy()
    m["nu"] = pd.to_numeric(m.NR_UNITS, errors="coerce")
    m["ps"] = pd.to_numeric(m.PARKING_SPACES, errors="coerce")
    m = m[m.nu.isin([2, 3, 4]) & np.isfinite(m.width_ft) & (m.width_ft > 0)]
    coded = R.districts("Milwaukee")
    out = []
    for basis in ("modelled rules", "recorded spaces"):
        rows = []
        for n in UNITS:
            s = m[m.nu == n]
            if basis == "recorded spaces":
                s = s[s.ps.notna()]
            res = []
            for row in s.itertuples(index=False):
                d = row.district if row.district in coded else R.as_if_district("Milwaukee", n)
                p = resolve(R, "Milwaukee", d, n, conds_of(row, "Milwaukee"))
                if basis == "recorded spaces":
                    p = replace(p, stalls=int(row.ps), enclosed=0)
                res.append(fit_lot(Lot(row.area_sqft, row.width_ft, row.depth_ft, bool(row.alley), bool(row.corner)), p)[0])
            res = pd.Series(res, dtype=str)
            rows.append({"basis": basis, "units": str(n), "existing_buildings": len(res),
                         "could_not_fit": int((res != FITS).sum()), "of_which_other_rules": int((res == OTHER).sum()),
                         "of_which_parking": int((res == PARKING).sum())})
        a = pd.DataFrame(rows)
        tot = a[["existing_buildings", "could_not_fit", "of_which_other_rules", "of_which_parking"]].sum()
        a = pd.concat([a, pd.DataFrame([{"basis": basis, "units": "2-4", **{k: int(v) for k, v in tot.items()}}])],
                      ignore_index=True)
        a["share_could_not_fit"] = np.where(a.existing_buildings > 0,
                                            a.could_not_fit / a.existing_buildings.where(a.existing_buildings > 0), np.nan)
        a["label"] = np.where(a.share_could_not_fit > cut, SANITY_LABEL, "")
        if basis == "recorded spaces" and tot.existing_buildings == 0:
            a["label"] = "not computable: PARKING_SPACES empty in the MPROP file"
        a["rule"] = rule_txt
        out.append(a)
    return pd.concat(out, ignore_index=True)


# ============================================================================================== synthetic
def synthetic_lots(place: str, n: int = 300, seed: int = 7) -> pd.DataFrame:
    """Made-up rectangular lots for a smoke run (no real data): widths 25-120 ft, depths 90-200 ft."""
    rng = np.random.default_rng(seed)
    w = rng.uniform(25, 120, n)
    d = rng.uniform(90, 200, n)
    df = pd.DataFrame({"area_sqft": w * d, "width_ft": w, "depth_ft": d, "fill": rng.uniform(0.7, 1.0, n),
                       "alley": rng.random(n) < 0.3, "corner": rng.random(n) < 0.1, "tod_overlay": rng.random(n) < 0.1,
                       "place": place})
    R = Rules(load_rules())
    ds = sorted(d for d in R.districts(place) if units_allowed(R, place, d, 2) or units_allowed(R, place, d, 4))
    df["district"] = [ds[i % len(ds)] for i in range(n)] if ds else ""
    df["NR_UNITS"] = rng.choice(["1", "2", "3", "4"], n)
    df["PARKING_SPACES"] = rng.choice(["0", "1", "2", "3", "4"], n)
    return df


# ==================================================================================================== main
def _place_job(place: str, synthetic: bool):
    R = Rules(load_rules())
    lots = synthetic_lots(place) if synthetic else load_place_lots(place, R)
    rows = run_place(place, lots, R)
    san = None
    if place == "Milwaukee":
        san = pd.concat([sanity_milwaukee(lots.assign(alley=a), R).assign(alley_bound=b)
                         for b, a in ALLEY_BOUNDS.items()], ignore_index=True)
        san["bound_label"] = BOUND_LABEL
    return place, rows, san


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--go", action="store_true", help="real run (only after the audit clears)")
    g.add_argument("--synthetic", action="store_true", help="smoke run on made-up lots; writes to --out only")
    ap.add_argument("--places", nargs="*", default=list(PLACES), choices=list(PLACES))
    ap.add_argument("--out", type=Path, default=None, help="output folder (default: reference/ for --go)")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    out = a.out or (REFERENCE if a.go else None)
    if out is None:
        ap.error("--synthetic needs --out (it never writes to reference/)")
    if a.synthetic and out.resolve() == REFERENCE.resolve():
        ap.error("--synthetic never writes to reference/")
    out.mkdir(parents=True, exist_ok=True)
    rows, sanity = [], None
    jobs = (a.places, [a.synthetic] * len(a.places))
    ex = cf.ProcessPoolExecutor(a.workers) if a.workers > 1 else None
    try:
        for place, r, san in (ex.map(_place_job, *jobs) if ex else map(_place_job, *jobs)):
            rows += r
            if san is not None:
                sanity = san
            print(f"{place}: done", flush=True)
    finally:
        if ex:
            ex.shutdown()
    shares = pd.DataFrame(rows)
    shares = pd.concat([shares, pooled(shares)], ignore_index=True)
    shares["note"] = WAIVER_LABEL
    shares["bound_label"] = BOUND_LABEL
    shares.to_csv(out / "parking_lotfit_shares.csv", index=False)
    spans(shares).to_csv(out / "parking_lotfit_spans.csv", index=False)
    if sanity is not None:
        sanity.to_csv(out / "parking_lotfit_sanity_milwaukee.csv", index=False)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
