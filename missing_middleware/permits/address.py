"""Address normalization for permit-to-parcel matching (city-agnostic).

Rules (fixed before match rates were evaluated; see docs/gate2/MADISON_PERMITS.md):

1. Upper-case; replace `.,#;` with spaces; collapse whitespace.
2. House number = leading token of digits, optionally followed by a letter
   (`123A`), a fraction (`123 1/2` -> `123`, flag `fraction`), or a range
   (`101-103` -> primary 101, alternates 101 and 103, flag `range`).
3. Pre-direction = next token if it is N/S/E/W (or NORTH etc.) and more tokens follow.
4. Street = the longest run of following tokens that forms a street known to
   the reference address table (`street_keys`); if none is known, the street
   runs to the last street-type token, else to the end.
5. Whatever follows the street is the unit/suffix (e.g. `2`, `UNIT 2`, `REAR`,
   `APT B`). It never blocks a match; it is kept for audit.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

DIRS = {"N": "N", "S": "S", "E": "E", "W": "W", "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
STREET_TYPES = {
    "ALY", "AVE", "BLVD", "BND", "CIR", "CRES", "CT", "CV", "CRST", "DR", "GLN", "GRN", "HTS", "HWY",
    "LN", "LOOP", "MALL", "PASS", "PATH", "PKWY", "PL", "PLZ", "PT", "RD", "RDG", "ROW", "RUN", "SQ",
    "ST", "TER", "TRL", "VW", "WALK", "WAY", "XING", "TRCE", "HL", "HOLW", "CMN", "ESTS", "FRD", "LNDG",
    "MDW", "MDWS", "PARK", "PNE", "PNES", "SPUR", "VLY", "VIS", "BRG", "CRK", "CTR", "GTWY", "HBR",
}
TYPE_ALIASES = {"AVENUE": "AVE", "STREET": "ST", "DRIVE": "DR", "ROAD": "RD", "LANE": "LN", "COURT": "CT",
                "PLACE": "PL", "BOULEVARD": "BLVD", "TRAIL": "TRL", "CIRCLE": "CIR", "PARKWAY": "PKWY",
                "TERRACE": "TER", "HIGHWAY": "HWY"}
UNIT_WORDS = {"UNIT", "APT", "STE", "SUITE", "REAR", "FRONT", "UPPER", "LOWER", "BLDG", "FL", "LOT", "ADU"}

_NUM_RE = re.compile(r"^(\d+)([A-Z])?$")
_RANGE_RE = re.compile(r"^(\d+)-(\d+)$")
_FRACTION_RE = re.compile(r"^\d/\d$")


def clean(text: str) -> str:
    text = (text or "").upper()
    text = re.sub(r"[.,#;]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class ParsedAddress:
    raw: str
    house_nbr: int | None = None
    house_alt: tuple[int, ...] = ()
    pre_dir: str = ""
    street: str = ""       # street name tokens without direction and type
    street_type: str = ""
    unit: str = ""
    flags: list[str] = field(default_factory=list)

    @property
    def street_key(self) -> str:
        """`DIR NAME TYPE`, the full street identity used for matching."""
        return " ".join(t for t in (self.pre_dir, self.street, self.street_type) if t)

    @property
    def key(self) -> str:
        return f"{self.house_nbr}|{self.street_key}" if self.house_nbr is not None else ""


def street_key_from_parts(pre_dir: str | None, name: str | None, stype: str | None) -> str:
    d = DIRS.get(clean(pre_dir or ""), clean(pre_dir or ""))
    t = clean(stype or "")
    t = TYPE_ALIASES.get(t, t)
    return " ".join(x for x in (d, clean(name or ""), t) if x)


def parse(raw: str, street_keys: set[str] | None = None) -> ParsedAddress:
    text = clean(raw)
    out = ParsedAddress(raw=raw)
    toks = text.split()
    if not toks:
        out.flags.append("empty")
        return out
    first = toks[0]
    m, r = _NUM_RE.match(first), _RANGE_RE.match(first)
    if m:
        out.house_nbr = int(m.group(1))
        if m.group(2):
            out.flags.append("number_suffix")
            out.unit = m.group(2)
    elif r:
        a, b = int(r.group(1)), int(r.group(2))
        out.house_nbr, out.house_alt = a, (a, b)
        out.flags.append("range")
    else:
        out.flags.append("no_house_number")
        return out
    rest = toks[1:]
    if rest and _FRACTION_RE.match(rest[0]):
        out.flags.append("fraction")
        rest = rest[1:]
    dir_word = ""
    if len(rest) > 1 and rest[0] in DIRS:
        dir_word = rest[0]
        out.pre_dir, rest = DIRS[rest[0]], rest[1:]
    rest = [TYPE_ALIASES.get(t, t) for t in rest]
    cut = None
    if street_keys:
        for n in range(len(rest), 0, -1):  # longest known street wins
            cand = " ".join(([out.pre_dir] if out.pre_dir else []) + rest[:n])
            if cand in street_keys:
                cut = n
                break
        if cut is None and dir_word:  # "WEST SHORE DR": the direction word is part of the name
            full = [TYPE_ALIASES.get(dir_word, dir_word)] + rest
            for n in range(len(full), 1, -1):
                if " ".join(full[:n]) in street_keys:
                    out.pre_dir, rest, cut = "", full, n
                    out.flags.append("dir_word_in_name")
                    break
        if cut is None and out.pre_dir:  # direction may be part of name only in reference
            for n in range(len(rest), 0, -1):
                if " ".join(rest[:n]) in street_keys:
                    cut = n
                    out.flags.append("dir_dropped")
                    out.pre_dir = ""
                    break
    if cut is None:
        type_idx = [i for i, t in enumerate(rest) if t in STREET_TYPES and i > 0]
        cut = (type_idx[-1] + 1) if type_idx else len(rest)
        if street_keys:
            out.flags.append("street_unknown")
    street, unit = rest[:cut], rest[cut:]
    if street and street[-1] in STREET_TYPES and len(street) > 1:
        out.street_type = street[-1]
        street = street[:-1]
    out.street = " ".join(street)
    if unit:
        out.unit = " ".join(t for t in unit if t not in {"UNIT", "APT", "STE", "SUITE"}) or " ".join(unit)
        out.flags.append("unit_suffix")
    return out
